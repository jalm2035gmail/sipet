from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from scripts.validate_module_architecture import validate_module
import fastapi_modulo.modulos.referidos.controladores.referidos as referidos_controller
from fastapi_modulo.modulos.referidos.controladores.referidos import router


MODULE_ROOT = Path(__file__).resolve().parents[1]


def test_referidos_passes_architecture_validation() -> None:
    result = validate_module(MODULE_ROOT)

    assert result.ok is True


def test_referidos_controller_uses_public_web_api() -> None:
    source = (MODULE_ROOT / "controladores" / "referidos.py").read_text(encoding="utf-8")

    assert "from fastapi_modulo.modulos_sipet.web import render_backend_page_html" in source
    assert "modulos_sipet.web.servicios.module_tools" not in source
    assert "multitienda_store_id" not in source


def test_referidos_view_and_js_do_not_depend_on_multitienda_store_contract() -> None:
    view_source = (MODULE_ROOT / "vistas" / "referidos.html").read_text(encoding="utf-8")
    js_source = (MODULE_ROOT / "static" / "js" / "referidos.js").read_text(encoding="utf-8")

    assert "multitienda_stores" not in view_source
    assert "multitienda_store_id" not in view_source
    assert "programStoreSelect" not in js_source
    assert "multitienda_store_id" not in js_source


def test_referidos_router_imports_successfully() -> None:
    paths = {getattr(route, "path", "") for route in router.routes}

    assert "/referidos" in paths
    assert "/api/referidos/crear" in paths


def test_referidos_page_does_not_require_kwargs_query_param(monkeypatch) -> None:
    app = FastAPI()
    app.include_router(router)
    monkeypatch.setattr(referidos_controller, "get_dashboard_stats", lambda db: {"total": 0, "by_state": {}})
    monkeypatch.setattr(referidos_controller, "list_referidos", lambda db, limit=50, **kwargs: [])
    monkeypatch.setattr(referidos_controller, "list_referentes", lambda db, limit=200, **kwargs: [])
    monkeypatch.setattr(referidos_controller, "list_incentivos", lambda db, **kwargs: [])
    monkeypatch.setattr(referidos_controller, "get_configuracion", lambda db: None)

    client = TestClient(app)
    response = client.get("/referidos")

    assert response.status_code == 200
    assert "Field required" not in response.text
