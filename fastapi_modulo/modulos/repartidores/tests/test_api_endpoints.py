"""
Tests de endpoints HTTP usando FastAPI TestClient.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_repartidor_payload(**kwargs) -> dict:
    return {
        "name": kwargs.get("name", "Rep API Test"),
        "codigo": kwargs.get("codigo", "RAPI001"),
        "telefono": "",
        "email": "",
        "tipo": "interno",
        "state": "available",
        "activo": True,
        "zona_id": None,
        "vehiculo_id": None,
        "negocio": "",
        "sucursal": "",
        "sipet_username": "",
        "tarifa_base": 100,
        "bono_por_entrega": 10,
        "meta_entregas_diarias": 10,
        "max_entregas_simultaneas": 5,
        "notas": "",
        **kwargs,
    }


def _make_entrega_payload(**kwargs) -> dict:
    return {
        "referencia_externa": "",
        "cliente_nombre": kwargs.get("cliente_nombre", "Cliente API"),
        "cliente_telefono": "",
        "origen": "Bodega",
        "destino": kwargs.get("destino", "Calle 123"),
        "descripcion": "",
        "prioridad": "normal",
        "costo_envio": 50,
        "distancia_km": 0.0,
        "tiempo_estimado_min": 0,
        "fecha_programada": (datetime.now() + timedelta(hours=2)).isoformat(),
        "zona_id": None,
        "repartidor_id": None,
        "liquidable": True,
        **kwargs,
    }


# ---------------------------------------------------------------------------
# Endpoints de repartidores
# ---------------------------------------------------------------------------

class TestApiRepartidores:
    def test_listar_repartidores_ok(self, build_client):
        client = build_client()
        resp = client.get("/api/repartidores/repartidores")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert isinstance(body["data"], list)

    def test_crear_repartidor_ok(self, build_client):
        client = build_client()
        payload = _make_repartidor_payload(codigo="RAPINEW1")
        resp = client.post("/api/repartidores/repartidores", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["codigo"] == "RAPINEW1"

    def test_crear_repartidor_estado_invalido_400(self, build_client):
        client = build_client()
        payload = _make_repartidor_payload(codigo="RBAD1", state="volando")
        resp = client.post("/api/repartidores/repartidores", json=payload)
        assert resp.status_code == 400

    def test_crear_repartidor_codigo_duplicado_400(self, build_client):
        client = build_client()
        payload = _make_repartidor_payload(codigo="RDUP1")
        client.post("/api/repartidores/repartidores", json=payload)
        resp = client.post("/api/repartidores/repartidores", json=payload)
        assert resp.status_code == 400

    def test_actualizar_repartidor_ok(self, build_client):
        client = build_client()
        payload = _make_repartidor_payload(codigo="RUPD1")
        created = client.post("/api/repartidores/repartidores", json=payload).json()
        rep_id = created["data"]["id"]

        resp = client.put(
            f"/api/repartidores/repartidores/{rep_id}", json={"name": "Actualizado"}
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "Actualizado"

    def test_actualizar_repartidor_inexistente_404(self, build_client):
        client = build_client()
        resp = client.put("/api/repartidores/repartidores/99999", json={"name": "X"})
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Endpoints de zonas
# ---------------------------------------------------------------------------

class TestApiZonas:
    def test_listar_zonas_ok(self, build_client):
        client = build_client()
        resp = client.get("/api/repartidores/zonas")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_crear_zona_ok(self, build_client):
        client = build_client()
        resp = client.post(
            "/api/repartidores/zonas",
            json={"name": "Sur", "code": "SUR_APITEST1", "ciudad": "CDMX", "radio_km": 5.0},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["code"] == "SUR_APITEST1"

    def test_crear_zona_codigo_duplicado_400(self, build_client):
        client = build_client()
        payload = {"name": "Dup", "code": "DUP_APIZONE1", "ciudad": "CDMX", "radio_km": 3.0}
        client.post("/api/repartidores/zonas", json=payload)
        resp = client.post("/api/repartidores/zonas", json=payload)
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Endpoints de entregas
# ---------------------------------------------------------------------------

class TestApiEntregas:
    def test_listar_entregas_ok(self, build_client):
        client = build_client()
        resp = client.get("/api/repartidores/entregas")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_crear_entrega_ok(self, build_client):
        client = build_client()
        payload = _make_entrega_payload(cliente_nombre="María Test")
        resp = client.post("/api/repartidores/entregas", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["state"] == "draft"
        assert body["data"]["folio"].startswith("REP")

    def test_crear_entrega_prioridad_invalida_400(self, build_client):
        client = build_client()
        payload = _make_entrega_payload(prioridad="MUYURGENTE")
        resp = client.post("/api/repartidores/entregas", json=payload)
        assert resp.status_code == 400

    def test_asignar_entrega_ok(self, build_client):
        client = build_client()
        rep = client.post(
            "/api/repartidores/repartidores",
            json=_make_repartidor_payload(codigo="RASIGN1"),
        ).json()["data"]
        entrega = client.post(
            "/api/repartidores/entregas", json=_make_entrega_payload()
        ).json()["data"]

        resp = client.post(
            f"/api/repartidores/entregas/{entrega['id']}/asignar",
            json={"repartidor_id": rep["id"]},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["state"] == "assigned"

    def test_asignar_entrega_repartidor_offline_400(self, build_client):
        client = build_client()
        rep = client.post(
            "/api/repartidores/repartidores",
            json=_make_repartidor_payload(codigo="ROFFL1", state="offline"),
        ).json()["data"]
        entrega = client.post(
            "/api/repartidores/entregas", json=_make_entrega_payload()
        ).json()["data"]

        resp = client.post(
            f"/api/repartidores/entregas/{entrega['id']}/asignar",
            json={"repartidor_id": rep["id"]},
        )
        assert resp.status_code == 400

    def test_cambiar_estado_entrega_ok(self, build_client):
        client = build_client()
        rep = client.post(
            "/api/repartidores/repartidores",
            json=_make_repartidor_payload(codigo="RESTADO1"),
        ).json()["data"]
        entrega = client.post(
            "/api/repartidores/entregas", json=_make_entrega_payload()
        ).json()["data"]
        client.post(
            f"/api/repartidores/entregas/{entrega['id']}/asignar",
            json={"repartidor_id": rep["id"]},
        )

        resp = client.post(
            f"/api/repartidores/entregas/{entrega['id']}/estado",
            json={"state": "picked_up"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["state"] == "picked_up"

    def test_cambiar_estado_transicion_invalida_400(self, build_client):
        client = build_client()
        entrega = client.post(
            "/api/repartidores/entregas", json=_make_entrega_payload()
        ).json()["data"]

        resp = client.post(
            f"/api/repartidores/entregas/{entrega['id']}/estado",
            json={"state": "in_transit"},
        )
        assert resp.status_code == 400

    def test_delivered_sin_evidencia_400(self, build_client):
        client = build_client()
        rep = client.post(
            "/api/repartidores/repartidores",
            json=_make_repartidor_payload(codigo="REVIDENCIA1"),
        ).json()["data"]
        entrega = client.post(
            "/api/repartidores/entregas", json=_make_entrega_payload()
        ).json()["data"]
        client.post(
            f"/api/repartidores/entregas/{entrega['id']}/asignar",
            json={"repartidor_id": rep["id"]},
        )
        client.post(
            f"/api/repartidores/entregas/{entrega['id']}/estado",
            json={"state": "picked_up"},
        )
        client.post(
            f"/api/repartidores/entregas/{entrega['id']}/estado",
            json={"state": "in_transit"},
        )

        resp = client.post(
            f"/api/repartidores/entregas/{entrega['id']}/estado",
            json={"state": "delivered", "evidencia_entrega": "cort"},
        )
        assert resp.status_code == 400

    def test_log_entrega_endpoint(self, build_client):
        client = build_client()
        rep = client.post(
            "/api/repartidores/repartidores",
            json=_make_repartidor_payload(codigo="RLOG1"),
        ).json()["data"]
        entrega = client.post(
            "/api/repartidores/entregas", json=_make_entrega_payload()
        ).json()["data"]
        client.post(
            f"/api/repartidores/entregas/{entrega['id']}/asignar",
            json={"repartidor_id": rep["id"]},
        )

        resp = client.get(f"/api/repartidores/entregas/{entrega['id']}/log")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert len(body["data"]) >= 1


# ---------------------------------------------------------------------------
# Endpoint de stats
# ---------------------------------------------------------------------------

class TestApiStats:
    def test_stats_ok(self, build_client):
        client = build_client()
        resp = client.get("/api/repartidores/stats")
        assert resp.status_code == 200
        body = resp.json()
        assert "repartidores_activos" in body or body.get("success") is True
