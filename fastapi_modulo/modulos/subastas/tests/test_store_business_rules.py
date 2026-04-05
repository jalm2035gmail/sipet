"""
7.1 — Pruebas de reglas de negocio del store.

Cubre: validaciones de puja, precio de reserva, auto-extensión,
duplicados, pagos parciales/totales.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from fastapi_modulo.modulos.subastas.modelos.db_models import AwardState, BidderState
from fastapi_modulo.modulos.subastas.modelos.schemas import (
    AwardUpdateState,
    BidCreate,
    LotCreate,
    PaymentCreate,
    RegistrationCreate,
)
from fastapi_modulo.modulos.subastas.modelos.store import (
    BusinessRuleError,
    approve_bidder,
    close_auction,
    create_lot,
    create_payment,
    place_bid,
    register_bidder,
    update_award_state,
)
from .conftest import authorize, bid, make_auction, make_bidder, make_lot


# ── Pujas: monto mínimo ──────────────────────────────────────────────────────

def test_primera_puja_debe_igualar_o_superar_base(db):
    auction = make_auction(db)
    make_lot(db, auction.id, base_price=Decimal("200.00"))
    bidder = make_bidder(db)
    authorize(db, auction.id, bidder.id)

    with pytest.raises(BusinessRuleError, match="mínima requerida"):
        bid(db, auction.id, bidder.id, "100.00")  # menor que base 200


def test_primera_puja_exactamente_en_base_es_valida(db):
    auction = make_auction(db)
    make_lot(db, auction.id, base_price=Decimal("100.00"))
    bidder = make_bidder(db)
    authorize(db, auction.id, bidder.id)

    result = bid(db, auction.id, bidder.id, "100.00")
    assert result.id is not None
    assert result.amount == Decimal("100.00")


def test_puja_sin_incremento_suficiente_rechazada(db):
    auction = make_auction(db, min_increment=Decimal("50.00"))
    make_lot(db, auction.id, base_price=Decimal("100.00"))
    bidder  = make_bidder(db, email="b1@t.com")
    bidder2 = make_bidder(db, email="b2@t.com")
    authorize(db, auction.id, bidder.id)
    authorize(db, auction.id, bidder2.id)

    bid(db, auction.id, bidder.id, "100.00")  # primera puja

    with pytest.raises(BusinessRuleError, match="mínima requerida"):
        bid(db, auction.id, bidder2.id, "120.00")  # 100 + 50 = 150 mínimo


def test_puja_con_incremento_exacto_es_valida(db):
    auction = make_auction(db, min_increment=Decimal("50.00"))
    make_lot(db, auction.id, base_price=Decimal("0.00"))
    bidder  = make_bidder(db, email="b1@t.com")
    bidder2 = make_bidder(db, email="b2@t.com")
    authorize(db, auction.id, bidder.id)
    authorize(db, auction.id, bidder2.id)

    bid(db, auction.id, bidder.id, "100.00")
    result = bid(db, auction.id, bidder2.id, "150.00")  # 100 + 50 exacto
    assert result.amount == Decimal("150.00")


# ── Pujas: ventana de tiempo ─────────────────────────────────────────────────

def test_puja_antes_del_inicio_rechazada(db):
    future = datetime.utcnow() + timedelta(hours=2)
    auction = make_auction(db, start_at=future, end_at=future + timedelta(hours=4))
    make_lot(db, auction.id)
    bidder = make_bidder(db)
    authorize(db, auction.id, bidder.id)

    with pytest.raises(BusinessRuleError, match="aún no inicia"):
        bid(db, auction.id, bidder.id, "50.00")


def test_puja_despues_del_cierre_rechazada(db):
    past = datetime.utcnow() - timedelta(hours=2)
    auction = make_auction(db, start_at=past - timedelta(hours=4), end_at=past)
    make_lot(db, auction.id)
    bidder = make_bidder(db)
    authorize(db, auction.id, bidder.id)

    with pytest.raises(BusinessRuleError, match="ya terminó"):
        bid(db, auction.id, bidder.id, "50.00")


# ── Pujas: estado de la subasta ──────────────────────────────────────────────

def test_puja_en_subasta_cancelada_rechazada(db):
    from fastapi_modulo.modulos.subastas.modelos.db_models import AuctionState
    auction = make_auction(db, state=AuctionState.cancelled)
    make_lot(db, auction.id)
    bidder = make_bidder(db)
    # Registrar directamente (la subasta está cancelada pero probamos la regla de estado)
    from fastapi_modulo.modulos.subastas.modelos.db_models import AuctionRegistration
    reg = AuctionRegistration(auction_id=auction.id, bidder_id=bidder.id, is_authorized=True)
    db.add(reg)
    db.commit()

    with pytest.raises(BusinessRuleError, match="no admite pujas"):
        bid(db, auction.id, bidder.id, "50.00")


def test_puja_en_subasta_draft_rechazada(db):
    from fastapi_modulo.modulos.subastas.modelos.db_models import AuctionState, AuctionRegistration
    auction = make_auction(db, state=AuctionState.draft)
    make_lot(db, auction.id)
    bidder = make_bidder(db)
    reg = AuctionRegistration(auction_id=auction.id, bidder_id=bidder.id, is_authorized=True)
    db.add(reg)
    db.commit()

    with pytest.raises(BusinessRuleError, match="no admite pujas"):
        bid(db, auction.id, bidder.id, "50.00")


# ── Pujas: elegibilidad del postor ───────────────────────────────────────────

def test_postor_sin_registro_no_puede_pujar(db):
    auction = make_auction(db)
    make_lot(db, auction.id)
    bidder = make_bidder(db)
    # NO se llama authorize()

    with pytest.raises(BusinessRuleError, match="autorizado"):
        bid(db, auction.id, bidder.id, "50.00")


def test_postor_registrado_no_autorizado_no_puede_pujar(db):
    auction = make_auction(db)
    make_lot(db, auction.id)
    bidder = make_bidder(db)
    register_bidder(db, RegistrationCreate(
        auction_id=auction.id, bidder_id=bidder.id, is_authorized=False
    ))

    with pytest.raises(BusinessRuleError, match="autorizado"):
        bid(db, auction.id, bidder.id, "50.00")


def test_postor_inactivo_no_puede_pujar(db):
    auction = make_auction(db)
    make_lot(db, auction.id)
    bidder = make_bidder(db)
    bidder.is_active = False
    db.commit()
    authorize(db, auction.id, bidder.id)

    with pytest.raises(BusinessRuleError, match="habilitado"):
        bid(db, auction.id, bidder.id, "50.00")


# ── Auto-extensión ───────────────────────────────────────────────────────────

def test_auto_extension_en_puja_tardia(db):
    ext_secs = 120
    end = datetime.utcnow() + timedelta(seconds=60)  # cierra en 60s
    auction = make_auction(
        db,
        start_at=datetime.utcnow() - timedelta(hours=1),
        end_at=end,
        auto_extend_seconds=ext_secs,
    )
    make_lot(db, auction.id, base_price=Decimal("0.00"))
    bidder = make_bidder(db)
    authorize(db, auction.id, bidder.id)

    original_end = auction.end_at
    bid(db, auction.id, bidder.id, "10.00")
    db.refresh(auction)

    assert auction.end_at > original_end, "El cierre debió extenderse"
    diff = (auction.end_at - original_end).total_seconds()
    assert abs(diff - ext_secs) < 2, f"Extensión esperada ~{ext_secs}s, obtenida {diff}s"


def test_sin_auto_extension_end_no_cambia(db):
    end = datetime.utcnow() + timedelta(seconds=60)
    auction = make_auction(
        db,
        start_at=datetime.utcnow() - timedelta(hours=1),
        end_at=end,
        auto_extend_seconds=0,
    )
    make_lot(db, auction.id, base_price=Decimal("0.00"))
    bidder = make_bidder(db)
    authorize(db, auction.id, bidder.id)

    bid(db, auction.id, bidder.id, "10.00")
    db.refresh(auction)

    assert abs((auction.end_at - end).total_seconds()) < 1, "end_at no debió cambiar"


# ── Duplicados ───────────────────────────────────────────────────────────────

def test_codigo_lote_duplicado_rechazado(db):
    auction = make_auction(db)
    make_lot(db, auction.id, code="L1")

    with pytest.raises(BusinessRuleError, match="duplicado"):
        make_lot(db, auction.id, code="L1")


def test_registro_duplicado_rechazado(db):
    auction = make_auction(db)
    bidder  = make_bidder(db)
    authorize(db, auction.id, bidder.id)

    with pytest.raises(BusinessRuleError, match="ya está registrado"):
        authorize(db, auction.id, bidder.id)


# ── Precio de reserva ────────────────────────────────────────────────────────

def test_precio_reserva_exactamente_alcanzado_adjudica(db):
    auction = make_auction(db, reserve_price=Decimal("100.00"))
    make_lot(db, auction.id, base_price=Decimal("0.00"))
    bidder = make_bidder(db)
    authorize(db, auction.id, bidder.id)

    bid(db, auction.id, bidder.id, "100.00")
    result = close_auction(db, auction.id)

    assert result.state.value == "awarded"


def test_precio_reserva_un_peso_abajo_deja_desierta(db):
    auction = make_auction(db, reserve_price=Decimal("100.00"), min_increment=Decimal("1.00"))
    make_lot(db, auction.id, base_price=Decimal("0.00"))
    bidder = make_bidder(db)
    authorize(db, auction.id, bidder.id)

    bid(db, auction.id, bidder.id, "99.00")
    result = close_auction(db, auction.id)

    assert result.state.value == "deserted"
    assert result.award is None


# ── Pagos ────────────────────────────────────────────────────────────────────

def test_pago_parcial_marca_award_payment_pending(db):
    auction = make_auction(db)
    make_lot(db, auction.id, base_price=Decimal("0.00"))
    bidder = make_bidder(db)
    authorize(db, auction.id, bidder.id)
    bid(db, auction.id, bidder.id, "200.00")
    closed = close_auction(db, auction.id)

    create_payment(db, PaymentCreate(
        award_id=closed.award.id, amount=Decimal("100.00"), state="partial"
    ))
    db.refresh(closed.award)

    assert closed.award.state == AwardState.payment_pending


def test_pago_completo_marca_award_paid(db):
    auction = make_auction(db)
    make_lot(db, auction.id, base_price=Decimal("0.00"))
    bidder = make_bidder(db)
    authorize(db, auction.id, bidder.id)
    bid(db, auction.id, bidder.id, "200.00")
    closed = close_auction(db, auction.id)

    create_payment(db, PaymentCreate(
        award_id=closed.award.id, amount=Decimal("200.00"), state="paid"
    ))
    db.refresh(closed.award)

    assert closed.award.state == AwardState.paid


def test_dos_pagos_parciales_suman_y_marcan_paid(db):
    auction = make_auction(db)
    make_lot(db, auction.id, base_price=Decimal("0.00"))
    bidder = make_bidder(db)
    authorize(db, auction.id, bidder.id)
    bid(db, auction.id, bidder.id, "300.00")
    closed = close_auction(db, auction.id)

    create_payment(db, PaymentCreate(award_id=closed.award.id, amount=Decimal("150.00"), state="partial"))
    create_payment(db, PaymentCreate(award_id=closed.award.id, amount=Decimal("150.00"), state="partial"))
    db.refresh(closed.award)

    assert closed.award.state == AwardState.paid


def test_pago_fallido_no_avanza_estado_award(db):
    auction = make_auction(db)
    make_lot(db, auction.id, base_price=Decimal("0.00"))
    bidder = make_bidder(db)
    authorize(db, auction.id, bidder.id)
    bid(db, auction.id, bidder.id, "100.00")
    closed = close_auction(db, auction.id)

    create_payment(db, PaymentCreate(
        award_id=closed.award.id, amount=Decimal("100.00"), state="failed"
    ))
    db.refresh(closed.award)

    # failed no se suma → sigue en awarded
    assert closed.award.state == AwardState.awarded


# ── Lote: solo se crea en subasta existente ──────────────────────────────────

def test_lote_en_subasta_inexistente_rechazado(db):
    with pytest.raises(BusinessRuleError, match="no existe"):
        make_lot(db, auction_id=9999)


# ── Postor: email único ──────────────────────────────────────────────────────

def test_email_postor_duplicado_rechazado(db):
    from fastapi_modulo.modulos.subastas.modelos.schemas import BidderCreate
    from fastapi_modulo.modulos.subastas.modelos.store import create_bidder
    create_bidder(db, BidderCreate(full_name="A", email="mismo@test.com"))
    with pytest.raises(BusinessRuleError, match="email"):
        create_bidder(db, BidderCreate(full_name="B", email="mismo@test.com"))
