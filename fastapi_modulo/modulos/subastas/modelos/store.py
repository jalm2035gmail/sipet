from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db_models import (
    Auction,
    AuctionEvent,
    AuctionRegistration,
    AuctionState,
    Award,
    AwardState,
    Bid,
    Bidder,
    BidderState,
    ConfiguracionSubastas,
    Delivery,
    DeliveryState,
    Lot,
    Payment,
    PaymentState,
)
from .schemas import (
    AuctionCreate,
    AuctionUpdate,
    AwardCreate,
    AwardUpdateState,
    BidCreate,
    BidderCreate,
    BidderUpdate,
    ConfiguracionUpdate,
    DeliveryConfirm,
    DeliveryCreate,
    DeliveryUpdate,
    LotCreate,
    LotUpdate,
    PaymentCreate,
    RegistrationApprove,
    RegistrationCreate,
)


class BusinessRuleError(ValueError):
    pass


# ─────────────────────────────────────────────────────────────────────────────
# Utilidades internas
# ─────────────────────────────────────────────────────────────────────────────

def _event(db: Session, auction_id: int, event_type: str, description: str, actor: str | None = None) -> None:
    db.add(AuctionEvent(auction_id=auction_id, event_type=event_type, description=description, actor=actor))


def _current_highest_bid(db: Session, auction_id: int) -> Bid | None:
    stmt = (
        select(Bid)
        .where(Bid.auction_id == auction_id, Bid.is_valid.is_(True))
        .order_by(Bid.amount.desc(), Bid.created_at.asc())
        .limit(1)
    )
    return db.scalars(stmt).first()


# ─────────────────────────────────────────────────────────────────────────────
# Subastas
# ─────────────────────────────────────────────────────────────────────────────

def create_auction(db: Session, data: AuctionCreate) -> Auction:
    auction = Auction(**data.model_dump())
    db.add(auction)
    db.commit()
    db.refresh(auction)
    _event(db, auction.id, 'auction_created', f'Subasta {auction.name} creada.', actor=data.created_by)
    db.commit()
    return auction


def update_auction(db: Session, auction_id: int, data: AuctionUpdate) -> Auction:
    auction = get_auction(db, auction_id)
    if not auction:
        raise BusinessRuleError('Subasta no encontrada.')
    payload = data.model_dump(exclude_unset=True)
    for key, value in payload.items():
        setattr(auction, key, value)
    auction.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(auction)
    _event(db, auction.id, 'auction_updated', 'Subasta actualizada.')
    db.commit()
    return auction


def get_auction(db: Session, auction_id: int) -> Auction | None:
    return db.get(Auction, auction_id)


def list_auctions(
    db: Session,
    state: str | None = None,
    business_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Auction]:
    stmt = select(Auction).order_by(Auction.id.desc()).limit(limit).offset(offset)
    if state:
        stmt = stmt.where(Auction.state == state)
    if business_id is not None:
        stmt = stmt.where(Auction.business_id == business_id)
    return list(db.scalars(stmt).all())


def count_auctions(db: Session, state: str | None = None, business_id: int | None = None) -> int:
    stmt = select(func.count()).select_from(Auction)
    if state:
        stmt = stmt.where(Auction.state == state)
    if business_id is not None:
        stmt = stmt.where(Auction.business_id == business_id)
    return db.scalar(stmt) or 0


# ─────────────────────────────────────────────────────────────────────────────
# Transiciones de estado de subasta
# ─────────────────────────────────────────────────────────────────────────────

_PUBLISHABLE_STATES = {AuctionState.draft, AuctionState.scheduled}
_SUSPENDABLE_STATES = {AuctionState.published, AuctionState.live}
_CANCELLABLE_STATES = {
    AuctionState.draft,
    AuctionState.scheduled,
    AuctionState.published,
    AuctionState.live,
    AuctionState.suspended,
}


def publish_auction(db: Session, auction_id: int, actor: str | None = None) -> Auction:
    auction = get_auction(db, auction_id)
    if not auction:
        raise BusinessRuleError('Subasta no encontrada.')
    if auction.state not in _PUBLISHABLE_STATES:
        raise BusinessRuleError(f'No se puede publicar una subasta en estado {auction.state}.')
    auction.state = AuctionState.published
    auction.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(auction)
    _event(db, auction.id, 'auction_published', 'Subasta publicada.', actor=actor)
    db.commit()
    return auction


def set_live(db: Session, auction_id: int, actor: str | None = None) -> Auction:
    auction = get_auction(db, auction_id)
    if not auction:
        raise BusinessRuleError('Subasta no encontrada.')
    if auction.state != AuctionState.published:
        raise BusinessRuleError(f'Solo una subasta publicada puede pasar a en curso (estado actual: {auction.state}).')
    auction.state = AuctionState.live
    auction.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(auction)
    _event(db, auction.id, 'auction_live', 'Subasta iniciada en curso.', actor=actor)
    db.commit()
    return auction


def suspend_auction(db: Session, auction_id: int, actor: str | None = None, reason: str | None = None) -> Auction:
    auction = get_auction(db, auction_id)
    if not auction:
        raise BusinessRuleError('Subasta no encontrada.')
    if auction.state not in _SUSPENDABLE_STATES:
        raise BusinessRuleError(f'No se puede suspender una subasta en estado {auction.state}.')
    auction.state = AuctionState.suspended
    auction.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(auction)
    _event(db, auction.id, 'auction_suspended', f'Subasta suspendida. {reason or ""}', actor=actor)
    db.commit()
    return auction


def cancel_auction(db: Session, auction_id: int, actor: str | None = None, reason: str | None = None) -> Auction:
    auction = get_auction(db, auction_id)
    if not auction:
        raise BusinessRuleError('Subasta no encontrada.')
    if auction.state not in _CANCELLABLE_STATES:
        raise BusinessRuleError(f'No se puede cancelar una subasta en estado {auction.state}.')
    auction.state = AuctionState.cancelled
    auction.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(auction)
    _event(db, auction.id, 'auction_cancelled', f'Subasta cancelada. {reason or ""}', actor=actor)
    db.commit()
    return auction


def close_auction(db: Session, auction_id: int, actor: str | None = None) -> Auction:
    auction = get_auction(db, auction_id)
    if not auction:
        raise BusinessRuleError('Subasta no encontrada.')
    highest = _current_highest_bid(db, auction_id)
    reserve_not_met = (
        highest is not None
        and auction.reserve_price is not None
        and Decimal(str(highest.amount)) < Decimal(str(auction.reserve_price))
    )
    if highest and not reserve_not_met:
        auction.state = AuctionState.awarded
        award = Award(
            auction_id=auction.id,
            bidder_id=highest.bidder_id,
            winning_bid_id=highest.id,
            final_amount=highest.amount,
            state=AwardState.awarded,
            awarded_at=datetime.utcnow(),
        )
        db.add(award)
        _event(db, auction.id, 'auction_awarded', f'Subasta adjudicada por {highest.amount}.', actor=actor)
    else:
        auction.state = AuctionState.deserted
        if reserve_not_met:
            _event(
                db, auction.id, 'auction_deserted',
                f'Subasta desierta: precio de reserva {auction.reserve_price} no alcanzado (mejor puja: {highest.amount}).',
                actor=actor,
            )
        else:
            _event(db, auction.id, 'auction_deserted', 'Subasta desierta sin pujas válidas.', actor=actor)
    auction.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(auction)
    return auction


# ─────────────────────────────────────────────────────────────────────────────
# Lotes
# ─────────────────────────────────────────────────────────────────────────────

def create_lot(db: Session, data: LotCreate) -> Lot:
    auction = get_auction(db, data.auction_id)
    if not auction:
        raise BusinessRuleError('La subasta no existe.')
    lot = Lot(**data.model_dump())
    db.add(lot)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise BusinessRuleError('Código de lote duplicado en la subasta.') from exc
    db.refresh(lot)
    _event(db, lot.auction_id, 'lot_created', f'Lote {lot.code} - {lot.name} creado.')
    db.commit()
    return lot


def get_lot(db: Session, lot_id: int) -> Lot | None:
    return db.get(Lot, lot_id)


def list_lots(db: Session, auction_id: int) -> list[Lot]:
    stmt = select(Lot).where(Lot.auction_id == auction_id).order_by(Lot.id)
    return list(db.scalars(stmt).all())


def update_lot(db: Session, lot_id: int, data: LotUpdate) -> Lot:
    lot = get_lot(db, lot_id)
    if not lot:
        raise BusinessRuleError('Lote no encontrado.')
    payload = data.model_dump(exclude_unset=True)
    for key, value in payload.items():
        setattr(lot, key, value)
    db.commit()
    db.refresh(lot)
    _event(db, lot.auction_id, 'lot_updated', f'Lote {lot.code} actualizado.')
    db.commit()
    return lot


def delete_lot(db: Session, lot_id: int) -> None:
    lot = get_lot(db, lot_id)
    if not lot:
        raise BusinessRuleError('Lote no encontrado.')
    auction = get_auction(db, lot.auction_id)
    if auction and auction.state not in {AuctionState.draft, AuctionState.scheduled}:
        raise BusinessRuleError('Solo se pueden eliminar lotes de subastas en borrador o programadas.')
    _event(db, lot.auction_id, 'lot_deleted', f'Lote {lot.code} eliminado.')
    db.commit()
    db.delete(lot)
    db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Postores
# ─────────────────────────────────────────────────────────────────────────────

def create_bidder(db: Session, data: BidderCreate) -> Bidder:
    bidder = Bidder(**data.model_dump())
    db.add(bidder)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise BusinessRuleError('El email del postor ya existe.') from exc
    db.refresh(bidder)
    return bidder


def get_bidder(db: Session, bidder_id: int) -> Bidder | None:
    return db.get(Bidder, bidder_id)


def list_bidders(
    db: Session,
    state: BidderState | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Bidder]:
    stmt = select(Bidder).order_by(Bidder.id.desc()).limit(limit).offset(offset)
    if state:
        stmt = stmt.where(Bidder.state == state)
    return list(db.scalars(stmt).all())


def count_bidders(db: Session, state: BidderState | None = None) -> int:
    stmt = select(func.count()).select_from(Bidder)
    if state:
        stmt = stmt.where(Bidder.state == state)
    return db.scalar(stmt) or 0


def update_bidder(db: Session, bidder_id: int, data: BidderUpdate) -> Bidder:
    bidder = get_bidder(db, bidder_id)
    if not bidder:
        raise BusinessRuleError('Postor no encontrado.')
    payload = data.model_dump(exclude_unset=True)
    for key, value in payload.items():
        setattr(bidder, key, value)
    db.commit()
    db.refresh(bidder)
    return bidder


def approve_bidder(db: Session, bidder_id: int, actor: str | None = None) -> Bidder:
    bidder = get_bidder(db, bidder_id)
    if not bidder:
        raise BusinessRuleError('Postor no encontrado.')
    if bidder.state == BidderState.approved:
        raise BusinessRuleError('El postor ya está aprobado.')
    bidder.state = BidderState.approved
    db.commit()
    db.refresh(bidder)
    return bidder


# ─────────────────────────────────────────────────────────────────────────────
# Registros de participación
# ─────────────────────────────────────────────────────────────────────────────

def register_bidder(db: Session, data: RegistrationCreate) -> AuctionRegistration:
    auction = get_auction(db, data.auction_id)
    bidder = db.get(Bidder, data.bidder_id)
    if not auction or not bidder:
        raise BusinessRuleError('Subasta o postor no encontrado.')
    reg = AuctionRegistration(
        auction_id=data.auction_id,
        bidder_id=data.bidder_id,
        is_authorized=data.is_authorized,
        approved_by=data.approved_by,
        approved_at=datetime.utcnow() if data.is_authorized else None,
    )
    db.add(reg)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise BusinessRuleError('El postor ya está registrado en esta subasta.') from exc
    db.refresh(reg)
    _event(db, data.auction_id, 'bidder_registered', f'Postor {bidder.full_name} registrado.', actor=data.approved_by)
    db.commit()
    return reg


def list_registrations(db: Session, auction_id: int) -> list[AuctionRegistration]:
    stmt = (
        select(AuctionRegistration)
        .where(AuctionRegistration.auction_id == auction_id)
        .order_by(AuctionRegistration.id)
    )
    return list(db.scalars(stmt).all())


def get_registration(db: Session, registration_id: int) -> AuctionRegistration | None:
    return db.get(AuctionRegistration, registration_id)


def approve_registration(db: Session, registration_id: int, data: RegistrationApprove) -> AuctionRegistration:
    reg = get_registration(db, registration_id)
    if not reg:
        raise BusinessRuleError('Registro no encontrado.')
    if reg.is_authorized:
        raise BusinessRuleError('El registro ya está autorizado.')
    reg.is_authorized = True
    reg.approved_by = data.approved_by
    reg.approved_at = datetime.utcnow()
    db.commit()
    db.refresh(reg)
    _event(db, reg.auction_id, 'registration_approved', f'Registro {registration_id} aprobado.', actor=data.approved_by)
    db.commit()
    return reg


def reject_registration(db: Session, registration_id: int, actor: str | None = None) -> AuctionRegistration:
    reg = get_registration(db, registration_id)
    if not reg:
        raise BusinessRuleError('Registro no encontrado.')
    reg.is_authorized = False
    reg.approved_by = actor
    reg.approved_at = datetime.utcnow()
    db.commit()
    db.refresh(reg)
    _event(db, reg.auction_id, 'registration_rejected', f'Registro {registration_id} rechazado.', actor=actor)
    db.commit()
    return reg


# ─────────────────────────────────────────────────────────────────────────────
# Pujas
# ─────────────────────────────────────────────────────────────────────────────

def place_bid(db: Session, data: BidCreate) -> Bid:
    # Bloqueo a nivel de fila para prevenir race conditions en pujas concurrentes.
    # with_for_update() es efectivo en PostgreSQL; en SQLite se acepta sin error
    # pero no provee bloqueo real — en producción usar PostgreSQL.
    auction = db.scalars(
        select(Auction).where(Auction.id == data.auction_id).with_for_update()
    ).first()
    bidder = db.get(Bidder, data.bidder_id)
    if not auction or not bidder:
        raise BusinessRuleError('Subasta o postor no encontrado.')
    if bidder.state not in {BidderState.approved, BidderState.pending} or not bidder.is_active:
        raise BusinessRuleError('El postor no está habilitado para participar.')
    registration = db.scalars(
        select(AuctionRegistration).where(
            AuctionRegistration.auction_id == data.auction_id,
            AuctionRegistration.bidder_id == data.bidder_id,
            AuctionRegistration.is_authorized.is_(True),
        )
    ).first()
    if not registration:
        raise BusinessRuleError('El postor no está autorizado en esta subasta.')
    now = datetime.utcnow()
    if auction.state not in {AuctionState.published, AuctionState.live}:
        raise BusinessRuleError('La subasta no admite pujas en su estado actual.')
    if auction.start_at and now < auction.start_at:
        raise BusinessRuleError('La subasta aún no inicia.')
    if auction.end_at and now > auction.end_at:
        raise BusinessRuleError('La subasta ya terminó.')

    highest = _current_highest_bid(db, data.auction_id)
    if highest:
        min_required = Decimal(str(highest.amount)) + Decimal(str(auction.min_increment))
    else:
        lot_base = db.scalar(select(func.coalesce(func.sum(Lot.base_price), 0)).where(Lot.auction_id == auction.id))
        min_required = Decimal(str(lot_base))
    if Decimal(str(data.amount)) < min_required:
        raise BusinessRuleError(f'La puja mínima requerida es {min_required}.')

    bid = Bid(**data.model_dump())
    db.add(bid)

    if auction.auto_extend_seconds and auction.end_at:
        remaining = (auction.end_at - now).total_seconds()
        if 0 <= remaining <= auction.auto_extend_seconds:
            auction.end_at = auction.end_at.replace(microsecond=0)
            auction.end_at = auction.end_at + timedelta(seconds=auction.auto_extend_seconds)

    db.commit()
    db.refresh(bid)
    _event(db, auction.id, 'bid_placed', f'Nueva puja por {bid.amount} del postor {bidder.full_name}.', actor=bidder.full_name)
    db.commit()
    return bid


def list_bids(db: Session, auction_id: int, valid_only: bool = True) -> list[Bid]:
    stmt = (
        select(Bid)
        .where(Bid.auction_id == auction_id)
        .order_by(Bid.amount.desc(), Bid.created_at.asc())
    )
    if valid_only:
        stmt = stmt.where(Bid.is_valid.is_(True))
    return list(db.scalars(stmt).all())


def get_bid(db: Session, bid_id: int) -> Bid | None:
    return db.get(Bid, bid_id)


# ─────────────────────────────────────────────────────────────────────────────
# Adjudicaciones
# ─────────────────────────────────────────────────────────────────────────────

def create_award(db: Session, data: AwardCreate) -> Award:
    auction = get_auction(db, data.auction_id)
    if not auction:
        raise BusinessRuleError('Subasta no encontrada.')
    if auction.award:
        raise BusinessRuleError('La subasta ya tiene adjudicación.')
    award = Award(**data.model_dump(), state=AwardState.awarded, awarded_at=datetime.utcnow())
    db.add(award)
    auction.state = AuctionState.awarded
    db.commit()
    db.refresh(award)
    _event(db, auction.id, 'award_created', f'Adjudicación manual creada por {award.final_amount}.')
    db.commit()
    return award


def get_award(db: Session, award_id: int) -> Award | None:
    return db.get(Award, award_id)


def list_awards(
    db: Session,
    state: AwardState | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Award]:
    stmt = select(Award).order_by(Award.id.desc()).limit(limit).offset(offset)
    if state:
        stmt = stmt.where(Award.state == state)
    return list(db.scalars(stmt).all())


def update_award_state(db: Session, award_id: int, data: AwardUpdateState) -> Award:
    award = db.get(Award, award_id)
    if not award:
        raise BusinessRuleError('Adjudicación no encontrada.')
    award.state = data.state
    if data.notes:
        award.notes = (award.notes or '') + f'\n{data.notes}'
    db.commit()
    db.refresh(award)
    _event(db, award.auction_id, 'award_updated', f'Adjudicación actualizada a {award.state}.')
    db.commit()
    return award


def reassign_award(db: Session, award_id: int, new_bidder_id: int, actor: str | None = None) -> Award:
    """Reasigna la adjudicación al siguiente postor cuando el ganador no paga."""
    award = get_award(db, award_id)
    if not award:
        raise BusinessRuleError('Adjudicación no encontrada.')
    if award.state not in {AwardState.expired, AwardState.cancelled, AwardState.payment_pending}:
        raise BusinessRuleError(f'No se puede reasignar una adjudicación en estado {award.state}.')
    new_bidder = get_bidder(db, new_bidder_id)
    if not new_bidder:
        raise BusinessRuleError('Postor destino no encontrado.')

    old_bidder_id = award.bidder_id
    award.bidder_id = new_bidder_id
    award.state = AwardState.reassigned
    award.notes = (award.notes or '') + f'\nReasignada de postor {old_bidder_id} a {new_bidder_id} por {actor or "sistema"}.'
    award.awarded_at = datetime.utcnow()
    db.commit()
    db.refresh(award)
    _event(
        db, award.auction_id, 'award_reassigned',
        f'Adjudicación reasignada al postor {new_bidder.full_name}.',
        actor=actor,
    )
    db.commit()
    return award


def mark_delivery(db: Session, award_id: int, actor: str | None = None, notes: str | None = None) -> Award:
    """Marca la adjudicación como entregada/formalizada."""
    award = get_award(db, award_id)
    if not award:
        raise BusinessRuleError('Adjudicación no encontrada.')
    if award.state != AwardState.paid:
        raise BusinessRuleError('Solo se puede registrar entrega de adjudicaciones pagadas.')
    # Reutilizamos el campo notes para el registro de entrega
    delivery_note = f'\n[ENTREGA {datetime.utcnow().isoformat()}] {notes or "Entrega confirmada."} Actor: {actor or "sistema"}.'
    award.notes = (award.notes or '') + delivery_note
    db.commit()
    db.refresh(award)
    _event(db, award.auction_id, 'delivery_confirmed', f'Entrega confirmada. {notes or ""}', actor=actor)
    db.commit()
    return award


# ─────────────────────────────────────────────────────────────────────────────
# Pagos
# ─────────────────────────────────────────────────────────────────────────────

def create_payment(db: Session, data: PaymentCreate) -> Payment:
    award = db.get(Award, data.award_id)
    if not award:
        raise BusinessRuleError('Adjudicación no encontrada.')
    payment = Payment(**data.model_dump())
    db.add(payment)
    db.commit()
    db.refresh(payment)

    total_paid = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.award_id == award.id,
            Payment.state.in_([PaymentState.partial, PaymentState.paid]),
        )
    )
    if Decimal(str(total_paid)) >= Decimal(str(award.final_amount)):
        award.state = AwardState.paid
    else:
        award.state = AwardState.payment_pending
    db.commit()
    _event(db, award.auction_id, 'payment_created', f'Pago registrado por {payment.amount}.')
    db.commit()
    return payment


def get_payment(db: Session, payment_id: int) -> Payment | None:
    return db.get(Payment, payment_id)


def list_payments(db: Session, award_id: int) -> list[Payment]:
    stmt = select(Payment).where(Payment.award_id == award_id).order_by(Payment.created_at)
    return list(db.scalars(stmt).all())


def update_payment_state(db: Session, payment_id: int, state: PaymentState, actor: str | None = None) -> Payment:
    payment = get_payment(db, payment_id)
    if not payment:
        raise BusinessRuleError('Pago no encontrado.')
    payment.state = state
    db.commit()
    db.refresh(payment)

    award = db.get(Award, payment.award_id)
    if award:
        total_paid = db.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.award_id == award.id,
                Payment.state.in_([PaymentState.partial, PaymentState.paid]),
            )
        )
        if Decimal(str(total_paid)) >= Decimal(str(award.final_amount)):
            award.state = AwardState.paid
        db.commit()
        _event(db, award.auction_id, 'payment_updated', f'Pago {payment_id} actualizado a {state}.', actor=actor)
        db.commit()
    return payment


# ─────────────────────────────────────────────────────────────────────────────
# Entrega
# ─────────────────────────────────────────────────────────────────────────────

def create_delivery(db: Session, data: DeliveryCreate) -> Delivery:
    """Crea un registro de entrega para una adjudicación pagada.

    La adjudicación debe estar en estado 'paid'. El campo external_order_ref
    permite vincular opcionalmente con una orden del módulo multitienda
    usando su order_uuid o order_number, sin acoplamiento directo.
    """
    award = get_award(db, data.award_id)
    if not award:
        raise BusinessRuleError('Adjudicación no encontrada.')
    if award.state != AwardState.paid:
        raise BusinessRuleError('Solo se puede programar entrega de adjudicaciones pagadas.')
    delivery = Delivery(
        award_id=data.award_id,
        state=DeliveryState.pending,
        scheduled_at=data.scheduled_at,
        delivery_address=data.delivery_address,
        delivery_notes=data.delivery_notes,
        external_order_ref=data.external_order_ref,
        created_by=data.created_by,
    )
    if data.scheduled_at:
        delivery.state = DeliveryState.scheduled
    db.add(delivery)
    db.commit()
    db.refresh(delivery)
    _event(
        db, award.auction_id, 'delivery_created',
        f'Entrega registrada para adjudicación {data.award_id}.'
        + (f' Ref externa: {data.external_order_ref}.' if data.external_order_ref else ''),
        actor=data.created_by,
    )
    db.commit()
    return delivery


def get_delivery(db: Session, delivery_id: int) -> Delivery | None:
    return db.get(Delivery, delivery_id)


def list_deliveries(
    db: Session,
    award_id: int | None = None,
    state: DeliveryState | None = None,
    external_order_ref: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Delivery]:
    stmt = select(Delivery).order_by(Delivery.id.desc()).limit(limit).offset(offset)
    if award_id is not None:
        stmt = stmt.where(Delivery.award_id == award_id)
    if state is not None:
        stmt = stmt.where(Delivery.state == state)
    if external_order_ref is not None:
        stmt = stmt.where(Delivery.external_order_ref == external_order_ref)
    return list(db.scalars(stmt).all())


def update_delivery(db: Session, delivery_id: int, data: DeliveryUpdate) -> Delivery:
    delivery = get_delivery(db, delivery_id)
    if not delivery:
        raise BusinessRuleError('Entrega no encontrada.')
    if delivery.state == DeliveryState.delivered:
        raise BusinessRuleError('No se puede modificar una entrega ya confirmada.')
    if delivery.state == DeliveryState.cancelled:
        raise BusinessRuleError('No se puede modificar una entrega cancelada.')
    payload = data.model_dump(exclude_unset=True)
    for key, value in payload.items():
        setattr(delivery, key, value)
    delivery.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(delivery)
    award = get_award(db, delivery.award_id)
    if award:
        _event(db, award.auction_id, 'delivery_updated', f'Entrega {delivery_id} actualizada.', actor=None)
        db.commit()
    return delivery


def confirm_delivery(db: Session, delivery_id: int, data: DeliveryConfirm, actor: str | None = None) -> Delivery:
    """Confirma la recepción del bien por parte del adjudicado."""
    delivery = get_delivery(db, delivery_id)
    if not delivery:
        raise BusinessRuleError('Entrega no encontrada.')
    if delivery.state == DeliveryState.delivered:
        raise BusinessRuleError('La entrega ya fue confirmada.')
    if delivery.state == DeliveryState.cancelled:
        raise BusinessRuleError('No se puede confirmar una entrega cancelada.')
    delivery.state = DeliveryState.delivered
    delivery.delivered_at = datetime.utcnow()
    delivery.received_by = data.received_by
    delivery.evidence_url = data.evidence_url
    if data.delivery_notes:
        delivery.delivery_notes = (delivery.delivery_notes or '') + f'\n{data.delivery_notes}'
    delivery.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(delivery)
    award = get_award(db, delivery.award_id)
    if award:
        _event(
            db, award.auction_id, 'delivery_confirmed',
            f'Entrega {delivery_id} confirmada. Recibió: {data.received_by}.',
            actor=actor,
        )
        db.commit()
    return delivery


def cancel_delivery(db: Session, delivery_id: int, actor: str | None = None, reason: str | None = None) -> Delivery:
    delivery = get_delivery(db, delivery_id)
    if not delivery:
        raise BusinessRuleError('Entrega no encontrada.')
    if delivery.state == DeliveryState.delivered:
        raise BusinessRuleError('No se puede cancelar una entrega ya confirmada.')
    if delivery.state == DeliveryState.cancelled:
        raise BusinessRuleError('La entrega ya está cancelada.')
    delivery.state = DeliveryState.cancelled
    delivery.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(delivery)
    award = get_award(db, delivery.award_id)
    if award:
        _event(
            db, award.auction_id, 'delivery_cancelled',
            f'Entrega {delivery_id} cancelada. {reason or ""}',
            actor=actor,
        )
        db.commit()
    return delivery


# ─────────────────────────────────────────────────────────────────────────────
# Auditoría
# ─────────────────────────────────────────────────────────────────────────────

def list_events(
    db: Session,
    auction_id: int,
    event_type: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> list[AuctionEvent]:
    stmt = (
        select(AuctionEvent)
        .where(AuctionEvent.auction_id == auction_id)
        .order_by(AuctionEvent.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if event_type:
        stmt = stmt.where(AuctionEvent.event_type == event_type)
    return list(db.scalars(stmt).all())


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────────────────────────────────────

def get_dashboard_stats(db: Session) -> dict:
    total_auctions = db.scalar(select(func.count()).select_from(Auction)) or 0
    total_bidders = db.scalar(select(func.count()).select_from(Bidder)) or 0
    total_bids = db.scalar(select(func.count()).select_from(Bid)) or 0
    awarded = db.scalar(
        select(func.count()).select_from(Auction).where(Auction.state == AuctionState.awarded)
    ) or 0
    deserted = db.scalar(
        select(func.count()).select_from(Auction).where(Auction.state == AuctionState.deserted)
    ) or 0
    live = db.scalar(
        select(func.count()).select_from(Auction).where(
            Auction.state.in_([AuctionState.published, AuctionState.live])
        )
    ) or 0
    total_amount = db.scalar(
        select(func.coalesce(func.sum(Award.final_amount), 0)).select_from(Award)
    ) or 0
    avg_amount = db.scalar(
        select(func.coalesce(func.avg(Award.final_amount), 0)).select_from(Award)
    ) or 0
    pending_payments = db.scalar(
        select(func.count()).select_from(Award).where(
            Award.state.in_([AwardState.awarded, AwardState.payment_pending])
        )
    ) or 0
    conversion_rate = round(awarded / total_auctions * 100, 1) if total_auctions else 0.0

    return {
        'total_auctions': int(total_auctions),
        'live_auctions': int(live),
        'awarded_auctions': int(awarded),
        'deserted_auctions': int(deserted),
        'total_bidders': int(total_bidders),
        'total_bids': int(total_bids),
        'awarded_amount': float(total_amount),
        'avg_award_amount': float(avg_amount),
        'pending_payments': int(pending_payments),
        'conversion_rate': conversion_rate,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Configuración global (singleton) — Fase 8.1
# ─────────────────────────────────────────────────────────────────────────────

def get_config(db: Session) -> ConfiguracionSubastas:
    """Devuelve la configuración global del módulo (singleton id=1).

    Si no existe aún, la crea con valores por defecto.
    """
    cfg = db.get(ConfiguracionSubastas, 1)
    if not cfg:
        cfg = ConfiguracionSubastas(id=1)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


def update_config(db: Session, data: ConfiguracionUpdate) -> ConfiguracionSubastas:
    cfg = get_config(db)
    payload = data.model_dump(exclude_unset=True)
    for key, value in payload.items():
        setattr(cfg, key, value)
    cfg.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(cfg)
    return cfg


# ─────────────────────────────────────────────────────────────────────────────
# Expiración de adjudicaciones vencidas — Fase 8.5
# ─────────────────────────────────────────────────────────────────────────────

def expire_overdue_awards(db: Session) -> int:
    """Marca como expiradas las adjudicaciones cuyo due_at ya pasó.

    Solo actúa sobre adjudicaciones en estado 'awarded' o 'payment_pending'.
    Retorna el número de adjudicaciones expiradas.
    """
    now = datetime.utcnow()
    expirable_states = {AwardState.awarded, AwardState.payment_pending}
    stmt = select(Award).where(
        Award.state.in_(expirable_states),
        Award.due_at.is_not(None),
        Award.due_at < now,
    )
    awards = list(db.scalars(stmt).all())
    expired = 0
    for award in awards:
        try:
            award.state = AwardState.expired
            db.commit()
            _event(
                db, award.auction_id, 'award_expired',
                f'Adjudicación {award.id} expirada por vencimiento de pago (due_at: {award.due_at}).',
                actor='sistema',
            )
            db.commit()
            expired += 1
        except Exception:
            db.rollback()
    return expired
