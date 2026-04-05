"""
7.4 — Pruebas de endpoints API con FastAPI TestClient.

Cubre: CRUD de subastas, lotes, postores, registros, pujas,
adjudicaciones, pagos, entregas, bitácora y dashboard.
"""
from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi_modulo.modulos.subastas.modelos.db_models import Base
from fastapi_modulo.modulos.subastas.modelos.store import (
    close_auction,
    create_payment,
)
from fastapi_modulo.modulos.subastas.modelos.schemas import PaymentCreate
from .conftest import authorize, bid, make_auction, make_bidder, make_lot


# ── App de prueba aislada ────────────────────────────────────────────────────

@pytest.fixture
def client(tmp_path):
    """TestClient con BD SQLite temporaria e inyección de dependencias."""
    db_url = f"sqlite:///{tmp_path}/test.db"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    # Importar router y sobreescribir get_db
    from fastapi_modulo.modulos.subastas.controladores.subastas import router, get_db
    app = FastAPI()
    app.include_router(router)

    def override_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture
def db_direct(tmp_path):
    """Sesión directa sobre la misma BD usada por client (para setup)."""
    db_url = f"sqlite:///{tmp_path}/test.db"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = Session()
    yield session
    session.close()


# ── Dashboard ────────────────────────────────────────────────────────────────

def test_dashboard_devuelve_stats(client):
    res = client.get("/subastas/api/dashboard")
    assert res.status_code == 200
    body = res.json()
    assert "total_auctions" in body
    assert "awarded_amount" in body
    assert "conversion_rate" in body


# ── Subastas ─────────────────────────────────────────────────────────────────

def test_crear_subasta(client):
    res = client.post("/subastas/api/auctions", json={
        "name": "Subasta API test",
        "currency": "MXN",
        "min_increment": "10.00",
    })
    assert res.status_code == 201
    assert res.json()["name"] == "Subasta API test"
    assert res.json()["state"] == "draft"


def test_listar_subastas_vacio(client):
    res = client.get("/subastas/api/auctions")
    assert res.status_code == 200
    assert res.json()["total"] == 0
    assert res.json()["items"] == []


def test_listar_subastas_con_filtro_state(client):
    client.post("/subastas/api/auctions", json={"name": "A", "min_increment": "10"})
    client.post("/subastas/api/auctions", json={"name": "B", "min_increment": "10"})
    res = client.get("/subastas/api/auctions?state=draft")
    assert res.status_code == 200
    assert res.json()["total"] == 2


def test_obtener_subasta_por_id(client):
    r = client.post("/subastas/api/auctions", json={"name": "X", "min_increment": "5"})
    aid = r.json()["id"]
    res = client.get(f"/subastas/api/auctions/{aid}")
    assert res.status_code == 200
    assert res.json()["id"] == aid
    assert "lots" in res.json()
    assert "highest_bid" in res.json()


def test_obtener_subasta_inexistente_404(client):
    res = client.get("/subastas/api/auctions/9999")
    assert res.status_code == 404


def test_actualizar_subasta(client):
    r = client.post("/subastas/api/auctions", json={"name": "Original", "min_increment": "10"})
    aid = r.json()["id"]
    res = client.patch(f"/subastas/api/auctions/{aid}", json={"name": "Actualizada"})
    assert res.status_code == 200
    assert res.json()["name"] == "Actualizada"


def test_transicion_publicar(client):
    r = client.post("/subastas/api/auctions", json={"name": "T", "min_increment": "10"})
    aid = r.json()["id"]
    res = client.post(f"/subastas/api/auctions/{aid}/publish")
    assert res.status_code == 200
    assert res.json()["state"] == "published"


def test_transicion_cancelar(client):
    r = client.post("/subastas/api/auctions", json={"name": "C", "min_increment": "10"})
    aid = r.json()["id"]
    res = client.post(f"/subastas/api/auctions/{aid}/cancel")
    assert res.status_code == 200
    assert res.json()["state"] == "cancelled"


def test_transicion_invalida_retorna_400(client):
    r   = client.post("/subastas/api/auctions", json={"name": "I", "min_increment": "10"})
    aid = r.json()["id"]
    client.post(f"/subastas/api/auctions/{aid}/cancel")
    res = client.post(f"/subastas/api/auctions/{aid}/publish")  # ya cancelada
    assert res.status_code == 400


# ── Lotes ─────────────────────────────────────────────────────────────────────

def test_crear_lote(client):
    r   = client.post("/subastas/api/auctions", json={"name": "L", "min_increment": "10"})
    aid = r.json()["id"]
    res = client.post("/subastas/api/lots", json={
        "auction_id": aid, "code": "L1", "name": "Lote 1", "base_price": "100.00"
    })
    assert res.status_code == 201
    assert res.json()["code"] == "L1"


def test_listar_lotes(client):
    r   = client.post("/subastas/api/auctions", json={"name": "L", "min_increment": "10"})
    aid = r.json()["id"]
    client.post("/subastas/api/lots", json={"auction_id": aid, "code": "A", "name": "Lote A"})
    client.post("/subastas/api/lots", json={"auction_id": aid, "code": "B", "name": "Lote B"})
    res = client.get(f"/subastas/api/lots?auction_id={aid}")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_codigo_lote_duplicado_400(client):
    r   = client.post("/subastas/api/auctions", json={"name": "L", "min_increment": "10"})
    aid = r.json()["id"]
    client.post("/subastas/api/lots", json={"auction_id": aid, "code": "X", "name": "Lote X"})
    res = client.post("/subastas/api/lots", json={"auction_id": aid, "code": "X", "name": "Otro"})
    assert res.status_code == 400


def test_actualizar_lote(client):
    r   = client.post("/subastas/api/auctions", json={"name": "L", "min_increment": "10"})
    aid = r.json()["id"]
    lr  = client.post("/subastas/api/lots", json={"auction_id": aid, "code": "U", "name": "Antes"})
    lid = lr.json()["id"]
    res = client.patch(f"/subastas/api/lots/{lid}", json={"name": "Después"})
    assert res.status_code == 200
    assert res.json()["name"] == "Después"


def test_eliminar_lote_en_borrador(client):
    r   = client.post("/subastas/api/auctions", json={"name": "L", "min_increment": "10"})
    aid = r.json()["id"]
    lr  = client.post("/subastas/api/lots", json={"auction_id": aid, "code": "D", "name": "Del"})
    lid = lr.json()["id"]
    res = client.delete(f"/subastas/api/lots/{lid}")
    assert res.status_code == 204
    assert client.get(f"/subastas/api/lots/{lid}").status_code == 404


# ── Postores ──────────────────────────────────────────────────────────────────

def test_crear_postor(client):
    res = client.post("/subastas/api/bidders", json={
        "full_name": "Ana López", "email": "ana@test.com"
    })
    assert res.status_code == 201
    assert res.json()["state"] == "pending"


def test_listar_postores_paginado(client):
    client.post("/subastas/api/bidders", json={"full_name": "A", "email": "a@t.com"})
    client.post("/subastas/api/bidders", json={"full_name": "B", "email": "b@t.com"})
    res = client.get("/subastas/api/bidders?page=1&page_size=1")
    assert res.status_code == 200
    assert res.json()["total"] == 2
    assert len(res.json()["items"]) == 1


def test_aprobar_postor(client):
    r   = client.post("/subastas/api/bidders", json={"full_name": "P", "email": "p@t.com"})
    bid_id = r.json()["id"]
    res = client.post(f"/subastas/api/bidders/{bid_id}/approve")
    assert res.status_code == 200
    assert res.json()["state"] == "approved"


def test_email_duplicado_400(client):
    client.post("/subastas/api/bidders", json={"full_name": "X", "email": "dup@t.com"})
    res = client.post("/subastas/api/bidders", json={"full_name": "Y", "email": "dup@t.com"})
    assert res.status_code == 400


# ── Registros ─────────────────────────────────────────────────────────────────

def test_registrar_postor_en_subasta(client):
    ar  = client.post("/subastas/api/auctions", json={"name": "R", "min_increment": "10"})
    br  = client.post("/subastas/api/bidders",  json={"full_name": "R", "email": "r@t.com"})
    res = client.post("/subastas/api/registrations", json={
        "auction_id": ar.json()["id"],
        "bidder_id":  br.json()["id"],
        "is_authorized": False,
    })
    assert res.status_code == 201
    assert res.json()["is_authorized"] is False


def test_aprobar_registro(client):
    ar  = client.post("/subastas/api/auctions", json={"name": "AR", "min_increment": "10"})
    br  = client.post("/subastas/api/bidders",  json={"full_name": "AR", "email": "ar@t.com"})
    rr  = client.post("/subastas/api/registrations", json={
        "auction_id": ar.json()["id"], "bidder_id": br.json()["id"]
    })
    rid = rr.json()["id"]
    res = client.post(f"/subastas/api/registrations/{rid}/approve",
                      json={"approved_by": "admin"})
    assert res.status_code == 200
    assert res.json()["is_authorized"] is True


# ── Pujas ─────────────────────────────────────────────────────────────────────

def _setup_biddable(client):
    """Crea subasta publicada + lote + postor autorizado. Devuelve (auction_id, bidder_id)."""
    ar = client.post("/subastas/api/auctions", json={
        "name": "Pujable", "min_increment": "10",
        "start_at": "2000-01-01T00:00:00",
        "end_at":   "2099-12-31T00:00:00",
    })
    aid = ar.json()["id"]
    client.post("/subastas/api/auctions/{}/publish".format(aid))
    client.post("/subastas/api/lots", json={"auction_id": aid, "code": "L", "name": "L", "base_price": "0"})
    br  = client.post("/subastas/api/bidders", json={"full_name": "Postor", "email": "postor@t.com"})
    bid_id = br.json()["id"]
    client.post(f"/subastas/api/bidders/{bid_id}/approve")
    rr = client.post("/subastas/api/registrations", json={
        "auction_id": aid, "bidder_id": bid_id, "is_authorized": True
    })
    return aid, bid_id


def test_registrar_puja(client):
    aid, bid_id = _setup_biddable(client)
    res = client.post("/subastas/api/bids", json={
        "auction_id": aid, "bidder_id": bid_id, "amount": "50.00"
    })
    assert res.status_code == 201
    assert float(res.json()["amount"]) == 50.0


def test_listar_pujas_de_subasta(client):
    aid, bid_id = _setup_biddable(client)
    client.post("/subastas/api/bids", json={"auction_id": aid, "bidder_id": bid_id, "amount": "50"})
    client.post("/subastas/api/bids", json={"auction_id": aid, "bidder_id": bid_id, "amount": "70"})
    res = client.get(f"/subastas/api/auctions/{aid}/bids")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_puja_invalida_400(client):
    aid, bid_id = _setup_biddable(client)
    client.post("/subastas/api/bids", json={"auction_id": aid, "bidder_id": bid_id, "amount": "100"})
    # incremento mínimo 10, así que 105 < 110 → error
    res = client.post("/subastas/api/bids", json={
        "auction_id": aid, "bidder_id": bid_id, "amount": "105"
    })
    assert res.status_code == 400


# ── Adjudicaciones ────────────────────────────────────────────────────────────

def test_cerrar_subasta_con_puja_devuelve_adjudicacion(client):
    aid, bid_id = _setup_biddable(client)
    client.post("/subastas/api/bids", json={"auction_id": aid, "bidder_id": bid_id, "amount": "200"})
    res = client.post(f"/subastas/api/auctions/{aid}/close")
    assert res.status_code == 200
    assert res.json()["state"] == "awarded"
    # El detalle de la subasta debe exponer la adjudicación
    detail = client.get(f"/subastas/api/auctions/{aid}").json()
    assert detail["award"]["final_amount"] == "200.00"


def test_listar_adjudicaciones(client):
    aid, bid_id = _setup_biddable(client)
    client.post("/subastas/api/bids", json={"auction_id": aid, "bidder_id": bid_id, "amount": "100"})
    client.post(f"/subastas/api/auctions/{aid}/close")
    res = client.get("/subastas/api/awards")
    assert res.status_code == 200
    assert len(res.json()) >= 1


# ── Pagos ─────────────────────────────────────────────────────────────────────

def test_registrar_pago(client):
    aid, bid_id = _setup_biddable(client)
    client.post("/subastas/api/bids", json={"auction_id": aid, "bidder_id": bid_id, "amount": "300"})
    client.post(f"/subastas/api/auctions/{aid}/close")
    awards = client.get("/subastas/api/awards").json()
    award_id = awards[0]["id"]

    res = client.post("/subastas/api/payments", json={
        "award_id": award_id, "amount": "300.00", "state": "paid", "method": "transferencia"
    })
    assert res.status_code == 201
    assert res.json()["state"] == "paid"


def test_listar_pagos_de_adjudicacion(client):
    aid, bid_id = _setup_biddable(client)
    client.post("/subastas/api/bids", json={"auction_id": aid, "bidder_id": bid_id, "amount": "100"})
    client.post(f"/subastas/api/auctions/{aid}/close")
    award_id = client.get("/subastas/api/awards").json()[0]["id"]
    client.post("/subastas/api/payments", json={"award_id": award_id, "amount": "50", "state": "partial"})
    client.post("/subastas/api/payments", json={"award_id": award_id, "amount": "50", "state": "paid"})
    res = client.get(f"/subastas/api/payments?award_id={award_id}")
    assert res.status_code == 200
    assert len(res.json()) == 2


# ── Entregas ──────────────────────────────────────────────────────────────────

def _setup_paid_award_api(client):
    aid, bid_id = _setup_biddable(client)
    client.post("/subastas/api/bids", json={"auction_id": aid, "bidder_id": bid_id, "amount": "500"})
    client.post(f"/subastas/api/auctions/{aid}/close")
    award_id = client.get("/subastas/api/awards").json()[0]["id"]
    client.post("/subastas/api/payments", json={"award_id": award_id, "amount": "500", "state": "paid"})
    return award_id


def test_crear_entrega(client):
    award_id = _setup_paid_award_api(client)
    res = client.post("/subastas/api/deliveries", json={
        "award_id": award_id, "delivery_address": "Calle 1"
    })
    assert res.status_code == 201
    assert res.json()["state"] == "pending"


def test_confirmar_entrega(client):
    award_id    = _setup_paid_award_api(client)
    delivery_id = client.post("/subastas/api/deliveries",
                              json={"award_id": award_id}).json()["id"]
    res = client.post(f"/subastas/api/deliveries/{delivery_id}/confirm",
                      json={"received_by": "Cliente Final"})
    assert res.status_code == 200
    assert res.json()["state"] == "delivered"
    assert res.json()["received_by"] == "Cliente Final"


def test_cancelar_entrega(client):
    award_id    = _setup_paid_award_api(client)
    delivery_id = client.post("/subastas/api/deliveries",
                              json={"award_id": award_id}).json()["id"]
    res = client.post(f"/subastas/api/deliveries/{delivery_id}/cancel")
    assert res.status_code == 200
    assert res.json()["state"] == "cancelled"


def test_entrega_con_referencia_externa(client):
    award_id = _setup_paid_award_api(client)
    res = client.post("/subastas/api/deliveries", json={
        "award_id": award_id,
        "external_order_ref": "ORD-MT-9999",
    })
    assert res.status_code == 201
    assert res.json()["external_order_ref"] == "ORD-MT-9999"


# ── Bitácora ──────────────────────────────────────────────────────────────────

def test_eventos_registrados_en_bitacora(client):
    r   = client.post("/subastas/api/auctions", json={"name": "Bitácora", "min_increment": "10"})
    aid = r.json()["id"]
    client.post(f"/subastas/api/auctions/{aid}/publish")
    client.post(f"/subastas/api/auctions/{aid}/cancel")

    res = client.get(f"/subastas/api/auctions/{aid}/events")
    assert res.status_code == 200
    types = {e["event_type"] for e in res.json()}
    assert "auction_created"   in types
    assert "auction_published" in types
    assert "auction_cancelled" in types


def test_filtrar_eventos_por_tipo(client):
    r   = client.post("/subastas/api/auctions", json={"name": "FE", "min_increment": "10"})
    aid = r.json()["id"]
    client.post(f"/subastas/api/auctions/{aid}/publish")

    res = client.get(f"/subastas/api/auctions/{aid}/events?event_type=auction_published")
    assert res.status_code == 200
    assert all(e["event_type"] == "auction_published" for e in res.json())
