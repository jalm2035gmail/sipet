"""
7.3 — Pruebas de transiciones de estado.

Cubre: publicar, iniciar, suspender, cancelar, cerrar,
reasignar adjudicación, ciclo completo de entrega.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from fastapi_modulo.modulos.subastas.modelos.db_models import (
    AuctionState,
    AwardState,
    DeliveryState,
)
from fastapi_modulo.modulos.subastas.modelos.schemas import (
    AwardUpdateState,
    DeliveryConfirm,
    DeliveryCreate,
    PaymentCreate,
)
from fastapi_modulo.modulos.subastas.modelos.store import (
    BusinessRuleError,
    cancel_auction,
    cancel_delivery,
    close_auction,
    confirm_delivery,
    create_delivery,
    create_payment,
    get_delivery,
    publish_auction,
    reassign_award,
    set_live,
    suspend_auction,
    update_award_state,
)
from .conftest import authorize, bid, make_auction, make_bidder, make_lot


# ── publish_auction ──────────────────────────────────────────────────────────

def test_publicar_desde_borrador(db):
    auction = make_auction(db, state=AuctionState.draft)
    result  = publish_auction(db, auction.id, actor="admin")
    assert result.state == AuctionState.published


def test_publicar_desde_programada(db):
    auction = make_auction(db, state=AuctionState.scheduled)
    result  = publish_auction(db, auction.id)
    assert result.state == AuctionState.published


def test_no_publicar_desde_live(db):
    auction = make_auction(db, state=AuctionState.live)
    with pytest.raises(BusinessRuleError, match="No se puede publicar"):
        publish_auction(db, auction.id)


def test_no_publicar_desde_cancelled(db):
    auction = make_auction(db, state=AuctionState.cancelled)
    with pytest.raises(BusinessRuleError, match="No se puede publicar"):
        publish_auction(db, auction.id)


# ── set_live ─────────────────────────────────────────────────────────────────

def test_iniciar_desde_published(db):
    auction = make_auction(db, state=AuctionState.published)
    result  = set_live(db, auction.id)
    assert result.state == AuctionState.live


def test_no_iniciar_desde_draft(db):
    auction = make_auction(db, state=AuctionState.draft)
    with pytest.raises(BusinessRuleError, match="Solo una subasta publicada"):
        set_live(db, auction.id)


# ── suspend_auction ──────────────────────────────────────────────────────────

def test_suspender_desde_published(db):
    auction = make_auction(db, state=AuctionState.published)
    result  = suspend_auction(db, auction.id, reason="Revisión interna")
    assert result.state == AuctionState.suspended


def test_suspender_desde_live(db):
    auction = make_auction(db, state=AuctionState.live)
    result  = suspend_auction(db, auction.id)
    assert result.state == AuctionState.suspended


def test_no_suspender_desde_draft(db):
    auction = make_auction(db, state=AuctionState.draft)
    with pytest.raises(BusinessRuleError, match="No se puede suspender"):
        suspend_auction(db, auction.id)


def test_no_suspender_desde_awarded(db):
    auction = make_auction(db, state=AuctionState.awarded)
    with pytest.raises(BusinessRuleError, match="No se puede suspender"):
        suspend_auction(db, auction.id)


# ── cancel_auction ───────────────────────────────────────────────────────────

def test_cancelar_desde_published(db):
    auction = make_auction(db, state=AuctionState.published)
    result  = cancel_auction(db, auction.id, actor="admin", reason="Error en catálogo")
    assert result.state == AuctionState.cancelled


def test_cancelar_desde_suspended(db):
    auction = make_auction(db, state=AuctionState.suspended)
    result  = cancel_auction(db, auction.id)
    assert result.state == AuctionState.cancelled


def test_no_cancelar_desde_awarded(db):
    auction = make_auction(db, state=AuctionState.awarded)
    with pytest.raises(BusinessRuleError, match="No se puede cancelar"):
        cancel_auction(db, auction.id)


def test_no_pujar_en_subasta_cancelada(db):
    auction = make_auction(db, state=AuctionState.published)
    make_lot(db, auction.id)
    bidder = make_bidder(db)
    authorize(db, auction.id, bidder.id)
    cancel_auction(db, auction.id)

    with pytest.raises(BusinessRuleError, match="no admite pujas"):
        bid(db, auction.id, bidder.id, "50.00")


# ── close y adjudicación automática ─────────────────────────────────────────

def test_cerrar_con_pujas_adjudica_mayor(db):
    auction = make_auction(db, min_increment=Decimal("10.00"))
    make_lot(db, auction.id, base_price=Decimal("0.00"))
    b1 = make_bidder(db, email="a@t.com")
    b2 = make_bidder(db, email="b@t.com")
    authorize(db, auction.id, b1.id)
    authorize(db, auction.id, b2.id)

    bid(db, auction.id, b1.id, "100.00")
    bid(db, auction.id, b2.id, "150.00")
    bid(db, auction.id, b1.id, "200.00")

    result = close_auction(db, auction.id)
    assert result.state == AuctionState.awarded
    assert result.award.final_amount == Decimal("200.00")
    assert result.award.bidder_id == b1.id


# ── reassign_award ───────────────────────────────────────────────────────────

def test_reasignar_adjudicacion_expirada(db):
    auction = make_auction(db)
    make_lot(db, auction.id, base_price=Decimal("0.00"))
    b1 = make_bidder(db, email="g1@t.com")
    b2 = make_bidder(db, email="g2@t.com")
    authorize(db, auction.id, b1.id)
    authorize(db, auction.id, b2.id)
    bid(db, auction.id, b1.id, "100.00")
    closed = close_auction(db, auction.id)

    # Marcar como vencida
    update_award_state(db, closed.award.id, AwardUpdateState(state=AwardState.expired))

    result = reassign_award(db, closed.award.id, b2.id, actor="admin")
    assert result.state == AwardState.reassigned
    assert result.bidder_id == b2.id


def test_no_reasignar_adjudicacion_pagada(db):
    auction = make_auction(db)
    make_lot(db, auction.id, base_price=Decimal("0.00"))
    bidder = make_bidder(db)
    b2     = make_bidder(db, email="otro@t.com")
    authorize(db, auction.id, bidder.id)
    bid(db, auction.id, bidder.id, "100.00")
    closed = close_auction(db, auction.id)

    create_payment(db, PaymentCreate(award_id=closed.award.id, amount=Decimal("100.00"), state="paid"))

    with pytest.raises(BusinessRuleError, match="No se puede reasignar"):
        reassign_award(db, closed.award.id, b2.id)


# ── Ciclo de entrega (Delivery) ───────────────────────────────────────────────

def _setup_paid_award(db):
    """Helper: crea subasta cerrada y adjudicación pagada."""
    auction = make_auction(db)
    make_lot(db, auction.id, base_price=Decimal("0.00"))
    bidder = make_bidder(db)
    authorize(db, auction.id, bidder.id)
    bid(db, auction.id, bidder.id, "500.00")
    closed = close_auction(db, auction.id)
    create_payment(db, PaymentCreate(
        award_id=closed.award.id, amount=Decimal("500.00"), state="paid"
    ))
    db.refresh(closed.award)
    return closed.award


def test_crear_entrega_solo_para_adjudicacion_pagada(db):
    award = _setup_paid_award(db)
    delivery = create_delivery(db, DeliveryCreate(
        award_id=award.id,
        delivery_address="Av. Principal 100",
        created_by="operador",
    ))
    assert delivery.id is not None
    assert delivery.state == DeliveryState.pending


def test_crear_entrega_programada_cuando_hay_fecha(db):
    from datetime import datetime, timedelta
    award    = _setup_paid_award(db)
    scheduled = datetime.utcnow() + timedelta(days=3)
    delivery = create_delivery(db, DeliveryCreate(
        award_id=award.id, scheduled_at=scheduled
    ))
    assert delivery.state == DeliveryState.scheduled


def test_no_crear_entrega_si_award_no_esta_pagada(db):
    auction = make_auction(db)
    make_lot(db, auction.id, base_price=Decimal("0.00"))
    bidder = make_bidder(db)
    authorize(db, auction.id, bidder.id)
    bid(db, auction.id, bidder.id, "100.00")
    closed = close_auction(db, auction.id)
    # No se paga

    with pytest.raises(BusinessRuleError, match="pagadas"):
        create_delivery(db, DeliveryCreate(award_id=closed.award.id))


def test_confirmar_entrega(db):
    award    = _setup_paid_award(db)
    delivery = create_delivery(db, DeliveryCreate(award_id=award.id))

    confirmed = confirm_delivery(db, delivery.id, DeliveryConfirm(
        received_by="Juan García",
        evidence_url="https://ejemplo.com/evidencia.jpg",
    ), actor="almacen")

    assert confirmed.state == DeliveryState.delivered
    assert confirmed.received_by == "Juan García"
    assert confirmed.delivered_at is not None


def test_no_confirmar_entrega_dos_veces(db):
    award    = _setup_paid_award(db)
    delivery = create_delivery(db, DeliveryCreate(award_id=award.id))
    confirm_delivery(db, delivery.id, DeliveryConfirm(received_by="A"))

    with pytest.raises(BusinessRuleError, match="ya fue confirmada"):
        confirm_delivery(db, delivery.id, DeliveryConfirm(received_by="B"))


def test_cancelar_entrega_pendiente(db):
    award    = _setup_paid_award(db)
    delivery = create_delivery(db, DeliveryCreate(award_id=award.id))
    result   = cancel_delivery(db, delivery.id, reason="Dirección incorrecta")
    assert result.state == DeliveryState.cancelled


def test_no_cancelar_entrega_confirmada(db):
    award    = _setup_paid_award(db)
    delivery = create_delivery(db, DeliveryCreate(award_id=award.id))
    confirm_delivery(db, delivery.id, DeliveryConfirm(received_by="A"))

    with pytest.raises(BusinessRuleError, match="ya confirmada"):
        cancel_delivery(db, delivery.id)


def test_external_order_ref_almacena_referencia_multitienda(db):
    """El campo external_order_ref vincula con multitienda sin FK directa."""
    award    = _setup_paid_award(db)
    ref      = "ORD-MT-2026-00123"   # simula order_number de multitienda
    delivery = create_delivery(db, DeliveryCreate(
        award_id=award.id,
        external_order_ref=ref,
    ))
    db.refresh(delivery)
    assert delivery.external_order_ref == ref


def test_ciclo_completo_subasta_puja_pago_entrega(db):
    """Flujo end-to-end: subasta → puja → cierre → pago → entrega → confirmación."""
    # 1. Crear y publicar
    auction = make_auction(db, state=AuctionState.published)
    make_lot(db, auction.id, base_price=Decimal("500.00"))
    bidder = make_bidder(db)
    authorize(db, auction.id, bidder.id)

    # 2. Pujar
    bid(db, auction.id, bidder.id, "500.00")
    bid(db, auction.id, bidder.id, "600.00")

    # 3. Cerrar
    closed = close_auction(db, auction.id)
    assert closed.state == AuctionState.awarded
    assert closed.award.final_amount == Decimal("600.00")

    # 4. Pagar
    create_payment(db, PaymentCreate(
        award_id=closed.award.id, amount=Decimal("600.00"), state="paid"
    ))
    db.refresh(closed.award)
    assert closed.award.state == AwardState.paid

    # 5. Crear entrega
    delivery = create_delivery(db, DeliveryCreate(
        award_id=closed.award.id,
        delivery_address="Bodega Central",
        created_by="logistica",
    ))
    assert delivery.state == DeliveryState.pending

    # 6. Confirmar entrega
    confirmed = confirm_delivery(db, delivery.id, DeliveryConfirm(
        received_by=bidder.full_name,
        evidence_url="https://evidencia.test/foto.png",
    ))
    assert confirmed.state == DeliveryState.delivered

    # 7. Bitácora: verificar eventos registrados
    from fastapi_modulo.modulos.subastas.modelos.store import list_events
    events = list_events(db, auction.id)
    event_types = {e.event_type for e in events}
    assert "auction_created"   in event_types
    assert "bid_placed"        in event_types
    assert "auction_awarded"   in event_types
    assert "payment_created"   in event_types
    assert "delivery_created"  in event_types
    assert "delivery_confirmed" in event_types
