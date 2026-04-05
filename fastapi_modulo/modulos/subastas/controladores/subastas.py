from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..modelos.db_models import AwardState, Base, BidderState, DeliveryState, PaymentState
from ..modelos.schemas import (
    AuctionCreate,
    AuctionDetail,
    AuctionOut,
    AuctionUpdate,
    AwardCreate,
    AwardOut,
    AwardUpdateState,
    BidCreate,
    BidOut,
    BidderCreate,
    BidderOut,
    BidderUpdate,
    ConfiguracionOut,
    ConfiguracionUpdate,
    DeliveryConfirm,
    DeliveryCreate,
    DeliveryOut,
    DeliveryUpdate,
    EventOut,
    LotCreate,
    LotOut,
    LotUpdate,
    PaginatedResponse,
    PaymentCreate,
    PaymentOut,
    RegistrationApprove,
    RegistrationCreate,
    RegistrationOut,
    SchedulerTickResult,
)
from ..modelos.store import (
    BusinessRuleError,
    approve_bidder,
    approve_registration,
    cancel_auction,
    cancel_delivery,
    close_auction,
    confirm_delivery,
    count_auctions,
    count_bidders,
    create_auction,
    create_award,
    create_bidder,
    create_delivery,
    create_lot,
    create_payment,
    delete_lot,
    get_auction,
    get_award,
    get_bid,
    get_bidder,
    get_config,
    get_dashboard_stats,
    get_delivery,
    get_lot,
    get_payment,
    list_auctions,
    list_awards,
    list_bidders,
    list_bids,
    list_deliveries,
    list_events,
    list_lots,
    list_payments,
    list_registrations,
    mark_delivery,
    place_bid,
    publish_auction,
    reassign_award,
    register_bidder,
    reject_registration,
    set_live,
    suspend_auction,
    update_auction,
    update_award_state,
    update_bidder,
    update_config,
    update_delivery,
    update_lot,
    update_payment_state,
)
from ..modelos.scheduler import run_all_ticks


BASE_DIR = Path(__file__).resolve().parents[1]
VIEWS_DIR = BASE_DIR / 'vistas'
DATABASE_URL = 'sqlite:///./subastas.sqlite3'

engine = create_engine(DATABASE_URL, future=True, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base.metadata.create_all(bind=engine)

router = APIRouter(prefix='/subastas', tags=['Subastas'])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _safe(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except BusinessRuleError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _or_404(obj, detail: str = 'Recurso no encontrado'):
    if obj is None:
        raise HTTPException(status_code=404, detail=detail)
    return obj


# ─────────────────────────────────────────────────────────────────────────────
# Vista HTML del dashboard
# ─────────────────────────────────────────────────────────────────────────────

@router.get('', response_class=HTMLResponse)
def subastas_dashboard(request: Request, db: Session = Depends(get_db)):
    html = (VIEWS_DIR / 'subastas.html').read_text(encoding='utf-8')
    stats = get_dashboard_stats(db)
    auctions = list_auctions(db, limit=25)
    rows = ''.join(
        f"<tr><td>{a.id}</td><td>{a.name}</td><td>{a.state}</td>"
        f"<td>{a.start_at or ''}</td><td>{a.end_at or ''}</td></tr>"
        for a in auctions
    ) or '<tr><td colspan="5">Sin registros</td></tr>'
    for key, value in stats.items():
        html = html.replace('{{ ' + key + ' }}', str(value))
    html = html.replace('{{ auctions_rows }}', rows)
    return HTMLResponse(html)


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard JSON
# ─────────────────────────────────────────────────────────────────────────────

@router.get('/api/dashboard')
def api_dashboard(db: Session = Depends(get_db)):
    return get_dashboard_stats(db)


# ─────────────────────────────────────────────────────────────────────────────
# Subastas
# ─────────────────────────────────────────────────────────────────────────────

@router.get('/api/auctions', response_model=PaginatedResponse[AuctionOut])
def api_list_auctions(
    state: str | None = None,
    business_id: int | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    db: Session = Depends(get_db),
):
    offset = (page - 1) * page_size
    items = list_auctions(db, state=state, business_id=business_id, limit=page_size, offset=offset)
    total = count_auctions(db, state=state, business_id=business_id)
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.post('/api/auctions', response_model=AuctionOut, status_code=201)
def api_create_auction(data: AuctionCreate, db: Session = Depends(get_db)):
    return _safe(create_auction, db, data)


@router.get('/api/auctions/{auction_id}', response_model=AuctionDetail)
def api_get_auction(auction_id: int, db: Session = Depends(get_db)):
    auction = _or_404(get_auction(db, auction_id), 'Subasta no encontrada')
    highest = max((b.amount for b in auction.bids if b.is_valid), default=0)
    bids_count = sum(1 for b in auction.bids if b.is_valid)
    return AuctionDetail.model_validate({
        **auction.__dict__,
        'lots': auction.lots,
        'highest_bid': highest,
        'bids_count': bids_count,
        'award': auction.award,
    })


@router.patch('/api/auctions/{auction_id}', response_model=AuctionOut)
def api_update_auction(auction_id: int, data: AuctionUpdate, db: Session = Depends(get_db)):
    return _safe(update_auction, db, auction_id, data)


@router.post('/api/auctions/{auction_id}/publish', response_model=AuctionOut)
def api_publish_auction(auction_id: int, actor: str | None = None, db: Session = Depends(get_db)):
    return _safe(publish_auction, db, auction_id, actor)


@router.post('/api/auctions/{auction_id}/live', response_model=AuctionOut)
def api_set_live(auction_id: int, actor: str | None = None, db: Session = Depends(get_db)):
    return _safe(set_live, db, auction_id, actor)


@router.post('/api/auctions/{auction_id}/suspend', response_model=AuctionOut)
def api_suspend_auction(
    auction_id: int,
    actor: str | None = None,
    reason: str | None = None,
    db: Session = Depends(get_db),
):
    return _safe(suspend_auction, db, auction_id, actor, reason)


@router.post('/api/auctions/{auction_id}/cancel', response_model=AuctionOut)
def api_cancel_auction(
    auction_id: int,
    actor: str | None = None,
    reason: str | None = None,
    db: Session = Depends(get_db),
):
    return _safe(cancel_auction, db, auction_id, actor, reason)


@router.post('/api/auctions/{auction_id}/close', response_model=AuctionOut)
def api_close_auction(auction_id: int, actor: str | None = None, db: Session = Depends(get_db)):
    return _safe(close_auction, db, auction_id, actor)


# ─────────────────────────────────────────────────────────────────────────────
# Lotes
# ─────────────────────────────────────────────────────────────────────────────

@router.post('/api/lots', response_model=LotOut, status_code=201)
def api_create_lot(data: LotCreate, db: Session = Depends(get_db)):
    return _safe(create_lot, db, data)


@router.get('/api/lots', response_model=list[LotOut])
def api_list_lots(auction_id: int, db: Session = Depends(get_db)):
    return list_lots(db, auction_id)


@router.get('/api/lots/{lot_id}', response_model=LotOut)
def api_get_lot(lot_id: int, db: Session = Depends(get_db)):
    return _or_404(get_lot(db, lot_id), 'Lote no encontrado')


@router.patch('/api/lots/{lot_id}', response_model=LotOut)
def api_update_lot(lot_id: int, data: LotUpdate, db: Session = Depends(get_db)):
    return _safe(update_lot, db, lot_id, data)


@router.delete('/api/lots/{lot_id}', status_code=204)
def api_delete_lot(lot_id: int, db: Session = Depends(get_db)):
    _safe(delete_lot, db, lot_id)


# ─────────────────────────────────────────────────────────────────────────────
# Postores
# ─────────────────────────────────────────────────────────────────────────────

@router.post('/api/bidders', response_model=BidderOut, status_code=201)
def api_create_bidder(data: BidderCreate, db: Session = Depends(get_db)):
    return _safe(create_bidder, db, data)


@router.get('/api/bidders', response_model=PaginatedResponse[BidderOut])
def api_list_bidders(
    state: BidderState | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    db: Session = Depends(get_db),
):
    offset = (page - 1) * page_size
    items = list_bidders(db, state=state, limit=page_size, offset=offset)
    total = count_bidders(db, state=state)
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get('/api/bidders/{bidder_id}', response_model=BidderOut)
def api_get_bidder(bidder_id: int, db: Session = Depends(get_db)):
    return _or_404(get_bidder(db, bidder_id), 'Postor no encontrado')


@router.patch('/api/bidders/{bidder_id}', response_model=BidderOut)
def api_update_bidder(bidder_id: int, data: BidderUpdate, db: Session = Depends(get_db)):
    return _safe(update_bidder, db, bidder_id, data)


@router.post('/api/bidders/{bidder_id}/approve', response_model=BidderOut)
def api_approve_bidder(bidder_id: int, actor: str | None = None, db: Session = Depends(get_db)):
    return _safe(approve_bidder, db, bidder_id, actor)


# ─────────────────────────────────────────────────────────────────────────────
# Registros de participación
# ─────────────────────────────────────────────────────────────────────────────

@router.post('/api/registrations', response_model=RegistrationOut, status_code=201)
def api_register_bidder(data: RegistrationCreate, db: Session = Depends(get_db)):
    return _safe(register_bidder, db, data)


@router.get('/api/registrations', response_model=list[RegistrationOut])
def api_list_registrations(auction_id: int, db: Session = Depends(get_db)):
    return list_registrations(db, auction_id)


@router.post('/api/registrations/{registration_id}/approve', response_model=RegistrationOut)
def api_approve_registration(registration_id: int, data: RegistrationApprove, db: Session = Depends(get_db)):
    return _safe(approve_registration, db, registration_id, data)


@router.post('/api/registrations/{registration_id}/reject', response_model=RegistrationOut)
def api_reject_registration(
    registration_id: int,
    actor: str | None = None,
    db: Session = Depends(get_db),
):
    return _safe(reject_registration, db, registration_id, actor)


# ─────────────────────────────────────────────────────────────────────────────
# Pujas
# ─────────────────────────────────────────────────────────────────────────────

@router.post('/api/bids', response_model=BidOut, status_code=201)
def api_place_bid(data: BidCreate, db: Session = Depends(get_db)):
    return _safe(place_bid, db, data)


@router.get('/api/auctions/{auction_id}/bids', response_model=list[BidOut])
def api_list_bids(
    auction_id: int,
    valid_only: bool = True,
    db: Session = Depends(get_db),
):
    return list_bids(db, auction_id, valid_only=valid_only)


@router.get('/api/bids/{bid_id}', response_model=BidOut)
def api_get_bid(bid_id: int, db: Session = Depends(get_db)):
    return _or_404(get_bid(db, bid_id), 'Puja no encontrada')


# ─────────────────────────────────────────────────────────────────────────────
# Adjudicaciones
# ─────────────────────────────────────────────────────────────────────────────

@router.post('/api/awards', response_model=AwardOut, status_code=201)
def api_create_award(data: AwardCreate, db: Session = Depends(get_db)):
    return _safe(create_award, db, data)


@router.get('/api/awards', response_model=list[AwardOut])
def api_list_awards(
    state: AwardState | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return list_awards(db, state=state, limit=limit)


@router.get('/api/awards/{award_id}', response_model=AwardOut)
def api_get_award(award_id: int, db: Session = Depends(get_db)):
    return _or_404(get_award(db, award_id), 'Adjudicación no encontrada')


@router.patch('/api/awards/{award_id}', response_model=AwardOut)
def api_update_award(award_id: int, data: AwardUpdateState, db: Session = Depends(get_db)):
    return _safe(update_award_state, db, award_id, data)


@router.post('/api/awards/{award_id}/reassign', response_model=AwardOut)
def api_reassign_award(
    award_id: int,
    new_bidder_id: int,
    actor: str | None = None,
    db: Session = Depends(get_db),
):
    return _safe(reassign_award, db, award_id, new_bidder_id, actor)


@router.post('/api/awards/{award_id}/deliver', response_model=AwardOut)
def api_mark_delivery(
    award_id: int,
    actor: str | None = None,
    notes: str | None = None,
    db: Session = Depends(get_db),
):
    return _safe(mark_delivery, db, award_id, actor, notes)


# ─────────────────────────────────────────────────────────────────────────────
# Pagos
# ─────────────────────────────────────────────────────────────────────────────

@router.post('/api/payments', response_model=PaymentOut, status_code=201)
def api_create_payment(data: PaymentCreate, db: Session = Depends(get_db)):
    return _safe(create_payment, db, data)


@router.get('/api/payments', response_model=list[PaymentOut])
def api_list_payments(award_id: int, db: Session = Depends(get_db)):
    return list_payments(db, award_id)


@router.get('/api/payments/{payment_id}', response_model=PaymentOut)
def api_get_payment(payment_id: int, db: Session = Depends(get_db)):
    return _or_404(get_payment(db, payment_id), 'Pago no encontrado')


@router.patch('/api/payments/{payment_id}/state', response_model=PaymentOut)
def api_update_payment_state(
    payment_id: int,
    state: PaymentState,
    actor: str | None = None,
    db: Session = Depends(get_db),
):
    return _safe(update_payment_state, db, payment_id, state, actor)


# ─────────────────────────────────────────────────────────────────────────────
# Entregas
# ─────────────────────────────────────────────────────────────────────────────

@router.post('/api/deliveries', response_model=DeliveryOut, status_code=201)
def api_create_delivery(data: DeliveryCreate, db: Session = Depends(get_db)):
    return _safe(create_delivery, db, data)


@router.get('/api/deliveries', response_model=list[DeliveryOut])
def api_list_deliveries(
    award_id: int | None = None,
    state: DeliveryState | None = None,
    external_order_ref: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return list_deliveries(db, award_id=award_id, state=state, external_order_ref=external_order_ref, limit=limit)


@router.get('/api/deliveries/{delivery_id}', response_model=DeliveryOut)
def api_get_delivery(delivery_id: int, db: Session = Depends(get_db)):
    return _or_404(get_delivery(db, delivery_id), 'Entrega no encontrada')


@router.patch('/api/deliveries/{delivery_id}', response_model=DeliveryOut)
def api_update_delivery(delivery_id: int, data: DeliveryUpdate, db: Session = Depends(get_db)):
    return _safe(update_delivery, db, delivery_id, data)


@router.post('/api/deliveries/{delivery_id}/confirm', response_model=DeliveryOut)
def api_confirm_delivery(
    delivery_id: int,
    data: DeliveryConfirm,
    actor: str | None = None,
    db: Session = Depends(get_db),
):
    return _safe(confirm_delivery, db, delivery_id, data, actor)


@router.post('/api/deliveries/{delivery_id}/cancel', response_model=DeliveryOut)
def api_cancel_delivery(
    delivery_id: int,
    actor: str | None = None,
    reason: str | None = None,
    db: Session = Depends(get_db),
):
    return _safe(cancel_delivery, db, delivery_id, actor, reason)


# ─────────────────────────────────────────────────────────────────────────────
# Auditoría / Bitácora
# ─────────────────────────────────────────────────────────────────────────────

@router.get('/api/auctions/{auction_id}/events', response_model=list[EventOut])
def api_list_events(
    auction_id: int,
    event_type: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return list_events(db, auction_id, event_type=event_type, limit=limit)


# ─────────────────────────────────────────────────────────────────────────────
# Configuración global — Fase 8.1
# ─────────────────────────────────────────────────────────────────────────────

@router.get('/api/config', response_model=ConfiguracionOut)
def api_get_config(db: Session = Depends(get_db)):
    """Devuelve la configuración global del módulo (singleton)."""
    return get_config(db)


@router.patch('/api/config', response_model=ConfiguracionOut)
def api_update_config(data: ConfiguracionUpdate, db: Session = Depends(get_db)):
    """Actualiza parcialmente la configuración global del módulo."""
    return _safe(update_config, db, data)


# ─────────────────────────────────────────────────────────────────────────────
# Scheduler manual — Fase 8.2 / 8.3 / 8.5
# ─────────────────────────────────────────────────────────────────────────────

@router.post('/api/scheduler/tick', response_model=SchedulerTickResult)
def api_scheduler_tick(db: Session = Depends(get_db)):
    """Ejecuta manualmente un tick del scheduler.

    Útil para testing, operación manual urgente o entornos sin scheduler
    en background activo. Retorna el conteo de registros afectados.
    """
    return run_all_ticks(db)

