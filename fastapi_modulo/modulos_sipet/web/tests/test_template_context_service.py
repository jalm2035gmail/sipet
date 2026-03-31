from __future__ import annotations

import sys
import types

import pytest
from fastapi import Request

import fastapi_modulo.modulos_sipet.web.servicios.template_context_service as template_context_service
from fastapi_modulo.modulos_sipet.web.servicios.template_context_service import (
    build_backend_context,
    build_login_context,
    build_not_found_context,
)

fake_main = types.ModuleType("fastapi_modulo.main")
fake_main.get_colores_context = lambda: {"sidebar-top": "#ffffff"}
sys.modules["fastapi_modulo.main"] = fake_main


def _build_request() -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/backend/demo",
        "headers": [(b"host", b"example.test")],
        "query_string": b"",
        "scheme": "https",
        "server": ("example.test", 443),
        "client": ("127.0.0.1", 1234),
    }
    request = Request(scope)
    request._cookies = {"csrf_token": "csrf-demo"}
    request.state.tenant_id = "tenant-demo"
    request.state.user_role = "superadmin"
    request.state.user_name = "alice"
    return request


def test_build_login_context_includes_request_and_error() -> None:
    context = build_login_context(_build_request(), title="Acceso", login_error="Credenciales inválidas")
    assert context["title"] == "Acceso"
    assert context["login_error"] == "Credenciales inválidas"
    assert context["request"].url.path == "/backend/demo"


def test_build_login_context_falls_back_to_query_error() -> None:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/backend/login",
        "headers": [(b"host", b"example.test")],
        "query_string": b"error=Datos+incorrectos&usuario=dumas",
        "scheme": "https",
        "server": ("example.test", 443),
        "client": ("127.0.0.1", 1234),
    }
    request = Request(scope)
    request._cookies = {}

    context = build_login_context(request, title="Acceso")

    assert context["login_error"] == "Datos incorrectos"


def test_build_not_found_context_includes_branding_keys() -> None:
    context = build_not_found_context(_build_request(), title="No existe")
    assert context["title"] == "No existe"
    assert "app_favicon_url" in context
    assert "company_logo_url" in context


def test_build_backend_context_populates_shared_shell_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(template_context_service, "get_backend_catalog_context", lambda _request: {"sidebar_modules": []})
    context = build_backend_context(
        _build_request(),
        title="Dashboard",
        description="Resumen",
        content="<section>ok</section>",
    )
    assert context["page_title"] == "Dashboard"
    assert context["page_description"] == "Resumen"
    assert context["content"] == "<section>ok</section>"
    assert context["csrf_token"] == "csrf-demo"
    assert context["is_superadmin_user"] is True
