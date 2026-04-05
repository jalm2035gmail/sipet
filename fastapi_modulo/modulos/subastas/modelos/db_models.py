from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class AuctionState(str, Enum):
    draft = 'draft'
    scheduled = 'scheduled'
    published = 'published'
    live = 'live'
    suspended = 'suspended'
    closed = 'closed'
    awarded = 'awarded'
    deserted = 'deserted'
    cancelled = 'cancelled'


class BidderState(str, Enum):
    pending = 'pending'
    approved = 'approved'
    rejected = 'rejected'
    suspended = 'suspended'


class AwardState(str, Enum):
    pending = 'pending'
    awarded = 'awarded'
    payment_pending = 'payment_pending'
    paid = 'paid'
    expired = 'expired'
    cancelled = 'cancelled'
    reassigned = 'reassigned'


class PaymentState(str, Enum):
    pending = 'pending'
    partial = 'partial'
    paid = 'paid'
    failed = 'failed'
    refunded = 'refunded'


class DeliveryState(str, Enum):
    pending = 'pending'       # Adjudicación pagada, entrega aún no programada
    scheduled = 'scheduled'   # Fecha y lugar confirmados
    in_transit = 'in_transit' # En camino o en proceso de retiro
    delivered = 'delivered'   # Entregado y confirmado por el receptor
    cancelled = 'cancelled'   # Cancelado (devuelto, reasignado, etc.)


class Auction(Base):
    __tablename__ = 'sub_auction'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text())
    business_id: Mapped[int | None] = mapped_column(index=True)
    auction_type: Mapped[str] = mapped_column(String(60), default='ascending', nullable=False)
    state: Mapped[AuctionState] = mapped_column(SAEnum(AuctionState), default=AuctionState.draft, nullable=False, index=True)
    visibility: Mapped[str] = mapped_column(String(30), default='public', nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default='MXN', nullable=False)
    min_increment: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal('10.00'), nullable=False)
    reserve_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), index=True)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), index=True)
    auto_extend_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    terms: Mapped[str | None] = mapped_column(Text())
    created_by: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    lots: Mapped[list['Lot']] = relationship(back_populates='auction', cascade='all, delete-orphan')
    registrations: Mapped[list['AuctionRegistration']] = relationship(back_populates='auction', cascade='all, delete-orphan')
    bids: Mapped[list['Bid']] = relationship(back_populates='auction', cascade='all, delete-orphan')
    award: Mapped['Award | None'] = relationship(back_populates='auction', cascade='all, delete-orphan', uselist=False)
    events: Mapped[list['AuctionEvent']] = relationship(back_populates='auction', cascade='all, delete-orphan')

    __table_args__ = (
        CheckConstraint('min_increment >= 0', name='ck_sub_auction_min_increment_nonnegative'),
    )


class Lot(Base):
    __tablename__ = 'sub_lot'

    id: Mapped[int] = mapped_column(primary_key=True)
    auction_id: Mapped[int] = mapped_column(ForeignKey('sub_auction.id', ondelete='CASCADE'), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text())
    category: Mapped[str | None] = mapped_column(String(80))
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    base_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    reserve_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    status_note: Mapped[str | None] = mapped_column(String(200))
    image_url: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)

    auction: Mapped['Auction'] = relationship(back_populates='lots')

    __table_args__ = (
        UniqueConstraint('auction_id', 'code', name='uq_sub_lot_auction_code'),
        CheckConstraint('quantity > 0', name='ck_sub_lot_quantity_positive'),
        CheckConstraint('base_price >= 0', name='ck_sub_lot_base_price_nonnegative'),
    )


class Bidder(Base):
    __tablename__ = 'sub_bidder'

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(160), nullable=False, unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(30))
    document_id: Mapped[str | None] = mapped_column(String(80))
    state: Mapped[BidderState] = mapped_column(SAEnum(BidderState), default=BidderState.pending, nullable=False, index=True)
    guarantee_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)

    registrations: Mapped[list['AuctionRegistration']] = relationship(back_populates='bidder', cascade='all, delete-orphan')
    bids: Mapped[list['Bid']] = relationship(back_populates='bidder', cascade='all, delete-orphan')
    awards: Mapped[list['Award']] = relationship(back_populates='bidder')


class AuctionRegistration(Base):
    __tablename__ = 'sub_auction_registration'

    id: Mapped[int] = mapped_column(primary_key=True)
    auction_id: Mapped[int] = mapped_column(ForeignKey('sub_auction.id', ondelete='CASCADE'), nullable=False, index=True)
    bidder_id: Mapped[int] = mapped_column(ForeignKey('sub_bidder.id', ondelete='CASCADE'), nullable=False, index=True)
    is_authorized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approved_by: Mapped[str | None] = mapped_column(String(120))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)

    auction: Mapped['Auction'] = relationship(back_populates='registrations')
    bidder: Mapped['Bidder'] = relationship(back_populates='registrations')

    __table_args__ = (
        UniqueConstraint('auction_id', 'bidder_id', name='uq_sub_registration_auction_bidder'),
    )


class Bid(Base):
    __tablename__ = 'sub_bid'

    id: Mapped[int] = mapped_column(primary_key=True)
    auction_id: Mapped[int] = mapped_column(ForeignKey('sub_auction.id', ondelete='CASCADE'), nullable=False, index=True)
    bidder_id: Mapped[int] = mapped_column(ForeignKey('sub_bidder.id', ondelete='CASCADE'), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, index=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    source: Mapped[str] = mapped_column(String(30), default='web', nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False, index=True)

    auction: Mapped['Auction'] = relationship(back_populates='bids')
    bidder: Mapped['Bidder'] = relationship(back_populates='bids')

    __table_args__ = (
        CheckConstraint('amount >= 0', name='ck_sub_bid_amount_nonnegative'),
    )


class Award(Base):
    __tablename__ = 'sub_award'

    id: Mapped[int] = mapped_column(primary_key=True)
    auction_id: Mapped[int] = mapped_column(ForeignKey('sub_auction.id', ondelete='CASCADE'), nullable=False, unique=True)
    bidder_id: Mapped[int | None] = mapped_column(ForeignKey('sub_bidder.id', ondelete='SET NULL'), index=True)
    winning_bid_id: Mapped[int | None] = mapped_column(ForeignKey('sub_bid.id', ondelete='SET NULL'))
    final_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal('0.00'), nullable=False)
    state: Mapped[AwardState] = mapped_column(SAEnum(AwardState), default=AwardState.pending, nullable=False, index=True)
    awarded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    notes: Mapped[str | None] = mapped_column(Text())

    auction: Mapped['Auction'] = relationship(back_populates='award')
    bidder: Mapped['Bidder | None'] = relationship(back_populates='awards')
    payments: Mapped[list['Payment']] = relationship(back_populates='award', cascade='all, delete-orphan')
    deliveries: Mapped[list['Delivery']] = relationship(back_populates='award', cascade='all, delete-orphan')


class Payment(Base):
    __tablename__ = 'sub_payment'

    id: Mapped[int] = mapped_column(primary_key=True)
    award_id: Mapped[int] = mapped_column(ForeignKey('sub_award.id', ondelete='CASCADE'), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    state: Mapped[PaymentState] = mapped_column(SAEnum(PaymentState), default=PaymentState.pending, nullable=False)
    method: Mapped[str | None] = mapped_column(String(50))
    reference: Mapped[str | None] = mapped_column(String(80))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False)

    award: Mapped['Award'] = relationship(back_populates='payments')


class AuctionEvent(Base):
    __tablename__ = 'sub_event'

    id: Mapped[int] = mapped_column(primary_key=True)
    auction_id: Mapped[int] = mapped_column(ForeignKey('sub_auction.id', ondelete='CASCADE'), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    actor: Mapped[str | None] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, nullable=False, index=True)

    auction: Mapped['Auction'] = relationship(back_populates='events')


class ConfiguracionSubastas(Base):
    """Configuración global del módulo de subastas.

    Diseñada como singleton (id=1). Sus valores son los defaults del módulo
    cuando una subasta individual no define los suyos propios.
    """
    __tablename__ = 'sub_configuracion'

    id: Mapped[int] = mapped_column(primary_key=True)
    # Incremento mínimo de puja cuando la subasta no define el suyo
    min_increment_global: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal('10.00'), nullable=False
    )
    # Segundos de extensión automática en el tramo final de la subasta
    extension_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Días de plazo para pagar desde la adjudicación
    payment_days: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    # Adjudicación automática al cerrar la subasta (True) o manual (False)
    auto_award: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Visibilidad por defecto para nuevas subastas
    default_visibility: Mapped[str] = mapped_column(String(30), default='public', nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        CheckConstraint('min_increment_global >= 0', name='ck_sub_config_min_increment_nonnegative'),
        CheckConstraint('extension_seconds >= 0', name='ck_sub_config_extension_seconds_nonnegative'),
        CheckConstraint('payment_days >= 1', name='ck_sub_config_payment_days_positive'),
    )


class Delivery(Base):
    """Registro de entrega o retiro del bien adjudicado.

    Diseñado para ser autocontenido dentro del módulo subastas.
    El campo `external_order_ref` permite referenciar opcionalmente una orden
    del módulo multitienda (order_uuid / order_number) sin FK directa,
    manteniendo la independencia entre módulos.
    """
    __tablename__ = 'sub_delivery'

    id: Mapped[int] = mapped_column(primary_key=True)
    award_id: Mapped[int] = mapped_column(
        ForeignKey('sub_award.id', ondelete='CASCADE'), nullable=False, index=True
    )
    state: Mapped[DeliveryState] = mapped_column(
        SAEnum(DeliveryState), default=DeliveryState.pending, nullable=False, index=True
    )
    # Datos de programación
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    delivery_address: Mapped[str | None] = mapped_column(String(300))
    delivery_notes: Mapped[str | None] = mapped_column(Text())
    # Confirmación de recepción
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    received_by: Mapped[str | None] = mapped_column(String(160))
    evidence_url: Mapped[str | None] = mapped_column(String(500))
    # Referencia externa opcional hacia multitienda (order_uuid o order_number)
    # Sin FK directa para preservar independencia modular
    external_order_ref: Mapped[str | None] = mapped_column(String(120), index=True)
    # Auditoría
    created_by: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    award: Mapped['Award'] = relationship(back_populates='deliveries')
