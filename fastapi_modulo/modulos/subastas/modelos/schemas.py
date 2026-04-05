from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, EmailStr, Field, field_validator

from .db_models import AuctionState, AwardState, BidderState, DeliveryState, PaymentState


# ─────────────────────────────────────────────────────────────────────────────
# Schemas de entrada — Crear
# ─────────────────────────────────────────────────────────────────────────────

class AuctionCreate(BaseModel):
    name: str = Field(min_length=3, max_length=180)
    description: str | None = None
    business_id: int | None = None
    auction_type: str = 'ascending'
    visibility: Literal['public', 'private'] = 'public'
    currency: str = Field(default='MXN', min_length=3, max_length=10)
    min_increment: Decimal = Field(default=Decimal('10.00'), ge=0)
    reserve_price: Decimal | None = Field(default=None, ge=0)
    start_at: datetime | None = None
    end_at: datetime | None = None
    auto_extend_seconds: int = Field(default=0, ge=0)
    terms: str | None = None
    created_by: str | None = None

    @field_validator('end_at')
    @classmethod
    def validate_end_after_start(cls, v, info):
        start_at = info.data.get('start_at')
        if v and start_at and v <= start_at:
            raise ValueError('La fecha final debe ser mayor a la fecha inicial.')
        return v


class AuctionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=180)
    description: str | None = None
    visibility: Literal['public', 'private'] | None = None
    min_increment: Decimal | None = Field(default=None, ge=0)
    reserve_price: Decimal | None = Field(default=None, ge=0)
    start_at: datetime | None = None
    end_at: datetime | None = None
    auto_extend_seconds: int | None = Field(default=None, ge=0)
    state: AuctionState | None = None
    terms: str | None = None


class LotCreate(BaseModel):
    auction_id: int
    code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=2, max_length=180)
    description: str | None = None
    category: str | None = Field(default=None, max_length=80)
    quantity: int = Field(default=1, gt=0)
    base_price: Decimal = Field(default=Decimal('0.00'), ge=0)
    reserve_price: Decimal | None = Field(default=None, ge=0)
    status_note: str | None = Field(default=None, max_length=200)
    image_url: str | None = None


class LotUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=180)
    description: str | None = None
    category: str | None = Field(default=None, max_length=80)
    quantity: int | None = Field(default=None, gt=0)
    base_price: Decimal | None = Field(default=None, ge=0)
    reserve_price: Decimal | None = Field(default=None, ge=0)
    status_note: str | None = Field(default=None, max_length=200)
    image_url: str | None = None


class BidderCreate(BaseModel):
    full_name: str = Field(min_length=3, max_length=160)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    document_id: str | None = Field(default=None, max_length=80)
    guarantee_amount: Decimal = Field(default=Decimal('0.00'), ge=0)


class BidderUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=3, max_length=160)
    phone: str | None = Field(default=None, max_length=30)
    document_id: str | None = Field(default=None, max_length=80)
    state: BidderState | None = None
    guarantee_amount: Decimal | None = Field(default=None, ge=0)
    is_active: bool | None = None


class RegistrationCreate(BaseModel):
    auction_id: int
    bidder_id: int
    is_authorized: bool = False
    approved_by: str | None = None


class RegistrationApprove(BaseModel):
    approved_by: str = Field(min_length=1, max_length=120)


class BidCreate(BaseModel):
    auction_id: int
    bidder_id: int
    amount: Decimal = Field(gt=0)
    source: Literal['web', 'admin', 'api'] = 'web'


class AwardCreate(BaseModel):
    auction_id: int
    bidder_id: int | None = None
    winning_bid_id: int | None = None
    final_amount: Decimal = Field(ge=0)
    due_at: datetime | None = None
    notes: str | None = None


class AwardUpdateState(BaseModel):
    state: AwardState
    notes: str | None = None


class PaymentCreate(BaseModel):
    award_id: int
    amount: Decimal = Field(gt=0)
    state: PaymentState = PaymentState.pending
    method: str | None = Field(default=None, max_length=50)
    reference: str | None = Field(default=None, max_length=80)
    paid_at: datetime | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Schemas de salida — Out
# ─────────────────────────────────────────────────────────────────────────────

class LotOut(BaseModel):
    id: int
    auction_id: int
    code: str
    name: str
    description: str | None
    category: str | None
    quantity: int
    base_price: Decimal
    reserve_price: Decimal | None
    status_note: str | None
    image_url: str | None
    created_at: datetime

    model_config = {'from_attributes': True}


class BidderOut(BaseModel):
    id: int
    full_name: str
    email: str
    phone: str | None
    document_id: str | None
    state: BidderState
    guarantee_amount: Decimal
    is_active: bool
    created_at: datetime

    model_config = {'from_attributes': True}


class RegistrationOut(BaseModel):
    id: int
    auction_id: int
    bidder_id: int
    is_authorized: bool
    approved_by: str | None
    approved_at: datetime | None
    created_at: datetime

    model_config = {'from_attributes': True}


class BidOut(BaseModel):
    id: int
    auction_id: int
    bidder_id: int
    amount: Decimal
    is_valid: bool
    source: str
    created_at: datetime

    model_config = {'from_attributes': True}


class PaymentOut(BaseModel):
    id: int
    award_id: int
    amount: Decimal
    state: PaymentState
    method: str | None
    reference: str | None
    paid_at: datetime | None
    created_at: datetime

    model_config = {'from_attributes': True}


class AwardOut(BaseModel):
    id: int
    auction_id: int
    bidder_id: int | None
    winning_bid_id: int | None
    final_amount: Decimal
    state: AwardState
    awarded_at: datetime | None
    due_at: datetime | None
    notes: str | None

    model_config = {'from_attributes': True}


class EventOut(BaseModel):
    id: int
    auction_id: int
    event_type: str
    actor: str | None
    description: str
    created_at: datetime

    model_config = {'from_attributes': True}


class AuctionOut(BaseModel):
    id: int
    name: str
    description: str | None
    business_id: int | None
    auction_type: str
    state: AuctionState
    visibility: str
    currency: str
    min_increment: Decimal
    reserve_price: Decimal | None
    start_at: datetime | None
    end_at: datetime | None
    auto_extend_seconds: int
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}


class AuctionDetail(AuctionOut):
    """Vista extendida de subasta con datos calculados y relaciones."""
    lots: list[LotOut] = []
    highest_bid: Decimal = Decimal('0.00')
    bids_count: int = 0
    award: AwardOut | None = None

    model_config = {'from_attributes': True}


# ─────────────────────────────────────────────────────────────────────────────
# Paginación genérica
# ─────────────────────────────────────────────────────────────────────────────

T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int

    @property
    def pages(self) -> int:
        if self.page_size == 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size


# ─────────────────────────────────────────────────────────────────────────────
# Entrega
# ─────────────────────────────────────────────────────────────────────────────

class DeliveryCreate(BaseModel):
    award_id: int
    scheduled_at: datetime | None = None
    delivery_address: str | None = Field(default=None, max_length=300)
    delivery_notes: str | None = None
    # Referencia opcional hacia una orden del módulo multitienda
    # (order_uuid o order_number). Sin FK directa — solo texto.
    external_order_ref: str | None = Field(default=None, max_length=120)
    created_by: str | None = Field(default=None, max_length=120)


class DeliveryUpdate(BaseModel):
    state: DeliveryState | None = None
    scheduled_at: datetime | None = None
    delivery_address: str | None = Field(default=None, max_length=300)
    delivery_notes: str | None = None
    external_order_ref: str | None = Field(default=None, max_length=120)


class DeliveryConfirm(BaseModel):
    received_by: str = Field(min_length=1, max_length=160)
    evidence_url: str | None = Field(default=None, max_length=500)
    delivery_notes: str | None = None


class DeliveryOut(BaseModel):
    id: int
    award_id: int
    state: DeliveryState
    scheduled_at: datetime | None
    delivery_address: str | None
    delivery_notes: str | None
    delivered_at: datetime | None
    received_by: str | None
    evidence_url: str | None
    external_order_ref: str | None
    created_by: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}


# ─────────────────────────────────────────────────────────────────────────────
# Configuración global — Fase 8
# ─────────────────────────────────────────────────────────────────────────────

class ConfiguracionUpdate(BaseModel):
    min_increment_global: Decimal | None = Field(default=None, ge=0)
    extension_seconds: int | None = Field(default=None, ge=0)
    payment_days: int | None = Field(default=None, ge=1)
    auto_award: bool | None = None
    default_visibility: Literal['public', 'private'] | None = None


class ConfiguracionOut(BaseModel):
    id: int
    min_increment_global: Decimal
    extension_seconds: int
    payment_days: int
    auto_award: bool
    default_visibility: str
    updated_at: datetime

    model_config = {'from_attributes': True}


# ─────────────────────────────────────────────────────────────────────────────
# Resultado de tick del scheduler — Fase 8
# ─────────────────────────────────────────────────────────────────────────────

class SchedulerTickResult(BaseModel):
    published: int
    closed: int
    expired_awards: int
