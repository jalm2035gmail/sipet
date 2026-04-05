from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)
os.environ.setdefault("APP_ENV", "test")

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
    RegistrationCreate,
)
from fastapi_modulo.modulos.subastas.modelos.store import (
    close_auction,
    create_auction,
    create_bidder,
    create_lot,
    place_bid,
    register_bidder,
)


# ── Sesión de BD en memoria ──────────────────────────────────────────────────

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


# ── Factories reutilizables ──────────────────────────────────────────────────

def make_auction(
    db,
    *,
    reserve_price=None,
    min_increment=Decimal("10.00"),
    state=AuctionState.published,
    start_at=None,
    end_at=None,
    auto_extend_seconds=0,
):
    data = AuctionCreate(
        name="Subasta test",
        start_at=start_at or datetime(2000, 1, 1),
        end_at=end_at or datetime(2099, 12, 31),
        min_increment=min_increment,
        reserve_price=reserve_price,
        auto_extend_seconds=auto_extend_seconds,
    )
    auction = create_auction(db, data)
    auction.state = state
    db.commit()
    db.refresh(auction)
    return auction


def make_bidder(db, *, email="postor@test.com", state=BidderState.approved):
    bidder = create_bidder(db, BidderCreate(full_name="Postor Test", email=email))
    bidder.state = state
    db.commit()
    db.refresh(bidder)
    return bidder


def make_lot(db, auction_id, *, code="L1", base_price=Decimal("0.00")):
    return create_lot(
        db,
        LotCreate(auction_id=auction_id, code=code, name=f"Lote {code}", base_price=base_price),
    )


def authorize(db, auction_id, bidder_id, *, approved_by="admin"):
    return register_bidder(
        db,
        RegistrationCreate(
            auction_id=auction_id,
            bidder_id=bidder_id,
            is_authorized=True,
            approved_by=approved_by,
        ),
    )


def bid(db, auction_id, bidder_id, amount):
    return place_bid(db, BidCreate(auction_id=auction_id, bidder_id=bidder_id, amount=Decimal(str(amount))))


# ── Fixture: escenario base (subasta publicada + lote + postor autorizado) ──

@pytest.fixture
def scenario(db):
    """Devuelve (db, auction, lot, bidder) listos para pujar."""
    auction = make_auction(db)
    lot     = make_lot(db, auction.id, base_price=Decimal("100.00"))
    bidder  = make_bidder(db)
    authorize(db, auction.id, bidder.id)
    return db, auction, lot, bidder
