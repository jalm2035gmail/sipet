from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Numeric, Text
from sqlalchemy.sql import func

from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import Base


# ── Medios de pago disponibles ────────────────────────────────────────────────
# efectivo     → Pago contra entrega / en tienda.
# paypal       → PayPal REST API v2.
# billetera_if → Billetera electrónica emitida por la institución financiera.
# prestamo_if  → Solicitud de crédito a la institución financiera.


class IFWalletAccount(Base):
    """Cuenta de billetera electrónica de la institución financiera.
    El saldo real vive en la IF; aquí guardamos la vinculación y un
    cache del último saldo consultado."""
    __tablename__ = "mt_if_wallet_accounts"

    id = Column(Integer, primary_key=True)
    session_key = Column(String(120), nullable=False, unique=True, index=True)
    # Datos del socio/cliente en la IF
    member_number = Column(String(60), nullable=False, default="")   # nº de socio / afiliado
    account_number = Column(String(60), nullable=False, default="")  # nº de cuenta IF
    # Balance cacheado (actualizado en cada consulta a la IF)
    cached_balance = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(10), nullable=False, default="MXN")
    # Estado de la vinculación
    status = Column(String(20), nullable=False, default="active")    # active | suspended
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class IFWalletTransaction(Base):
    """Registro local de movimientos realizados con la billetera IF
    (para auditoría y conciliación). La fuente de verdad es la IF."""
    __tablename__ = "mt_if_wallet_transactions"

    id = Column(Integer, primary_key=True)
    wallet_id = Column(Integer, nullable=False, index=True)          # → mt_if_wallet_accounts.id
    type = Column(String(10), nullable=False)                        # "debit"
    amount = Column(Numeric(12, 2), nullable=False)
    reference_id = Column(String(100), nullable=True)               # order_reference
    if_transaction_ref = Column(String(100), nullable=True)         # referencia devuelta por la IF
    description = Column(String(300), nullable=False, default="")
    status = Column(String(20), nullable=False, default="pending")  # pending | completed | failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LoanRequest(Base):
    """Solicitud de préstamo/crédito a la institución financiera para
    financiar una compra en la tienda."""
    __tablename__ = "mt_loan_requests"

    id = Column(Integer, primary_key=True)
    session_key = Column(String(120), nullable=False, index=True)
    order_reference = Column(String(100), nullable=False, index=True)
    # Datos del solicitante
    member_number = Column(String(60), nullable=False, default="")
    customer_name = Column(String(200), nullable=False, default="")
    customer_email = Column(String(200), nullable=False, default="")
    customer_phone = Column(String(30), nullable=False, default="")
    # Condiciones del crédito solicitado
    amount_requested = Column(Numeric(12, 2), nullable=False)
    loan_product = Column(String(60), nullable=False, default="personal")  # personal | nomina | pyme | otro
    term_months = Column(Integer, nullable=True)                   # plazo en meses
    purpose = Column(String(300), nullable=False, default="")      # propósito / destino del crédito
    # Respuesta de la institución financiera
    status = Column(String(30), nullable=False, default="pending")
    # pending | reviewing | approved | rejected | disbursed | cancelled
    if_folio = Column(String(100), nullable=True)                  # folio asignado por la IF
    if_approved_amount = Column(Numeric(12, 2), nullable=True)     # monto aprobado (puede diferir)
    if_interest_rate = Column(Numeric(6, 4), nullable=True)        # tasa anual aprobada
    if_response_notes = Column(Text, nullable=True)                # observaciones de la IF
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)


class CheckoutPayment(Base):
    """Registro de cada pago/intento de pago vinculado a un checkout."""
    __tablename__ = "mt_checkout_payments"

    id = Column(Integer, primary_key=True)
    session_key = Column(String(120), nullable=False, index=True)
    order_reference = Column(String(100), nullable=False)
    # efectivo | paypal | billetera_if | prestamo_if
    payment_method = Column(String(20), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    # Datos según método
    paypal_order_id = Column(String(100), nullable=True)
    paypal_capture_id = Column(String(100), nullable=True)
    if_wallet_transaction_id = Column(Integer, nullable=True)      # → mt_if_wallet_transactions.id
    loan_request_id = Column(Integer, nullable=True)               # → mt_loan_requests.id
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class VendorPayout(Base):
    """Liquidaciones a vendedores (registro histórico)."""
    __tablename__ = "vendor_payouts"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, nullable=False, index=True)
    order_id = Column(Integer, nullable=False, index=True)
    vendor_amount = Column(Numeric(10, 2), nullable=False)
    platform_commission = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

