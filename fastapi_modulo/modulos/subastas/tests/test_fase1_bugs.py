"""
Pruebas de regresión para los 5 bugs corregidos en Fase 1.

BUG-1: timedelta importado al inicio (no es testeable en runtime, se valida con inspect)
BUG-2: close_auction() respeta reserve_price
BUG-3: place_bid() usa SELECT FOR UPDATE
BUG-4: Award tiene ORM relationship a Bidder
BUG-5: Payment tiene ORM relationship a Award
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi_modulo.modulos.subastas.modelos.db_models import (
    AuctionState,
    AwardState,
    Base,
    BidderState,
)
from fastapi_modulo.modulos.subastas.modelos.schemas import (
    AuctionCreate,
    BidCreate,
    BidderCreate,
    LotCreate,
    PaymentCreate,
    RegistrationCreate,
)
from fastapi_modulo.modulos.subastas.modelos.store import (
    BusinessRuleError,
    close_auction,
    create_auction,
    create_bidder,
    create_lot,
    create_payment,
    place_bid,
    register_bidder,
)


@pytest.fixture
def db():
    engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


def _make_auction(db, reserve_price=None, min_increment=Decimal('10.00')):
    data = AuctionCreate(
        name='Subasta test',
        start_at=datetime(2000, 1, 1),
        end_at=datetime(2099, 12, 31),
        min_increment=min_increment,
        reserve_price=reserve_price,
    )
    auction = create_auction(db, data)
    auction.state = AuctionState.published
    db.commit()
    db.refresh(auction)
    return auction


def _make_bidder_and_register(db, auction_id, email='test@test.com'):
    bidder = create_bidder(db, BidderCreate(full_name='Postor Test', email=email))
    bidder.state = BidderState.approved
    db.commit()
    db.refresh(bidder)
    reg = register_bidder(db, RegistrationCreate(
        auction_id=auction_id,
        bidder_id=bidder.id,
        is_authorized=True,
        approved_by='admin',
    ))
    return bidder, reg


# ─── BUG-1 ────────────────────────────────────────────────────────────────────

def test_bug1_timedelta_importado_al_inicio():
    """timedelta debe estar importado antes de la definición de place_bid."""
    import inspect
    from fastapi_modulo.modulos.subastas.modelos import store
    source = inspect.getsource(store)
    timedelta_pos = source.index('from datetime import datetime, timedelta')
    place_bid_pos = source.index('def place_bid')
    assert timedelta_pos < place_bid_pos, 'timedelta debe importarse antes de place_bid'


# ─── BUG-2 ────────────────────────────────────────────────────────────────────

def test_bug2_reserve_no_alcanzada_resulta_desierta(db):
    """Puja presente pero menor al precio de reserva → estado deserted."""
    auction = _make_auction(db, reserve_price=Decimal('500.00'))
    create_lot(db, LotCreate(auction_id=auction.id, code='L1', name='Lote 1', base_price=Decimal('100.00')))
    bidder, _ = _make_bidder_and_register(db, auction.id)

    place_bid(db, BidCreate(auction_id=auction.id, bidder_id=bidder.id, amount=Decimal('200.00')))

    result = close_auction(db, auction.id, actor='admin')
    assert result.state == AuctionState.deserted
    assert result.award is None


def test_bug2_reserve_alcanzada_resulta_adjudicada(db):
    """Puja igual o mayor al precio de reserva → estado awarded."""
    auction = _make_auction(db, reserve_price=Decimal('150.00'))
    create_lot(db, LotCreate(auction_id=auction.id, code='L1', name='Lote 1', base_price=Decimal('100.00')))
    bidder, _ = _make_bidder_and_register(db, auction.id)

    place_bid(db, BidCreate(auction_id=auction.id, bidder_id=bidder.id, amount=Decimal('200.00')))

    result = close_auction(db, auction.id, actor='admin')
    assert result.state == AuctionState.awarded
    assert result.award is not None
    assert result.award.final_amount == Decimal('200.00')


def test_bug2_sin_reserve_con_puja_resulta_adjudicada(db):
    """Sin precio de reserva, cualquier puja adjudica."""
    auction = _make_auction(db, reserve_price=None)
    create_lot(db, LotCreate(auction_id=auction.id, code='L1', name='Lote 1', base_price=Decimal('50.00')))
    bidder, _ = _make_bidder_and_register(db, auction.id)

    place_bid(db, BidCreate(auction_id=auction.id, bidder_id=bidder.id, amount=Decimal('50.00')))

    result = close_auction(db, auction.id, actor='admin')
    assert result.state == AuctionState.awarded


def test_bug2_sin_pujas_resulta_desierta(db):
    """Sin pujas → desierta, con o sin precio de reserva."""
    auction = _make_auction(db, reserve_price=Decimal('100.00'))
    result = close_auction(db, auction.id, actor='admin')
    assert result.state == AuctionState.deserted


# ─── BUG-3 ────────────────────────────────────────────────────────────────────

def test_bug3_place_bid_usa_with_for_update():
    """place_bid() debe usar with_for_update() en la consulta de la subasta."""
    import inspect
    from fastapi_modulo.modulos.subastas.modelos import store
    source = inspect.getsource(store.place_bid)
    assert 'with_for_update' in source, 'place_bid debe usar with_for_update para prevenir race conditions'


def test_bug3_postor_sin_autorizacion_no_puede_pujar(db):
    """Validación de autorización sigue funcionando con la nueva lógica de lock."""
    auction = _make_auction(db)
    create_lot(db, LotCreate(auction_id=auction.id, code='L1', name='Lote 1', base_price=Decimal('0.00')))
    bidder = create_bidder(db, BidderCreate(full_name='Sin Auth', email='noauth@test.com'))
    bidder.state = BidderState.approved
    db.commit()
    register_bidder(db, RegistrationCreate(
        auction_id=auction.id, bidder_id=bidder.id, is_authorized=False
    ))

    with pytest.raises(BusinessRuleError, match='autorizado'):
        place_bid(db, BidCreate(auction_id=auction.id, bidder_id=bidder.id, amount=Decimal('50.00')))


# ─── BUG-4 ────────────────────────────────────────────────────────────────────

def test_bug4_award_tiene_relationship_bidder():
    """Award debe tener atributo relationship 'bidder' declarado."""
    from fastapi_modulo.modulos.subastas.modelos.db_models import Award
    assert hasattr(Award, 'bidder'), 'Award debe tener relationship bidder'


def test_bug4_award_bidder_navegable(db):
    """Después de adjudicar, award.bidder debe retornar el objeto Bidder completo."""
    auction = _make_auction(db)
    create_lot(db, LotCreate(auction_id=auction.id, code='L1', name='Lote 1', base_price=Decimal('0.00')))
    bidder, _ = _make_bidder_and_register(db, auction.id)
    place_bid(db, BidCreate(auction_id=auction.id, bidder_id=bidder.id, amount=Decimal('10.00')))

    result = close_auction(db, auction.id, actor='admin')
    db.refresh(result.award)
    assert result.award.bidder is not None
    assert result.award.bidder.id == bidder.id
    assert result.award.bidder.full_name == 'Postor Test'


def test_bug4_bidder_tiene_relationship_awards():
    """Bidder debe tener atributo relationship 'awards' declarado."""
    from fastapi_modulo.modulos.subastas.modelos.db_models import Bidder
    assert hasattr(Bidder, 'awards'), 'Bidder debe tener relationship awards'


def test_bug4_bidder_awards_navegable(db):
    """Desde un Bidder se debe poder navegar a sus adjudicaciones ganadas."""
    auction = _make_auction(db)
    create_lot(db, LotCreate(auction_id=auction.id, code='L1', name='Lote 1', base_price=Decimal('0.00')))
    bidder, _ = _make_bidder_and_register(db, auction.id)
    place_bid(db, BidCreate(auction_id=auction.id, bidder_id=bidder.id, amount=Decimal('10.00')))
    close_auction(db, auction.id, actor='admin')

    db.refresh(bidder)
    assert len(bidder.awards) == 1
    assert bidder.awards[0].final_amount == Decimal('10.00')


# ─── BUG-5 ────────────────────────────────────────────────────────────────────

def test_bug5_payment_tiene_relationship_award():
    """Payment debe tener atributo relationship 'award' declarado."""
    from fastapi_modulo.modulos.subastas.modelos.db_models import Payment
    assert hasattr(Payment, 'award'), 'Payment debe tener relationship award'


def test_bug5_payment_award_navegable(db):
    """Desde un Payment se debe poder navegar a su Award."""
    auction = _make_auction(db)
    create_lot(db, LotCreate(auction_id=auction.id, code='L1', name='Lote 1', base_price=Decimal('0.00')))
    bidder, _ = _make_bidder_and_register(db, auction.id)
    place_bid(db, BidCreate(auction_id=auction.id, bidder_id=bidder.id, amount=Decimal('100.00')))
    closed = close_auction(db, auction.id, actor='admin')

    payment = create_payment(db, PaymentCreate(
        award_id=closed.award.id,
        amount=Decimal('100.00'),
        method='efectivo',
    ))
    db.refresh(payment)
    assert payment.award is not None
    assert payment.award.id == closed.award.id


def test_bug5_award_tiene_relationship_payments():
    """Award debe tener atributo relationship 'payments' declarado."""
    from fastapi_modulo.modulos.subastas.modelos.db_models import Award
    assert hasattr(Award, 'payments'), 'Award debe tener relationship payments'


def test_bug5_award_payments_navegable(db):
    """Desde un Award se debe poder navegar a sus pagos registrados."""
    auction = _make_auction(db)
    create_lot(db, LotCreate(auction_id=auction.id, code='L1', name='Lote 1', base_price=Decimal('0.00')))
    bidder, _ = _make_bidder_and_register(db, auction.id)
    place_bid(db, BidCreate(auction_id=auction.id, bidder_id=bidder.id, amount=Decimal('200.00')))
    closed = close_auction(db, auction.id, actor='admin')

    create_payment(db, PaymentCreate(award_id=closed.award.id, amount=Decimal('100.00')))
    create_payment(db, PaymentCreate(award_id=closed.award.id, amount=Decimal('100.00')))

    db.refresh(closed.award)
    assert len(closed.award.payments) == 2
