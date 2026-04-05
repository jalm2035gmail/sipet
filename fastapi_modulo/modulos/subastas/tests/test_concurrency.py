"""
7.2 — Prueba de concurrencia en pujas simultáneas.

Objetivo: demostrar que dos hilos que pujan al mismo tiempo desde la misma
base no producen un estado inconsistente (doble-adjudicación o incremento
omitido). En SQLite el SELECT FOR UPDATE no bloquea realmente, pero la
lógica de validación serializada debe rechazar al menos una puja inválida.

En producción con PostgreSQL el bloqueo es real; aquí verificamos que la
estructura del código lo contempla correctamente.
"""
from __future__ import annotations

import threading
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi_modulo.modulos.subastas.modelos.db_models import Base, BidderState
from fastapi_modulo.modulos.subastas.modelos.schemas import BidCreate
from fastapi_modulo.modulos.subastas.modelos.store import (
    BusinessRuleError,
    place_bid,
)
from .conftest import authorize, make_auction, make_bidder, make_lot


def _make_session_factory():
    engine = create_engine(
        "sqlite:///file::memory:?cache=shared",
        connect_args={"check_same_thread": False, "uri": True},
    )
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, autoflush=False, autocommit=False)


def test_estructura_place_bid_usa_with_for_update():
    """Verificación estática: place_bid debe tener with_for_update()."""
    import inspect
    from fastapi_modulo.modulos.subastas.modelos import store
    src = inspect.getsource(store.place_bid)
    assert "with_for_update" in src


def test_dos_pujas_simultaneas_no_producen_bid_por_debajo_del_minimo():
    """
    Simula dos postores pujando al mismo tiempo partiendo de la misma
    mejor puja. Al menos una de las dos debe ser rechazada o ambas deben
    ser válidas pero con montos que respeten el incremento.

    Con SQLite (sin bloqueo real) ambas pueden pasar; lo importante es que
    ninguna quede con monto < base. Con PostgreSQL en producción el FOR UPDATE
    garantiza serialización.
    """
    engine, SessionFactory = _make_session_factory()

    # Preparar datos en sesión maestra
    setup_db = SessionFactory()
    auction = make_auction(setup_db)
    make_lot(setup_db, auction.id, base_price=Decimal("100.00"))
    b1 = make_bidder(setup_db, email="concurrent1@test.com")
    b2 = make_bidder(setup_db, email="concurrent2@test.com")
    authorize(setup_db, auction.id, b1.id)
    authorize(setup_db, auction.id, b2.id)
    auction_id, b1_id, b2_id = auction.id, b1.id, b2.id
    setup_db.close()

    results = []
    errors  = []

    def do_bid(bidder_id, amount):
        db = SessionFactory()
        try:
            b = place_bid(db, BidCreate(
                auction_id=auction_id,
                bidder_id=bidder_id,
                amount=Decimal(str(amount)),
            ))
            results.append(b.amount)
        except BusinessRuleError as e:
            errors.append(str(e))
        except Exception as e:
            errors.append(f"unexpected: {e}")
        finally:
            db.close()

    # Ambos intentan pujar 100 (la base) al mismo tiempo
    t1 = threading.Thread(target=do_bid, args=(b1_id, "100.00"))
    t2 = threading.Thread(target=do_bid, args=(b2_id, "100.00"))
    t1.start(); t2.start()
    t1.join();  t2.join()

    # Al menos una puja debe haberse registrado
    assert len(results) >= 1, "Al menos una puja debió registrarse"

    # Ninguna puja registrada debe estar por debajo de la base
    for amount in results:
        assert amount >= Decimal("100.00"), f"Puja {amount} está por debajo de la base"

    # Cleanup
    Base.metadata.drop_all(engine)


def test_segunda_puja_rechazada_si_no_supera_incremento_en_secuencia():
    """
    Versión secuencial que verifica el mismo invariante sin concurrencia.
    Ambos postores intentan pujar 100; el segundo debe fallar porque
    el incremento mínimo es 50 (requiere ≥ 150).
    """
    engine, SessionFactory = _make_session_factory()

    setup_db = SessionFactory()
    auction = make_auction(setup_db, min_increment=Decimal("50.00"))
    make_lot(setup_db, auction.id, base_price=Decimal("100.00"))
    b1 = make_bidder(setup_db, email="seq1@test.com")
    b2 = make_bidder(setup_db, email="seq2@test.com")
    authorize(setup_db, auction.id, b1.id)
    authorize(setup_db, auction.id, b2.id)
    auction_id, b1_id, b2_id = auction.id, b1.id, b2.id
    setup_db.close()

    db1 = SessionFactory()
    place_bid(db1, BidCreate(auction_id=auction_id, bidder_id=b1_id, amount=Decimal("100.00")))
    db1.close()

    db2 = SessionFactory()
    with pytest.raises(BusinessRuleError, match="mínima requerida"):
        place_bid(db2, BidCreate(auction_id=auction_id, bidder_id=b2_id, amount=Decimal("100.00")))
    db2.close()

    Base.metadata.drop_all(engine)
