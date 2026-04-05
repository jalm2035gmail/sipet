"""
Rutas de medios de pago para MultiTiendApp.

Medios soportados:
  - efectivo     → Pago contra entrega / en tienda.
  - paypal       → PayPal REST API v2 (sandbox o producción según PAYPAL_SANDBOX env var).
  - billetera_if → Billetera electrónica emitida por la institución financiera.
  - prestamo_if  → Solicitud de crédito/préstamo a la institución financiera.

Variables de entorno necesarias:
  PayPal:
    PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET, PAYPAL_SANDBOX (true|false)
  Institución financiera:
    IF_API_BASE_URL  → URL base de la API de la IF (ej. https://api.miif.com)
    IF_API_KEY       → Clave de API para autenticar contra la IF
    IF_API_TIMEOUT   → Timeout en segundos (default: 15)
"""

from __future__ import annotations

import os
import secrets
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import get_db
from .models import (
    CheckoutPayment,
    IFWalletAccount,
    IFWalletTransaction,
    LoanRequest,
)
from .schemas import (
    CashCheckoutIn,
    CheckoutPaymentOut,
    IFWalletCheckoutIn,
    IFWalletLinkIn,
    IFWalletOut,
    IFWalletTransactionOut,
    LoanRequestIn,
    LoanRequestOut,
    LoanStatusUpdateIn,
    PayPalCaptureIn,
    PayPalCheckoutIn,
)

router = APIRouter(prefix="/api/payments", tags=["payments"])

_SESSION_COOKIE = "mt_session"

# ── PayPal config ──────────────────────────────────────────────────────────────

_PAYPAL_SANDBOX = os.getenv("PAYPAL_SANDBOX", "true").lower() != "false"
_PAYPAL_BASE = (
    "https://api-m.sandbox.paypal.com" if _PAYPAL_SANDBOX
    else "https://api-m.paypal.com"
)
_PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "")
_PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "")

# ── Institución financiera config ──────────────────────────────────────────────

_IF_API_BASE = os.getenv("IF_API_BASE_URL", "").rstrip("/")
_IF_API_KEY = os.getenv("IF_API_KEY", "")
_IF_TIMEOUT = int(os.getenv("IF_API_TIMEOUT", "15"))


def _if_headers() -> dict:
    return {"Authorization": f"Bearer {_IF_API_KEY}", "Accept": "application/json"}


def _if_available() -> bool:
    return bool(_IF_API_BASE and _IF_API_KEY)



_PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_session_key(request: Request, response: Response) -> str:
    key = request.headers.get("X-Session-Key") or request.cookies.get(_SESSION_COOKIE)
    if not key:
        key = secrets.token_urlsafe(32)
        response.set_cookie(
            _SESSION_COOKIE, key,
            max_age=60 * 60 * 24 * 365,
            httponly=True,
            samesite="lax",
        )
    return key


def _serialize_payment(p: CheckoutPayment) -> dict:
    return {
        "id": p.id,
        "order_reference": p.order_reference,
        "payment_method": p.payment_method,
        "amount": float(p.amount),
        "status": p.status,
        "paypal_order_id": p.paypal_order_id,
        "paypal_capture_id": p.paypal_capture_id,
        "if_wallet_transaction_id": p.if_wallet_transaction_id,
        "loan_request_id": p.loan_request_id,
        "notes": p.notes,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


def _serialize_loan(lr: LoanRequest) -> dict:
    return {
        "id": lr.id,
        "order_reference": lr.order_reference,
        "member_number": lr.member_number,
        "customer_name": lr.customer_name,
        "amount_requested": float(lr.amount_requested),
        "loan_product": lr.loan_product,
        "term_months": lr.term_months,
        "purpose": lr.purpose,
        "status": lr.status,
        "if_folio": lr.if_folio,
        "if_approved_amount": float(lr.if_approved_amount) if lr.if_approved_amount else None,
        "if_interest_rate": float(lr.if_interest_rate) if lr.if_interest_rate else None,
        "if_response_notes": lr.if_response_notes,
        "created_at": lr.created_at.isoformat() if lr.created_at else None,
        "reviewed_at": lr.reviewed_at.isoformat() if lr.reviewed_at else None,
    }


async def _paypal_access_token() -> str:
    if not _PAYPAL_CLIENT_ID or not _PAYPAL_CLIENT_SECRET:
        raise HTTPException(
            status_code=503,
            detail="PayPal no está configurado. Define PAYPAL_CLIENT_ID y PAYPAL_CLIENT_SECRET.",
        )
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{_PAYPAL_BASE}/v1/oauth2/token",
            data={"grant_type": "client_credentials"},
            auth=(_PAYPAL_CLIENT_ID, _PAYPAL_CLIENT_SECRET),
            headers={"Accept": "application/json"},
            timeout=15,
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Error al autenticar con PayPal.")
    return resp.json()["access_token"]


# ── Billetera IF: vinculación y consulta ───────────────────────────────────────

@router.post("/billetera-if/vincular", response_model=IFWalletOut, status_code=201)
def if_wallet_link(
    payload: IFWalletLinkIn,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Vincula la sesión actual con la cuenta de billetera IF del socio."""
    session_key = _get_session_key(request, response)
    wallet = db.query(IFWalletAccount).filter(IFWalletAccount.session_key == session_key).first()
    if wallet:
        wallet.member_number = payload.member_number
        wallet.account_number = payload.account_number
    else:
        wallet = IFWalletAccount(
            session_key=session_key,
            member_number=payload.member_number,
            account_number=payload.account_number,
            currency="MXN",
            status="active",
        )
        db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return {
        "session_key": session_key,
        "member_number": wallet.member_number,
        "account_number": wallet.account_number,
        "cached_balance": float(wallet.cached_balance) if wallet.cached_balance is not None else None,
        "currency": wallet.currency,
        "status": wallet.status,
        "last_synced_at": wallet.last_synced_at.isoformat() if wallet.last_synced_at else None,
    }


@router.get("/billetera-if/saldo", response_model=IFWalletOut)
async def if_wallet_balance(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Consulta el saldo de la billetera IF del socio.
    Si IF_API_BASE_URL está configurado, consulta el saldo en tiempo real a la IF.
    De lo contrario devuelve el último saldo cacheado.
    """
    session_key = _get_session_key(request, response)
    wallet = db.query(IFWalletAccount).filter(IFWalletAccount.session_key == session_key).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="No hay billetera IF vinculada. Usa /billetera-if/vincular primero.")

    # Consultar saldo en la IF si está configurada
    if _if_available():
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{_IF_API_BASE}/api/billetera/saldo",
                    params={"numero_socio": wallet.member_number, "numero_cuenta": wallet.account_number},
                    headers=_if_headers(),
                    timeout=_IF_TIMEOUT,
                )
            if resp.status_code == 200:
                data = resp.json()
                wallet.cached_balance = Decimal(str(data.get("saldo", wallet.cached_balance or 0)))
                wallet.last_synced_at = datetime.now(timezone.utc)
                db.commit()
                db.refresh(wallet)
        except Exception:
            pass  # usar cache si la IF no responde

    return {
        "session_key": session_key,
        "member_number": wallet.member_number,
        "account_number": wallet.account_number,
        "cached_balance": float(wallet.cached_balance) if wallet.cached_balance is not None else None,
        "currency": wallet.currency,
        "status": wallet.status,
        "last_synced_at": wallet.last_synced_at.isoformat() if wallet.last_synced_at else None,
    }


@router.get("/billetera-if/movimientos", response_model=List[IFWalletTransactionOut])
def if_wallet_transactions(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Historial local de débitos realizados con la billetera IF."""
    session_key = _get_session_key(request, response)
    wallet = db.query(IFWalletAccount).filter(IFWalletAccount.session_key == session_key).first()
    if not wallet:
        return []
    txs = (
        db.query(IFWalletTransaction)
        .filter(IFWalletTransaction.wallet_id == wallet.id)
        .order_by(IFWalletTransaction.created_at.desc())
        .all()
    )
    return [
        {
            "id": t.id,
            "type": t.type,
            "amount": float(t.amount),
            "reference_id": t.reference_id,
            "if_transaction_ref": t.if_transaction_ref,
            "description": t.description,
            "status": t.status,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in txs
    ]


# ── Checkout: Efectivo ─────────────────────────────────────────────────────────

@router.post("/checkout/efectivo", response_model=dict, status_code=201)
def checkout_cash(
    payload: CashCheckoutIn,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Registra un pedido para pago en efectivo (contra entrega o en tienda)."""
    session_key = _get_session_key(request, response)
    payment = CheckoutPayment(
        session_key=session_key,
        order_reference=payload.order_reference,
        payment_method="efectivo",
        amount=payload.amount,
        status="pending",
        notes="; ".join(filter(None, [
            payload.notes,
            f"Entrega: {payload.delivery_address}" if payload.delivery_address else "",
            f"Cliente: {payload.customer_name}" if payload.customer_name else "",
        ])),
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return _serialize_payment(payment)


# ── Checkout: PayPal ──────────────────────────────────────────────────────────

@router.post("/checkout/paypal", response_model=dict, status_code=201)
async def checkout_paypal_create(
    payload: PayPalCheckoutIn,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Crea una orden en PayPal. Redirigir al cliente a `approve_url`.
    Luego capturar con POST /checkout/paypal/capture."""
    session_key = _get_session_key(request, response)
    token = await _paypal_access_token()

    order_payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "reference_id": payload.order_reference,
                "amount": {
                    "currency_code": payload.currency,
                    "value": str(payload.amount.quantize(Decimal("0.01"))),
                },
            }
        ],
        "application_context": {
            "return_url": payload.return_url,
            "cancel_url": payload.cancel_url,
            "user_action": "PAY_NOW",
        },
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{_PAYPAL_BASE}/v2/checkout/orders",
            json=order_payload,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=20,
        )

    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=502, detail=f"PayPal error: {resp.text[:300]}")

    pp_data = resp.json()
    pp_order_id = pp_data["id"]
    approve_url = next(
        (lnk["href"] for lnk in pp_data.get("links", []) if lnk["rel"] == "approve"), None
    )

    payment = CheckoutPayment(
        session_key=session_key,
        order_reference=payload.order_reference,
        payment_method="paypal",
        amount=payload.amount,
        status="created",
        paypal_order_id=pp_order_id,
        notes=f"approve_url={approve_url}",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    result = _serialize_payment(payment)
    result["approve_url"] = approve_url
    return result


@router.post("/checkout/paypal/capture", response_model=dict)
async def checkout_paypal_capture(
    payload: PayPalCaptureIn,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Captura el pago de una orden PayPal ya aprobada por el cliente."""
    session_key = _get_session_key(request, response)
    payment = db.query(CheckoutPayment).filter(
        CheckoutPayment.id == payload.payment_id,
        CheckoutPayment.session_key == session_key,
        CheckoutPayment.payment_method == "paypal",
    ).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Pago no encontrado.")
    if payment.status == "completed":
        return _serialize_payment(payment)

    token = await _paypal_access_token()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{_PAYPAL_BASE}/v2/checkout/orders/{payload.paypal_order_id}/capture",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=20,
        )

    if resp.status_code not in (200, 201):
        payment.status = "failed"
        db.commit()
        raise HTTPException(status_code=502, detail=f"PayPal capture error: {resp.text[:300]}")

    cap_data = resp.json()
    capture_id = (
        cap_data.get("purchase_units", [{}])[0]
        .get("payments", {})
        .get("captures", [{}])[0]
        .get("id", "")
    )
    payment.paypal_capture_id = capture_id
    payment.status = "completed"
    db.commit()
    db.refresh(payment)
    return _serialize_payment(payment)


# ── Checkout: Billetera IF ────────────────────────────────────────────────────

@router.post("/checkout/billetera-if", response_model=dict, status_code=201)
async def checkout_if_wallet(
    payload: IFWalletCheckoutIn,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Debita el monto de la billetera electrónica de la institución financiera.
    Llama al endpoint de débito de la IF si está configurado, o registra
    el intento para conciliación manual si no hay integración activa.
    """
    session_key = _get_session_key(request, response)

    # Obtener o crear vínculo de billetera IF
    wallet = db.query(IFWalletAccount).filter(IFWalletAccount.session_key == session_key).first()
    if not wallet:
        wallet = IFWalletAccount(
            session_key=session_key,
            member_number=payload.member_number,
            account_number=payload.account_number,
            currency="MXN",
            status="active",
        )
        db.add(wallet)
        db.flush()
    else:
        # Actualizar datos del socio si cambiaron
        wallet.member_number = payload.member_number
        wallet.account_number = payload.account_number

    if_ref = None
    tx_status = "pending"

    # Intentar débito en la IF si está configurada
    if _if_available():
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{_IF_API_BASE}/api/billetera/debito",
                    json={
                        "numero_socio": payload.member_number,
                        "numero_cuenta": payload.account_number,
                        "monto": str(payload.amount.quantize(Decimal("0.01"))),
                        "referencia": payload.order_reference,
                        "concepto": f"Compra en tienda - Orden {payload.order_reference}",
                    },
                    headers={**_if_headers(), "Content-Type": "application/json"},
                    timeout=_IF_TIMEOUT,
                )
            if resp.status_code == 200:
                data = resp.json()
                if_ref = data.get("referencia_if") or data.get("folio")
                tx_status = "completed"
            else:
                raise HTTPException(
                    status_code=402,
                    detail=f"La institución financiera rechazó el débito: {resp.text[:200]}",
                )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"No se pudo conectar con la institución financiera: {exc}") from exc

    # Registrar la transacción localmente
    tx = IFWalletTransaction(
        wallet_id=wallet.id,
        type="debit",
        amount=payload.amount,
        reference_id=payload.order_reference,
        if_transaction_ref=if_ref,
        description=f"Pago pedido {payload.order_reference}",
        status=tx_status,
    )
    db.add(tx)
    db.flush()

    payment = CheckoutPayment(
        session_key=session_key,
        order_reference=payload.order_reference,
        payment_method="billetera_if",
        amount=payload.amount,
        status=tx_status,
        if_wallet_transaction_id=tx.id,
        notes=f"Socio: {payload.member_number} | IF ref: {if_ref}" if if_ref else f"Socio: {payload.member_number}",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return _serialize_payment(payment)


# ── Solicitud de préstamo IF ──────────────────────────────────────────────────

@router.post("/prestamo-if", response_model=dict, status_code=201)
async def solicitar_prestamo(
    payload: LoanRequestIn,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Envía una solicitud de crédito a la institución financiera para financiar
    la compra. El estado inicial es 'pending'; la IF notificará el resultado
    vía webhook o puede ser consultado con GET /prestamo-if/{id}.
    """
    session_key = _get_session_key(request, response)

    lr = LoanRequest(
        session_key=session_key,
        order_reference=payload.order_reference,
        member_number=payload.member_number,
        customer_name=payload.customer_name,
        customer_email=payload.customer_email,
        customer_phone=payload.customer_phone,
        amount_requested=payload.amount_requested,
        loan_product=payload.loan_product,
        term_months=payload.term_months,
        purpose=payload.purpose,
        status="pending",
    )
    db.add(lr)
    db.flush()

    if_folio = None

    # Enviar solicitud a la IF si está configurada
    if _if_available():
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{_IF_API_BASE}/api/creditos/solicitud",
                    json={
                        "numero_socio": payload.member_number,
                        "nombre": payload.customer_name,
                        "email": payload.customer_email,
                        "telefono": payload.customer_phone,
                        "monto_solicitado": str(payload.amount_requested.quantize(Decimal("0.01"))),
                        "producto": payload.loan_product,
                        "plazo_meses": payload.term_months,
                        "destino": payload.purpose,
                        "referencia_externa": payload.order_reference,
                        "solicitud_id": lr.id,
                    },
                    headers={**_if_headers(), "Content-Type": "application/json"},
                    timeout=_IF_TIMEOUT,
                )
            if resp.status_code in (200, 201):
                data = resp.json()
                if_folio = data.get("folio") or data.get("id_solicitud")
                lr.if_folio = if_folio
                lr.status = data.get("status", "reviewing")
            else:
                # No falla el request: la solicitud queda en pending para revisión manual
                lr.if_response_notes = f"IF HTTP {resp.status_code}: {resp.text[:200]}"
        except Exception as exc:
            lr.if_response_notes = f"Error de conexión con IF: {exc}"

    # Registrar CheckoutPayment vinculado al préstamo
    payment = CheckoutPayment(
        session_key=session_key,
        order_reference=payload.order_reference,
        payment_method="prestamo_if",
        amount=payload.amount_requested,
        status="pending",
        loan_request_id=lr.id,
        notes=f"Solicitud de crédito | Socio: {payload.member_number} | Folio IF: {if_folio or 'pendiente'}",
    )
    db.add(payment)
    db.commit()
    db.refresh(lr)
    result = _serialize_loan(lr)
    result["checkout_payment_id"] = payment.id
    return result


@router.get("/prestamo-if/{loan_id}", response_model=dict)
def get_loan(
    loan_id: int,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Consulta el estado de una solicitud de préstamo."""
    session_key = _get_session_key(request, response)
    lr = db.query(LoanRequest).filter(
        LoanRequest.id == loan_id,
        LoanRequest.session_key == session_key,
    ).first()
    if not lr:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada.")
    return _serialize_loan(lr)


@router.get("/prestamos-if", response_model=List[dict])
def list_loans(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Lista todas las solicitudes de préstamo de la sesión actual."""
    session_key = _get_session_key(request, response)
    loans = (
        db.query(LoanRequest)
        .filter(LoanRequest.session_key == session_key)
        .order_by(LoanRequest.created_at.desc())
        .all()
    )
    return [_serialize_loan(lr) for lr in loans]


@router.patch("/prestamo-if/{loan_id}/estado", response_model=dict)
def update_loan_status(
    loan_id: int,
    payload: LoanStatusUpdateIn,
    db: Session = Depends(get_db),
):
    """
    Webhook interno: actualiza el resultado de una solicitud de préstamo
    (llamado por la IF o por un proceso administrativo).
    No requiere session_key (uso interno/backend).
    """
    lr = db.query(LoanRequest).filter(LoanRequest.id == loan_id).first()
    if not lr:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada.")

    lr.status = payload.status
    if payload.if_folio is not None:
        lr.if_folio = payload.if_folio
    if payload.if_approved_amount is not None:
        lr.if_approved_amount = payload.if_approved_amount
    if payload.if_interest_rate is not None:
        lr.if_interest_rate = payload.if_interest_rate
    if payload.if_response_notes is not None:
        lr.if_response_notes = payload.if_response_notes
    if payload.status in ("approved", "rejected", "disbursed"):
        lr.reviewed_at = datetime.now(timezone.utc)

    # Sincronizar estado del CheckoutPayment vinculado
    payment = db.query(CheckoutPayment).filter(
        CheckoutPayment.loan_request_id == loan_id,
        CheckoutPayment.payment_method == "prestamo_if",
    ).first()
    if payment:
        if payload.status == "disbursed":
            payment.status = "completed"
        elif payload.status == "rejected":
            payment.status = "failed"
        elif payload.status == "approved":
            payment.status = "approved"

    db.commit()
    db.refresh(lr)
    return _serialize_loan(lr)


# ── Consulta de pagos por pedido ──────────────────────────────────────────────

@router.get("/checkout/{order_reference}", response_model=List[dict])
def get_payments_for_order(
    order_reference: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Devuelve todos los registros de pago para una referencia de orden."""
    session_key = _get_session_key(request, response)
    payments = (
        db.query(CheckoutPayment)
        .filter(
            CheckoutPayment.order_reference == order_reference,
            CheckoutPayment.session_key == session_key,
        )
        .order_by(CheckoutPayment.created_at.desc())
        .all()
    )
    return [_serialize_payment(p) for p in payments]

