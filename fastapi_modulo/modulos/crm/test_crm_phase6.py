from __future__ import annotations

import os
import sys
import types
from datetime import datetime

import pytest
from sqlalchemy import inspect
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SQLITE_DB_PATH", "/tmp/sipet_crm_phase6.sqlite3")
pytestmark = pytest.mark.filterwarnings("ignore:The 'app' shortcut is now deprecated.*:DeprecationWarning")

# ── Stub de fastapi_modulo.main ───────────────────────────────────────────────

fake_main = types.ModuleType("fastapi_modulo.main")


def _fake_render_backend_page(
    request: Request,
    title: str,
    description: str = "",
    content: str = "",
    **_: object,
) -> HTMLResponse:
    html = f"<html><head><title>{title}</title></head><body>{content}</body></html>"
    return HTMLResponse(content=html)


def _fake_get_user_app_access(request: Request) -> list[str]:
    raw = request.headers.get("x-app-access", "")
    return [item.strip() for item in raw.split(",") if item.strip()]


def _fake_is_admin_or_superadmin(request: Request) -> bool:
    return getattr(request.state, "user_role", "").strip().lower() in {
        "administrador", "admin", "superadministrador", "superadmin",
    }


fake_main.render_backend_page = _fake_render_backend_page
fake_main._get_user_app_access = _fake_get_user_app_access
fake_main.is_admin_or_superadmin = _fake_is_admin_or_superadmin
sys.modules["fastapi_modulo.main"] = fake_main

# ── Imports del módulo bajo prueba ────────────────────────────────────────────

from fastapi_modulo.db import MAIN, engine  # noqa: E402
from fastapi_modulo.modulos.crm.controladores.crm import router  # noqa: E402
from fastapi_modulo.modulos.crm.modelos.crm_db_models import (  # noqa: E402
    CrmActividad,
    CrmCampania,
    CrmContacto,
    CrmContactoCampania,
    CrmEvento,
    CrmNota,
    CrmOportunidad,
)

CRM_TABLES = [
    CrmContacto.__table__,
    CrmOportunidad.__table__,
    CrmActividad.__table__,
    CrmNota.__table__,
    CrmCampania.__table__,
    CrmContactoCampania.__table__,
    CrmEvento.__table__,
]


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _build_client() -> TestClient:
    app = FastAPI()

    @app.middleware("http")
    async def inject_test_session(request: Request, call_next):
        request.state.user_name = request.headers.get("x-user", "tester")
        request.state.user_role = request.headers.get("x-role", "usuario")
        request.state.tenant_id = request.headers.get("x-tenant-id", "test")
        return await call_next(request)

    app.include_router(router)
    return TestClient(app)


def _auth(role: str = "usuario", *access: str) -> dict[str, str]:
    headers = {"x-role": role, "x-user": "crm.test"}
    if access:
        headers["x-app-access"] = ",".join(access)
    return headers


def _auth_tenant(tenant: str, role: str = "usuario", *access: str) -> dict[str, str]:
    headers = _auth(role, *access)
    headers["x-tenant-id"] = tenant
    return headers


def setup_function() -> None:
    MAIN.metadata.drop_all(bind=engine, tables=CRM_TABLES, checkfirst=True)
    MAIN.metadata.create_all(bind=engine, tables=CRM_TABLES, checkfirst=True)


# ── Permisos y acceso ─────────────────────────────────────────────────────────

def test_crm_html_requires_access() -> None:
    client = _build_client()
    response = client.get("/crm")
    assert response.status_code == 403
    assert response.json()["detail"] == "Acceso restringido al módulo CRM"


def test_crm_html_admin_bypasses_permission() -> None:
    client = _build_client()
    response = client.get("/crm", headers=_auth("administrador"))
    assert response.status_code == 200
    assert "crm-root" in response.text


def test_crm_html_renders_with_crm_access() -> None:
    client = _build_client()
    response = client.get("/crm", headers=_auth("usuario", "CRM"))
    assert response.status_code == 200
    assert "CRM" in response.text
    assert "crm-root" in response.text


def test_crm_api_blocks_without_access() -> None:
    client = _build_client()
    response = client.get("/api/crm/contactos")
    assert response.status_code == 403


def test_crm_js_asset_served() -> None:
    client = _build_client()
    response = client.get("/api/crm/assets/crm.js", headers=_auth("usuario", "CRM"))
    assert response.status_code == 200
    assert "application/javascript" in response.headers["content-type"]


# ── Contactos ─────────────────────────────────────────────────────────────────

def test_create_and_list_contacto() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    r = client.post("/api/crm/contactos", headers=headers, json={
        "nombre": "Laura Gomez",
        "email": "laura@example.com",
        "telefono": "555-0101",
        "empresa": "Acme",
        "puesto": "Gerente",
        "tipo": "prospecto",
        "fuente": "backend",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["nombre"] == "Laura Gomez"
    assert data["tipo"] == "prospecto"
    contacto_id = data["id"]

    listing = client.get("/api/crm/contactos", headers=headers)
    assert listing.status_code == 200
    ids = [c["id"] for c in listing.json()]
    assert contacto_id in ids


def test_get_contacto_detail() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    r = client.post("/api/crm/contactos", headers=headers, json={
        "nombre": "Pedro Ruiz",
        "email": "pedro@example.com",
    })
    contacto_id = r.json()["id"]

    detail = client.get(f"/api/crm/contactos/{contacto_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["nombre"] == "Pedro Ruiz"


def test_get_contacto_not_found() -> None:
    client = _build_client()
    r = client.get("/api/crm/contactos/99999", headers=_auth("usuario", "CRM"))
    assert r.status_code == 404


def test_update_contacto() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    r = client.post("/api/crm/contactos", headers=headers, json={"nombre": "Carlos Mora"})
    contacto_id = r.json()["id"]

    upd = client.put(f"/api/crm/contactos/{contacto_id}", headers=headers, json={"tipo": "cliente"})
    assert upd.status_code == 200
    assert upd.json()["tipo"] == "cliente"


def test_delete_contacto() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    r = client.post("/api/crm/contactos", headers=headers, json={"nombre": "Borrar Este"})
    contacto_id = r.json()["id"]

    d = client.delete(f"/api/crm/contactos/{contacto_id}", headers=headers)
    assert d.status_code == 200
    assert d.json()["ok"] is True

    listing = client.get("/api/crm/contactos", headers=headers)
    ids = [c["id"] for c in listing.json()]
    assert contacto_id not in ids


def test_convertir_contacto_a_cliente() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    created = client.post("/api/crm/contactos", headers=headers, json={"nombre": "Conversión Cliente"})
    contacto_id = created.json()["id"]

    converted = client.post(f"/api/crm/contactos/{contacto_id}/convertir-cliente", headers=headers)
    assert converted.status_code == 200
    assert converted.json()["tipo"] == "cliente"


def test_duplicate_email_rejected() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    client.post("/api/crm/contactos", headers=headers, json={
        "nombre": "Primero", "email": "dup@example.com",
    })
    r = client.post("/api/crm/contactos", headers=headers, json={
        "nombre": "Segundo", "email": "dup@example.com",
    })
    assert r.status_code == 409
    assert "email" in r.json()["detail"].lower()


def test_contacto_email_normalizado_a_minusculas() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    r = client.post("/api/crm/contactos", headers=headers, json={
        "nombre": "Correo Normalizado",
        "email": "USER@Example.COM",
    })
    assert r.status_code == 201
    assert r.json()["email"] == "user@example.com"


def test_contacto_guarda_scoring_sucursal_y_origen_detallado() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    r = client.post("/api/crm/contactos", headers=headers, json={
        "nombre": "Lead Scoring",
        "email": "lead@example.com",
        "telefono": "5551234",
        "empresa": "AVAN",
        "puesto": "Gerente",
        "sucursal": "Centro",
        "fuente": "campania",
        "fuente_detalle": "Meta Ads",
    })
    assert r.status_code == 201
    assert r.json()["sucursal"] == "Centro"
    assert r.json()["fuente_detalle"] == "Meta Ads"
    assert r.json()["lead_score"] >= 70


def test_contacto_nombre_corto_rechazado() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    r = client.post("/api/crm/contactos", headers=headers, json={"nombre": "Al"})
    assert r.status_code == 422


# ── Oportunidades ─────────────────────────────────────────────────────────────

def test_create_oportunidad_full_flow() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    contacto = client.post("/api/crm/contactos", headers=headers, json={"nombre": "Sofia Torres"})
    contacto_id = contacto.json()["id"]

    r = client.post("/api/crm/oportunidades", headers=headers, json={
        "contacto_id": contacto_id,
        "nombre": "Proyecto Alpha",
        "etapa": "negociacion",
        "valor_estimado": 25000.0,
        "probabilidad": 60,
        "responsable": "vendedor1",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["nombre"] == "Proyecto Alpha"
    assert data["etapa"] == "negociacion"
    assert data["contacto_nombre"] == "Sofia Torres"
    op_id = data["id"]

    listing = client.get("/api/crm/oportunidades", headers=headers)
    assert any(o["id"] == op_id for o in listing.json())


def test_update_oportunidad_etapa() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    contacto = client.post("/api/crm/contactos", headers=headers, json={"nombre": "Rene Vargas"})
    contacto_id = contacto.json()["id"]
    op = client.post("/api/crm/oportunidades", headers=headers, json={
        "contacto_id": contacto_id, "nombre": "Deal B",
    })
    op_id = op.json()["id"]

    upd = client.put(f"/api/crm/oportunidades/{op_id}", headers=headers, json={"etapa": "cerrado_ganado"})
    assert upd.status_code == 200
    assert upd.json()["etapa"] == "cerrado_ganado"
    assert upd.json()["fecha_cierre_real"]


def test_oportunidad_cerrada_no_se_edita_sin_reabrir() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    contacto = client.post("/api/crm/contactos", headers=headers, json={"nombre": "Cierre Controlado"})
    contacto_id = contacto.json()["id"]
    op = client.post("/api/crm/oportunidades", headers=headers, json={
        "contacto_id": contacto_id,
        "nombre": "Cerrada",
        "etapa": "cerrado_ganado",
    })
    op_id = op.json()["id"]

    upd = client.put(f"/api/crm/oportunidades/{op_id}", headers=headers, json={"nombre": "Cambio no permitido"})
    assert upd.status_code == 409


def test_oportunidad_probabilidad_fuera_de_rango_rechazada() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    contacto = client.post("/api/crm/contactos", headers=headers, json={"nombre": "Rango Oportunidad"})
    contacto_id = contacto.json()["id"]
    r = client.post("/api/crm/oportunidades", headers=headers, json={
        "contacto_id": contacto_id,
        "nombre": "Probabilidad mala",
        "probabilidad": 120,
    })
    assert r.status_code == 422


def test_delete_oportunidad() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    contacto = client.post("/api/crm/contactos", headers=headers, json={"nombre": "Hugo Diaz"})
    contacto_id = contacto.json()["id"]
    op = client.post("/api/crm/oportunidades", headers=headers, json={
        "contacto_id": contacto_id, "nombre": "Deal C",
    })
    op_id = op.json()["id"]

    d = client.delete(f"/api/crm/oportunidades/{op_id}", headers=headers)
    assert d.status_code == 200
    listing = client.get("/api/crm/oportunidades", headers=headers)
    assert not any(o["id"] == op_id for o in listing.json())


def test_filtrar_oportunidades_por_etapa() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    contacto = client.post("/api/crm/contactos", headers=headers, json={"nombre": "Filtro Test"})
    cid = contacto.json()["id"]
    client.post("/api/crm/oportunidades", headers=headers, json={"contacto_id": cid, "nombre": "Ganada", "etapa": "cerrado_ganado"})
    client.post("/api/crm/oportunidades", headers=headers, json={"contacto_id": cid, "nombre": "Perdida", "etapa": "cerrado_perdido"})

    r = client.get("/api/crm/oportunidades?etapa=cerrado_ganado", headers=headers)
    assert r.status_code == 200
    assert all(o["etapa"] == "cerrado_ganado" for o in r.json())


def test_acciones_operativas_oportunidad() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    contacto = client.post("/api/crm/contactos", headers=headers, json={"nombre": "Operativa Oportunidad"})
    cid = contacto.json()["id"]
    created = client.post("/api/crm/oportunidades", headers=headers, json={"contacto_id": cid, "nombre": "Pipeline vivo"})
    oportunidad_id = created.json()["id"]

    stage = client.post(f"/api/crm/oportunidades/{oportunidad_id}/etapa", headers=headers, json={"etapa": "propuesta"})
    assert stage.status_code == 200
    assert stage.json()["etapa"] == "propuesta"

    won = client.post(f"/api/crm/oportunidades/{oportunidad_id}/ganar", headers=headers)
    assert won.status_code == 200
    assert won.json()["etapa"] == "cerrado_ganado"
    assert won.json()["cerrado_por"] == "crm.test"

    reopen = client.put(f"/api/crm/oportunidades/{oportunidad_id}", headers=headers, json={"etapa": "negociacion"})
    assert reopen.status_code == 200

    lost = client.post(f"/api/crm/oportunidades/{oportunidad_id}/perder", headers=headers)
    assert lost.status_code == 200
    assert lost.json()["etapa"] == "cerrado_perdido"


def test_oportunidad_crea_actividad_automatica_por_etapa() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    contacto = client.post("/api/crm/contactos", headers=headers, json={"nombre": "Auto Stage", "sucursal": "Norte"})
    cid = contacto.json()["id"]
    created = client.post("/api/crm/oportunidades", headers=headers, json={
        "contacto_id": cid,
        "nombre": "Oportunidad Auto",
        "etapa": "negociacion",
        "responsable": "ejecutivo.auto",
    })
    assert created.status_code == 201
    assert created.json()["sucursal"] == "Norte"

    actividades = client.get("/api/crm/actividades", headers=headers).json()
    assert any(item["oportunidad_id"] == created.json()["id"] and "negociación" in item["titulo"].lower() for item in actividades)


# ── Actividades ───────────────────────────────────────────────────────────────

def test_crear_y_completar_actividad() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    contacto = client.post("/api/crm/contactos", headers=headers, json={"nombre": "Mario Leal"})
    cid = contacto.json()["id"]

    r = client.post("/api/crm/actividades", headers=headers, json={
        "contacto_id": cid,
        "tipo": "llamada",
        "titulo": "Llamada inicial",
        "responsable": "vendedor2",
    })
    assert r.status_code == 201
    act_id = r.json()["id"]
    assert r.json()["completada"] is False

    upd = client.put(f"/api/crm/actividades/{act_id}", headers=headers, json={"completada": True})
    assert upd.status_code == 200
    assert upd.json()["completada"] is True
    assert upd.json()["fecha_completada"]


def test_actividad_requiere_contacto_u_oportunidad() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    r = client.post("/api/crm/actividades", headers=headers, json={
        "tipo": "llamada",
        "titulo": "Sin relación",
    })
    assert r.status_code == 422


def test_filtrar_actividades_pendientes() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    r_pend = client.get("/api/crm/actividades?completada=false", headers=headers)
    assert r_pend.status_code == 200
    assert all(not a["completada"] for a in r_pend.json())


def test_delete_actividad() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    contacto = client.post("/api/crm/contactos", headers=headers, json={"nombre": "Eliminar Actividad"})
    cid = contacto.json()["id"]
    r = client.post("/api/crm/actividades", headers=headers, json={"contacto_id": cid, "tipo": "tarea", "titulo": "Borrar esto"})
    act_id = r.json()["id"]

    d = client.delete(f"/api/crm/actividades/{act_id}", headers=headers)
    assert d.status_code == 200


def test_acciones_operativas_actividad() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    contacto = client.post("/api/crm/contactos", headers=headers, json={"nombre": "Operativa Actividad"})
    cid = contacto.json()["id"]
    created = client.post("/api/crm/actividades", headers=headers, json={
        "contacto_id": cid,
        "titulo": "Seguimiento vencido",
        "fecha": "2025-01-01T09:00:00",
    })
    actividad_id = created.json()["id"]

    overdue = client.get("/api/crm/actividades/vencidas", headers=headers)
    assert overdue.status_code == 200
    assert any(item["id"] == actividad_id for item in overdue.json())

    completed = client.post(f"/api/crm/actividades/{actividad_id}/completar", headers=headers)
    assert completed.status_code == 200
    assert completed.json()["completada"] is True

    rescheduled = client.post(
        f"/api/crm/actividades/{actividad_id}/reprogramar",
        headers=headers,
        json={"fecha": "2027-01-15T11:30:00"},
    )
    assert rescheduled.status_code == 200
    assert rescheduled.json()["completada"] is False
    assert rescheduled.json()["fecha"] == "2027-01-15T11:30:00"
    assert rescheduled.json()["fecha_completada"] == ""


# ── Notas ─────────────────────────────────────────────────────────────────────

def test_crear_y_eliminar_nota() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    contacto = client.post("/api/crm/contactos", headers=headers, json={"nombre": "Elena Cruz"})
    cid = contacto.json()["id"]

    r = client.post("/api/crm/notas", headers=headers, json={
        "contacto_id": cid,
        "contenido": "Interesado en producto X",
        "autor": "crm.test",
    })
    assert r.status_code == 201
    nota_id = r.json()["id"]

    listing = client.get(f"/api/crm/notas?contacto_id={cid}", headers=headers)
    assert any(n["id"] == nota_id for n in listing.json())

    d = client.delete(f"/api/crm/notas/{nota_id}", headers=headers)
    assert d.status_code == 200

    listing_after = client.get(f"/api/crm/notas?contacto_id={cid}", headers=headers)
    assert not any(n["id"] == nota_id for n in listing_after.json())


# ── Campañas ──────────────────────────────────────────────────────────────────

def test_crear_campania_y_listar() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    r = client.post("/api/crm/campanias", headers=headers, json={
        "nombre": "Q1 Promo",
        "tipo": "email",
        "estado": "activa",
        "fecha_inicio": "2026-01-01",
        "fecha_fin": "2026-03-31",
    })
    assert r.status_code == 201
    camp_id = r.json()["id"]
    assert r.json()["estado"] == "activa"

    listing = client.get("/api/crm/campanias", headers=headers)
    assert any(c["id"] == camp_id for c in listing.json())


def test_actualizar_estado_campania() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    r = client.post("/api/crm/campanias", headers=headers, json={"nombre": "Verano 2026"})
    camp_id = r.json()["id"]

    upd = client.put(f"/api/crm/campanias/{camp_id}", headers=headers, json={"estado": "finalizada"})
    assert upd.status_code == 200
    assert upd.json()["estado"] == "finalizada"


def test_campania_rechaza_fecha_fin_menor_a_inicio() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    r = client.post("/api/crm/campanias", headers=headers, json={
        "nombre": "Fechas inválidas",
        "fecha_inicio": "2026-03-10",
        "fecha_fin": "2026-03-01",
    })
    assert r.status_code == 422


def test_asociar_contacto_a_campania() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    contacto = client.post("/api/crm/contactos", headers=headers, json={"nombre": "Ana Rios"})
    cid = contacto.json()["id"]
    camp = client.post("/api/crm/campanias", headers=headers, json={"nombre": "Camp Test"})
    camp_id = camp.json()["id"]

    r = client.post("/api/crm/campanias/contactos", headers=headers, json={
        "contacto_id": cid,
        "campania_id": camp_id,
        "estado": "pendiente",
    })
    assert r.status_code == 201

    listing = client.get(f"/api/crm/campanias/{camp_id}/contactos", headers=headers)
    assert any(cc["contacto_id"] == cid for cc in listing.json())


def test_asociar_contacto_duplicado_a_campania_rechazado() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    contacto = client.post("/api/crm/contactos", headers=headers, json={"nombre": "Ana Repetida"})
    cid = contacto.json()["id"]
    camp = client.post("/api/crm/campanias", headers=headers, json={"nombre": "Camp Repetida"})
    camp_id = camp.json()["id"]

    payload = {"contacto_id": cid, "campania_id": camp_id, "estado": "pendiente"}
    first = client.post("/api/crm/campanias/contactos", headers=headers, json=payload)
    second = client.post("/api/crm/campanias/contactos", headers=headers, json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_remover_contacto_de_campania() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    contacto = client.post("/api/crm/contactos", headers=headers, json={"nombre": "Quitar campaña"})
    cid = contacto.json()["id"]
    camp = client.post("/api/crm/campanias", headers=headers, json={"nombre": "Camp quitar"})
    camp_id = camp.json()["id"]

    created = client.post("/api/crm/campanias/contactos", headers=headers, json={
        "contacto_id": cid,
        "campania_id": camp_id,
        "estado": "pendiente",
    })
    assert created.status_code == 201

    removed = client.delete(f"/api/crm/campanias/{camp_id}/contactos/{cid}", headers=headers)
    assert removed.status_code == 200
    assert removed.json()["ok"] is True

    listing = client.get(f"/api/crm/campanias/{camp_id}/contactos", headers=headers)
    assert listing.status_code == 200
    assert listing.json() == []


def test_eliminar_contacto_elimina_dependencias_relacionadas() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    contacto = client.post("/api/crm/contactos", headers=headers, json={"nombre": "Cascade Contacto"})
    cid = contacto.json()["id"]
    oportunidad = client.post("/api/crm/oportunidades", headers=headers, json={"contacto_id": cid, "nombre": "Deal cascade"})
    oid = oportunidad.json()["id"]
    actividad = client.post("/api/crm/actividades", headers=headers, json={"contacto_id": cid, "oportunidad_id": oid, "titulo": "Actividad cascade"})
    assert actividad.status_code == 201
    nota = client.post("/api/crm/notas", headers=headers, json={"contacto_id": cid, "oportunidad_id": oid, "contenido": "Nota cascade"})
    assert nota.status_code == 201
    campania = client.post("/api/crm/campanias", headers=headers, json={"nombre": "Camp cascade"})
    camp_id = campania.json()["id"]
    vinculo = client.post("/api/crm/campanias/contactos", headers=headers, json={"contacto_id": cid, "campania_id": camp_id})
    assert vinculo.status_code == 201

    deleted = client.delete(f"/api/crm/contactos/{cid}", headers=headers)
    assert deleted.status_code == 200

    oportunidades = client.get("/api/crm/oportunidades", headers=headers).json()
    actividades = client.get("/api/crm/actividades", headers=headers).json()
    notas = client.get(f"/api/crm/notas?contacto_id={cid}", headers=headers).json()
    contactos_campania = client.get(f"/api/crm/campanias/{camp_id}/contactos", headers=headers).json()

    assert not any(item["id"] == oid for item in oportunidades)
    assert not any(item["contacto_id"] == cid for item in actividades)
    assert notas == []
    assert contactos_campania == []


def test_eliminar_oportunidad_elimina_dependencias_relacionadas() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    contacto = client.post("/api/crm/contactos", headers=headers, json={"nombre": "Cascade Oportunidad"})
    cid = contacto.json()["id"]
    oportunidad = client.post("/api/crm/oportunidades", headers=headers, json={"contacto_id": cid, "nombre": "Deal delete"})
    oid = oportunidad.json()["id"]
    actividad = client.post("/api/crm/actividades", headers=headers, json={"contacto_id": cid, "oportunidad_id": oid, "titulo": "Actividad delete"})
    assert actividad.status_code == 201
    nota = client.post("/api/crm/notas", headers=headers, json={"contacto_id": cid, "oportunidad_id": oid, "contenido": "Nota delete"})
    assert nota.status_code == 201

    deleted = client.delete(f"/api/crm/oportunidades/{oid}", headers=headers)
    assert deleted.status_code == 200

    actividades = client.get("/api/crm/actividades", headers=headers).json()
    notas = client.get(f"/api/crm/notas?contacto_id={cid}", headers=headers).json()
    assert not any(item["oportunidad_id"] == oid for item in actividades)
    assert not any(item["oportunidad_id"] == oid for item in notas)


def test_crm_schema_declara_indices_y_unicos_clave() -> None:
    inspector = inspect(engine)

    contacto_indexes = {item["name"] for item in inspector.get_indexes("crm_contactos")}
    oportunidad_indexes = {item["name"] for item in inspector.get_indexes("crm_oportunidades")}
    actividad_indexes = {item["name"] for item in inspector.get_indexes("crm_actividades")}
    campania_indexes = {item["name"] for item in inspector.get_indexes("crm_campanias")}
    contacto_campania_indexes = {item["name"] for item in inspector.get_indexes("crm_contactos_campanias")}
    contacto_uniques = {item["name"] for item in inspector.get_unique_constraints("crm_contactos")}
    contacto_campania_uniques = {item["name"] for item in inspector.get_unique_constraints("crm_contactos_campanias")}

    assert "ix_crm_contactos_tenant_email" in contacto_indexes
    assert "ix_crm_contactos_tenant_tipo" in contacto_indexes
    assert "ix_crm_oportunidades_tenant_etapa" in oportunidad_indexes
    assert "ix_crm_oportunidades_tenant_responsable" in oportunidad_indexes
    assert "ix_crm_oportunidades_tenant_fecha_cierre_est" in oportunidad_indexes
    assert "ix_crm_actividades_tenant_responsable" in actividad_indexes
    assert "ix_crm_actividades_tenant_fecha" in actividad_indexes
    assert "ix_crm_campanias_tenant_estado" in campania_indexes
    assert "ix_crm_campanias_tenant_fecha_inicio" in campania_indexes
    assert "ix_crm_contactos_campanias_tenant_estado" in contacto_campania_indexes
    assert "uq_crm_contacto_tenant_email" in contacto_uniques
    assert "uq_crm_contacto_campania" in contacto_campania_uniques


def test_acciones_operativas_campania() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    created = client.post("/api/crm/campanias", headers=headers, json={
        "nombre": "Campaña Operativa",
        "estado": "activa",
        "descripcion": "Base original",
    })
    campania_id = created.json()["id"]

    duplicated = client.post(f"/api/crm/campanias/{campania_id}/duplicar", headers=headers)
    assert duplicated.status_code == 201
    assert duplicated.json()["estado"] == "borrador"
    assert duplicated.json()["nombre"].startswith("Campaña Operativa (copia)")

    result = client.post(
        f"/api/crm/campanias/{campania_id}/resultado",
        headers=headers,
        json={"resultado": "Generó 14 leads calificados"},
    )
    assert result.status_code == 200
    assert result.json()["resultado"] == "Generó 14 leads calificados"

    closed = client.post(f"/api/crm/campanias/{campania_id}/cerrar", headers=headers)
    assert closed.status_code == 200
    assert closed.json()["estado"] == "finalizada"
    assert closed.json()["cerrado_por"] == "crm.test"
    assert closed.json()["cerrado_en"]


# ── Dashboard resumen ─────────────────────────────────────────────────────────

def test_crm_resumen_contadores() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    r = client.get("/api/crm/resumen", headers=headers)
    assert r.status_code == 200
    data = r.json()
    for key in ("total_contactos", "total_oportunidades", "oportunidades_abiertas",
                "actividades_pendientes", "campanias_activas"):
        assert key in data
        assert isinstance(data[key], int)
    for key in (
        "total_pipeline_monto",
        "forecast_periodo",
        "meta_ventas_periodo",
        "avance_meta_ventas",
        "monto_por_etapa",
        "embudo_comercial",
        "tasa_conversion_prospecto_cliente",
        "oportunidades_ganadas",
        "oportunidades_perdidas",
        "valor_ganado_periodo",
        "actividades_vencidas",
        "actividades_por_responsable",
        "contactos_por_fuente",
        "campanias_por_efectividad",
        "top_responsables_por_cierre",
        "tasa_cierre_por_campania",
        "origen_leads_detallado",
        "pipeline_por_sucursal",
        "pipeline_por_ejecutivo",
        "dashboard_por_asesor",
        "dashboard_por_sucursal",
        "dashboard_por_campania",
        "oportunidades_sin_movimiento",
        "scoring_leads",
        "recordatorios_seguimiento",
        "proximos_vencimientos",
        "observaciones_cronologicas",
        "historial_cambios",
    ):
        assert key in data


def test_resumen_refleja_creaciones() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    pre = client.get("/api/crm/resumen", headers=headers).json()
    client.post("/api/crm/contactos", headers=headers, json={"nombre": "Nuevo KPI"})
    post = client.get("/api/crm/resumen", headers=headers).json()

    assert post["total_contactos"] == pre["total_contactos"] + 1


def test_resumen_comercial_refleja_metricas_avanzadas() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    contacto = client.post("/api/crm/contactos", headers=headers, json={
        "nombre": "Comercial KPI",
        "email": "kpi@example.com",
        "tipo": "cliente",
        "fuente": "backend",
        "fuente_detalle": "Landing AVAN",
        "sucursal": "Centro",
    })
    cid = contacto.json()["id"]
    client.post("/api/crm/oportunidades", headers=headers, json={
        "contacto_id": cid,
        "nombre": "Abierta",
        "etapa": "negociacion",
        "valor_estimado": 15000,
        "responsable": "ejecutivo1",
        "sucursal": "Centro",
    })
    won = client.post("/api/crm/oportunidades", headers=headers, json={
        "contacto_id": cid,
        "nombre": "Ganada",
        "etapa": "cerrado_ganado",
        "valor_estimado": 22000,
        "responsable": "ejecutivo1",
        "sucursal": "Centro",
    })
    client.post("/api/crm/oportunidades", headers=headers, json={
        "contacto_id": cid,
        "nombre": "Perdida",
        "etapa": "cerrado_perdido",
        "valor_estimado": 8000,
        "responsable": "ejecutivo2",
        "sucursal": "Norte",
    })
    client.post("/api/crm/actividades", headers=headers, json={
        "contacto_id": cid,
        "titulo": "Atrasada",
        "responsable": "ejecutivo1",
        "fecha": "2025-01-01T10:00:00",
    })
    camp = client.post("/api/crm/campanias", headers=headers, json={"nombre": "Camp KPI", "estado": "activa"})
    camp_id = camp.json()["id"]
    client.post("/api/crm/campanias/contactos", headers=headers, json={
        "contacto_id": cid,
        "campania_id": camp_id,
        "estado": "convertido",
    })

    resumen = client.get("/api/crm/resumen", headers=headers).json()

    assert resumen["total_pipeline_monto"] == 15000
    assert resumen["oportunidades_ganadas"] == 1
    assert resumen["oportunidades_perdidas"] == 1
    assert resumen["actividades_vencidas"] == 1
    assert any(item["fuente"] == "backend" and item["total"] >= 1 for item in resumen["contactos_por_fuente"])
    assert any(item["origen"] == "Landing AVAN" and item["total"] >= 1 for item in resumen["origen_leads_detallado"])
    assert any(item["responsable"] == "ejecutivo1" for item in resumen["actividades_por_responsable"])
    assert any(item["nombre"] == "Camp KPI" and item["efectividad"] == 100.0 for item in resumen["campanias_por_efectividad"])
    assert any(item["responsable"] in {"crm.test", "ejecutivo1"} for item in resumen["top_responsables_por_cierre"])
    assert any(item["nombre"] == "Camp KPI" and item["tasa_cierre"] >= 0 for item in resumen["tasa_cierre_por_campania"])
    assert any(item["sucursal"] == "Centro" and item["monto"] == 15000 for item in resumen["pipeline_por_sucursal"])
    assert any(item["ejecutivo"] == "ejecutivo1" and item["monto"] == 15000 for item in resumen["pipeline_por_ejecutivo"])
    assert resumen["forecast_periodo"] >= 9000
    assert resumen["meta_ventas_periodo"] > 0
    assert resumen["avance_meta_ventas"] >= 0
    assert any(item["etapa"] == "negociacion" and item["total"] >= 1 for item in resumen["embudo_comercial"])
    assert any(item["asesor"] == "ejecutivo1" for item in resumen["dashboard_por_asesor"])
    assert any(item["sucursal"] == "Centro" for item in resumen["dashboard_por_sucursal"])
    assert any(item["nombre"] == "Camp KPI" for item in resumen["dashboard_por_campania"])
    assert resumen["scoring_leads"]
    assert resumen["proximos_vencimientos"]
    assert resumen["historial_cambios"]


def test_crm_resumen_crea_esquema_si_no_existe() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    MAIN.metadata.drop_all(bind=engine, tables=CRM_TABLES, checkfirst=True)

    response = client.get("/api/crm/resumen", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total_contactos"] == 0
    inspector = inspect(engine)
    assert inspector.has_table("crm_eventos")


def test_crm_resumen_tolera_fechas_nulas_heredadas(monkeypatch: pytest.MonkeyPatch) -> None:
    from types import SimpleNamespace

    from fastapi_modulo.modulos.crm.servicios import dashboard_service

    class FakeQuery:
        def __init__(self, rows):
            self.rows = rows

        def filter(self, *_args, **_kwargs):
            return self

        def order_by(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

        def all(self):
            return self.rows

    class FakeSession:
        def __init__(self, mapping):
            self.mapping = mapping

        def query(self, model):
            return FakeQuery(self.mapping.get(model, []))

        def close(self):
            return None

    contacto = SimpleNamespace(
        id=1,
        tenant_id="test",
        nombre="Legacy CRM",
        tipo="prospecto",
        fuente="manual",
        fuente_detalle="",
        lead_score=0,
        sucursal="",
    )
    oportunidad = SimpleNamespace(
        id=10,
        tenant_id="test",
        contacto_id=1,
        nombre="Legacy Deal",
        etapa="negociacion",
        valor_estimado=5000,
        probabilidad=0,
        responsable="",
        asignado_a="",
        sucursal="",
        ultimo_movimiento_en=None,
        actualizado_en=None,
        creado_en=None,
    )
    nota_nula = SimpleNamespace(
        creado_en=None,
        contenido="Nota heredada",
        autor="",
        creado_por="",
    )
    nota_reciente = SimpleNamespace(
        creado_en=datetime.utcnow(),
        contenido="Nota reciente",
        autor="",
        creado_por="",
    )
    actividad = SimpleNamespace(
        id=100,
        titulo="Seguimiento",
        fecha=None,
        completada=False,
        responsable="",
        asignado_a="",
    )
    fake_db = FakeSession({
        CrmContacto: [contacto],
        CrmOportunidad: [oportunidad],
        CrmActividad: [actividad],
        CrmCampania: [],
        CrmContactoCampania: [],
        CrmNota: [nota_nula, nota_reciente],
        CrmEvento: [],
    })

    monkeypatch.setattr(dashboard_service, "ensure_crm_schema", lambda: None)
    monkeypatch.setattr(dashboard_service, "get_db", lambda: fake_db)

    data = dashboard_service.get_crm_resumen("test")

    assert data["total_contactos"] == 1
    assert any(item["nombre"] == "Legacy Deal" for item in data["oportunidades_sin_movimiento"])
    assert data["observaciones_cronologicas"][0]["descripcion"] == "Nota reciente"


def test_crm_html_incluye_pipeline_kanban() -> None:
    client = _build_client()
    response = client.get("/crm", headers=_auth("usuario", "CRM"))
    assert response.status_code == 200
    assert "crm-oportunidades-kanban" in response.text


# ── Admin omite permiso CRM ───────────────────────────────────────────────────

def test_admin_can_access_crm_without_checkbox() -> None:
    client = _build_client()
    r = client.get("/api/crm/contactos", headers=_auth("administrador"))
    assert r.status_code == 200


def test_tenant_isolation_contactos() -> None:
    client = _build_client()
    headers_a = _auth_tenant("tenant-a", "usuario", "CRM")
    headers_b = _auth_tenant("tenant-b", "usuario", "CRM")

    created = client.post("/api/crm/contactos", headers=headers_a, json={"nombre": "Tenant A"})
    assert created.status_code == 201

    list_a = client.get("/api/crm/contactos", headers=headers_a)
    list_b = client.get("/api/crm/contactos", headers=headers_b)

    assert len(list_a.json()) == 1
    assert list_b.json() == []


def test_duplicate_email_allowed_across_tenants() -> None:
    client = _build_client()
    headers_a = _auth_tenant("tenant-a", "usuario", "CRM")
    headers_b = _auth_tenant("tenant-b", "usuario", "CRM")

    first = client.post("/api/crm/contactos", headers=headers_a, json={"nombre": "Uno", "email": "shared@example.com"})
    second = client.post("/api/crm/contactos", headers=headers_b, json={"nombre": "Dos", "email": "shared@example.com"})

    assert first.status_code == 201
    assert second.status_code == 201


def test_tenant_isolation_campanias() -> None:
    client = _build_client()
    headers_a = _auth_tenant("tenant-a", "usuario", "CRM")
    headers_b = _auth_tenant("tenant-b", "usuario", "CRM")

    created = client.post("/api/crm/campanias", headers=headers_a, json={"nombre": "Camp Tenant A"})
    assert created.status_code == 201

    list_a = client.get("/api/crm/campanias", headers=headers_a)
    list_b = client.get("/api/crm/campanias", headers=headers_b)

    assert len(list_a.json()) == 1
    assert list_b.json() == []


def test_contacto_guarda_trazabilidad_y_evento() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    created = client.post("/api/crm/contactos", headers=headers, json={"nombre": "Traza Contacto"})
    assert created.status_code == 201
    assert created.json()["creado_por"] == "crm.test"
    assert created.json()["actualizado_por"] == "crm.test"

    eventos = client.get("/api/crm/eventos?entidad=contacto", headers=headers)
    assert eventos.status_code == 200
    assert any(evt["tipo_evento"] == "contacto_creado" for evt in eventos.json())


def test_oportunidad_cierre_registra_trazabilidad_y_evento() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    contacto = client.post("/api/crm/contactos", headers=headers, json={"nombre": "Traza Oportunidad"})
    cid = contacto.json()["id"]
    created = client.post("/api/crm/oportunidades", headers=headers, json={"contacto_id": cid, "nombre": "Oportunidad X"})
    oid = created.json()["id"]

    closed = client.put(f"/api/crm/oportunidades/{oid}", headers=headers, json={"etapa": "cerrado_ganado"})
    assert closed.status_code == 200
    assert closed.json()["cerrado_por"] == "crm.test"

    eventos = client.get("/api/crm/eventos?entidad=oportunidad&entidad_id=" + str(oid), headers=headers)
    tipos = {evt["tipo_evento"] for evt in eventos.json()}
    assert "oportunidad_etapa_cambiada" in tipos
    assert "oportunidad_cerrada" in tipos


def test_actividad_y_campania_generan_eventos() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    contacto = client.post("/api/crm/contactos", headers=headers, json={"nombre": "Evento Multiples"})
    cid = contacto.json()["id"]
    actividad = client.post("/api/crm/actividades", headers=headers, json={"contacto_id": cid, "titulo": "Seguimiento"})
    assert actividad.status_code == 201
    campania = client.post("/api/crm/campanias", headers=headers, json={"nombre": "Camp Evento"})
    camp_id = campania.json()["id"]
    union = client.post("/api/crm/campanias/contactos", headers=headers, json={"contacto_id": cid, "campania_id": camp_id})
    assert union.status_code == 201

    eventos = client.get("/api/crm/eventos", headers=headers)
    tipos = {evt["tipo_evento"] for evt in eventos.json()}
    assert "actividad_creada" in tipos
    assert "contacto_incorporado_a_campania" in tipos


def test_acciones_operativas_generan_eventos() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    contacto = client.post("/api/crm/contactos", headers=headers, json={"nombre": "Eventos Acciones"})
    cid = contacto.json()["id"]
    client.post(f"/api/crm/contactos/{cid}/convertir-cliente", headers=headers)

    oportunidad = client.post("/api/crm/oportunidades", headers=headers, json={"contacto_id": cid, "nombre": "Evento oportunidad"})
    oid = oportunidad.json()["id"]
    client.post(f"/api/crm/oportunidades/{oid}/ganar", headers=headers)

    actividad = client.post("/api/crm/actividades", headers=headers, json={"contacto_id": cid, "titulo": "Evento actividad"})
    aid = actividad.json()["id"]
    client.post(f"/api/crm/actividades/{aid}/reprogramar", headers=headers, json={"fecha": "2027-02-10T08:00:00"})

    campania = client.post("/api/crm/campanias", headers=headers, json={"nombre": "Evento campaña"})
    camp_id = campania.json()["id"]
    client.post(f"/api/crm/campanias/{camp_id}/duplicar", headers=headers)
    client.post(f"/api/crm/campanias/{camp_id}/resultado", headers=headers, json={"resultado": "Evento registrado"})
    client.post(f"/api/crm/campanias/{camp_id}/cerrar", headers=headers)

    eventos = client.get("/api/crm/eventos", headers=headers)
    tipos = {evt["tipo_evento"] for evt in eventos.json()}
    assert "contacto_convertido_a_cliente" in tipos
    assert "oportunidad_cerrada" in tipos
    assert "actividad_reprogramada" in tipos
    assert "campania_duplicada" in tipos
    assert "campania_resultado_registrado" in tipos
    assert "campania_cerrada" in tipos


def test_seguimiento_unifica_notas_e_historial() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    contacto = client.post("/api/crm/contactos", headers=headers, json={"nombre": "Seguimiento Lead"})
    cid = contacto.json()["id"]
    oportunidad = client.post("/api/crm/oportunidades", headers=headers, json={"contacto_id": cid, "nombre": "Seguimiento Oportunidad"})
    oid = oportunidad.json()["id"]
    nota = client.post("/api/crm/notas", headers=headers, json={"contacto_id": cid, "oportunidad_id": oid, "contenido": "Llamada realizada", "autor": "crm.test"})
    assert nota.status_code == 201
    etapa = client.post(f"/api/crm/oportunidades/{oid}/etapa", headers=headers, json={"etapa": "propuesta"})
    assert etapa.status_code == 200

    seguimiento = client.get(f"/api/crm/seguimiento?oportunidad_id={oid}", headers=headers)
    assert seguimiento.status_code == 200
    tipos = {item["tipo"] for item in seguimiento.json()}
    detalles = {item["detalle"] for item in seguimiento.json()}
    assert "nota" in tipos
    assert "evento" in tipos
    assert "oportunidad_etapa_cambiada" in detalles
