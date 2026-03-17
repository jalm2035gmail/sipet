from __future__ import annotations

import os
import sys
import types

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SQLITE_DB_PATH", "/tmp/sipet_crm_phase6.sqlite3")
pytestmark = pytest.mark.filterwarnings("ignore:The 'app' shortcut is now deprecated.*:DeprecationWarning")

fake_main = types.ModuleType("fastapi_modulo.main")


def _fake_render_backend_page(
    request: Request,
    title: str,
    description: str = "",
    content: str = "",
    **_: object,
) -> HTMLResponse:
    return HTMLResponse(content=f"<html><body>{content}</body></html>")


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

from fastapi_modulo.core.db import MAIN, engine  # noqa: E402
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


def _build_client() -> TestClient:
    app = FastAPI()

    @app.middleware("http")
    async def inject_test_session(request: Request, call_next):
        request.state.user_name = request.headers.get("x-user", "crm.test")
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


def setup_function() -> None:
    MAIN.metadata.drop_all(bind=engine, tables=CRM_TABLES, checkfirst=True)
    MAIN.metadata.create_all(bind=engine, tables=CRM_TABLES, checkfirst=True)


def _crear_contacto(client: TestClient, headers: dict[str, str], nombre: str = "Contacto Base") -> int:
    response = client.post("/api/crm/contactos", headers=headers, json={"nombre": nombre, "email": f"{nombre.replace(' ', '').lower()}@example.com"})
    assert response.status_code == 201
    return response.json()["id"]


def test_validacion_duplicado_email() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    first = client.post("/api/crm/contactos", headers=headers, json={"nombre": "Uno", "email": "dup@example.com"})
    second = client.post("/api/crm/contactos", headers=headers, json={"nombre": "Dos", "email": "dup@example.com"})

    assert first.status_code == 201
    assert second.status_code == 409


def test_validacion_probabilidad_invalida() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")
    contacto_id = _crear_contacto(client, headers, "Probabilidad Contacto")

    response = client.post("/api/crm/oportunidades", headers=headers, json={
        "contacto_id": contacto_id,
        "nombre": "Probabilidad inválida",
        "probabilidad": -1,
    })
    assert response.status_code == 422


def test_validacion_valor_estimado_invalido() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")
    contacto_id = _crear_contacto(client, headers, "Valor Contacto")

    response = client.post("/api/crm/oportunidades", headers=headers, json={
        "contacto_id": contacto_id,
        "nombre": "Valor inválido",
        "valor_estimado": -10,
    })
    assert response.status_code == 422


def test_cambio_de_etapa_por_endpoint_dedicado() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")
    contacto_id = _crear_contacto(client, headers, "Etapa Contacto")
    oportunidad = client.post("/api/crm/oportunidades", headers=headers, json={"contacto_id": contacto_id, "nombre": "Etapa"})
    oportunidad_id = oportunidad.json()["id"]

    response = client.post(f"/api/crm/oportunidades/{oportunidad_id}/etapa", headers=headers, json={"etapa": "propuesta"})
    assert response.status_code == 200
    assert response.json()["etapa"] == "propuesta"


def test_campania_con_fechas_invalidas() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")

    response = client.post("/api/crm/campanias", headers=headers, json={
        "nombre": "Fechas invalidas granular",
        "fecha_inicio": "2026-04-30",
        "fecha_fin": "2026-04-01",
    })
    assert response.status_code == 422


def test_agregar_mismo_contacto_a_campania_dos_veces() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")
    contacto_id = _crear_contacto(client, headers, "Camp Doble")
    campania_id = client.post("/api/crm/campanias", headers=headers, json={"nombre": "Campaña Doble"}).json()["id"]

    payload = {"contacto_id": contacto_id, "campania_id": campania_id, "estado": "pendiente"}
    first = client.post("/api/crm/campanias/contactos", headers=headers, json=payload)
    second = client.post("/api/crm/campanias/contactos", headers=headers, json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_filtrado_por_etapa() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")
    contacto_id = _crear_contacto(client, headers, "Filtro Etapa")
    client.post("/api/crm/oportunidades", headers=headers, json={"contacto_id": contacto_id, "nombre": "Op A", "etapa": "negociacion"})
    client.post("/api/crm/oportunidades", headers=headers, json={"contacto_id": contacto_id, "nombre": "Op B", "etapa": "cerrado_ganado"})

    response = client.get("/api/crm/oportunidades?etapa=cerrado_ganado", headers=headers)
    assert response.status_code == 200
    assert response.json()
    assert all(item["etapa"] == "cerrado_ganado" for item in response.json())


def test_filtrado_por_estado_de_campania() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")
    client.post("/api/crm/campanias", headers=headers, json={"nombre": "Camp Activa", "estado": "activa"})
    client.post("/api/crm/campanias", headers=headers, json={"nombre": "Camp Borrador", "estado": "borrador"})

    response = client.get("/api/crm/campanias?estado=activa", headers=headers)
    assert response.status_code == 200
    assert response.json()
    assert all(item["estado"] == "activa" for item in response.json())


def test_eliminacion_en_cascada() -> None:
    client = _build_client()
    headers = _auth("usuario", "CRM")
    contacto_id = _crear_contacto(client, headers, "Cascade Granular")
    oportunidad_id = client.post("/api/crm/oportunidades", headers=headers, json={"contacto_id": contacto_id, "nombre": "Op Cascade"}).json()["id"]
    client.post("/api/crm/actividades", headers=headers, json={"contacto_id": contacto_id, "oportunidad_id": oportunidad_id, "titulo": "Act cascade"})
    client.post("/api/crm/notas", headers=headers, json={"contacto_id": contacto_id, "oportunidad_id": oportunidad_id, "contenido": "Nota cascade"})

    deleted = client.delete(f"/api/crm/contactos/{contacto_id}", headers=headers)
    assert deleted.status_code == 200
    assert client.get("/api/crm/oportunidades", headers=headers).json() == []
    assert client.get("/api/crm/actividades", headers=headers).json() == []
    assert client.get(f"/api/crm/notas?contacto_id={contacto_id}", headers=headers).json() == []


def test_seguridad_por_permisos_en_endpoints_clave() -> None:
    client = _build_client()

    contactos = client.get("/api/crm/contactos")
    crear_oportunidad = client.post("/api/crm/oportunidades", json={"contacto_id": 1, "nombre": "No autorizado"})
    campanias = client.get("/api/crm/campanias")
    actividades = client.get("/api/crm/actividades")

    assert contactos.status_code == 403
    assert crear_oportunidad.status_code == 403
    assert campanias.status_code == 403
    assert actividades.status_code == 403
