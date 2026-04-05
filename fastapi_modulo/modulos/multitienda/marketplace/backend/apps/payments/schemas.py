from __future__ import annotations

from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field


# ── Checkout base ──────────────────────────────────────────────────────────────

class CheckoutBase(BaseModel):
    order_reference: str = Field(..., description="UUID o número de orden generado por el frontend")
    amount: Decimal = Field(..., gt=0, description="Monto total a cobrar")
    customer_name: str = ""
    customer_email: str = ""
    customer_phone: str = ""


# ── Efectivo ───────────────────────────────────────────────────────────────────

class CashCheckoutIn(CheckoutBase):
    delivery_address: str = ""
    notes: str = ""


# ── PayPal ────────────────────────────────────────────────────────────────────

class PayPalCheckoutIn(CheckoutBase):
    return_url: str = Field(..., description="URL a la que PayPal redirige tras aprobación")
    cancel_url: str = Field(..., description="URL a la que PayPal redirige si el usuario cancela")
    currency: str = Field("MXN", description="Código ISO 4217")


class PayPalCaptureIn(BaseModel):
    paypal_order_id: str = Field(..., description="ID de la orden PayPal devuelto en el paso anterior")
    payment_id: int = Field(..., description="ID del CheckoutPayment registrado al crear la orden")


# ── Billetera institución financiera ──────────────────────────────────────────

class IFWalletLinkIn(BaseModel):
    """Vincula la sesión actual con la cuenta de billetera IF del socio."""
    member_number: str = Field(..., description="Número de socio / afiliado en la institución financiera")
    account_number: str = Field(..., description="Número de cuenta de billetera IF")


class IFWalletCheckoutIn(CheckoutBase):
    """Pago con la billetera electrónica de la institución financiera."""
    member_number: str = Field(..., description="Número de socio / afiliado")
    account_number: str = Field(..., description="Número de cuenta de billetera IF")


# ── Solicitud de préstamo (institución financiera) ────────────────────────────

class LoanRequestIn(BaseModel):
    order_reference: str = Field(..., description="UUID o número de orden a financiar")
    amount_requested: Decimal = Field(..., gt=0, description="Monto total a financiar")
    member_number: str = Field(..., description="Número de socio / afiliado en la institución financiera")
    customer_name: str = Field(..., min_length=2)
    customer_email: str = ""
    customer_phone: str = ""
    loan_product: Literal["personal", "nomina", "pyme", "hipotecario", "automotriz", "otro"] = "personal"
    term_months: Optional[int] = Field(None, ge=1, le=360, description="Plazo solicitado en meses")
    purpose: str = Field("", description="Propósito o destino del crédito")


class LoanStatusUpdateIn(BaseModel):
    """Permite a un webhook/endpoint interno actualizar el estado de un préstamo."""
    status: Literal["reviewing", "approved", "rejected", "disbursed", "cancelled"]
    if_folio: Optional[str] = None
    if_approved_amount: Optional[Decimal] = None
    if_interest_rate: Optional[Decimal] = None
    if_response_notes: Optional[str] = None


# ── Respuestas ────────────────────────────────────────────────────────────────

class IFWalletOut(BaseModel):
    session_key: str
    member_number: str
    account_number: str
    cached_balance: Optional[float] = None
    currency: str
    status: str
    last_synced_at: Optional[str] = None

    class Config:
        from_attributes = True


class IFWalletTransactionOut(BaseModel):
    id: int
    type: str
    amount: float
    reference_id: Optional[str] = None
    if_transaction_ref: Optional[str] = None
    description: str
    status: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class LoanRequestOut(BaseModel):
    id: int
    order_reference: str
    member_number: str
    customer_name: str
    amount_requested: float
    loan_product: str
    term_months: Optional[int] = None
    purpose: str
    status: str
    if_folio: Optional[str] = None
    if_approved_amount: Optional[float] = None
    if_interest_rate: Optional[float] = None
    if_response_notes: Optional[str] = None
    created_at: Optional[str] = None
    reviewed_at: Optional[str] = None

    class Config:
        from_attributes = True


class CheckoutPaymentOut(BaseModel):
    id: int
    order_reference: str
    payment_method: str
    amount: float
    status: str
    paypal_order_id: Optional[str] = None
    paypal_capture_id: Optional[str] = None
    if_wallet_transaction_id: Optional[int] = None
    loan_request_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class VendorPayoutCreate(BaseModel):
    vendor_id: int
    order_id: int
    vendor_amount: float
    platform_commission: float
    status: Literal["pending", "paid", "cancelled"]



class VendorPayoutRead(BaseModel):
    id: int
    vendor_id: int
    order_id: int
    vendor_amount: float
    platform_commission: float
    status: str

    class Config:
        from_attributes = True
