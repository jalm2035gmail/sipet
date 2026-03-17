from __future__ import annotations

import os
import sys
import types
from collections.abc import Callable

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient

os.environ.setdefault("APP_ENV", "test")

fake_main = types.ModuleType("fastapi_modulo.main")


def _fake_render_backend_page(
    request: Request,
    title: str,
    description: str = "",
    content: str = "",
    **_: object,
) -> HTMLResponse:
    return HTMLResponse(f"<html><title>{title}</title><body>{content}</body></html>")


def _fake_get_user_app_access(request: Request) -> list[str]:
    raw = request.headers.get("x-app-access", "")
    return [item.strip() for item in raw.split(",") if item.strip()]


def _fake_is_admin_or_superadmin(request: Request) -> bool:
    return getattr(request.state, "user_role", "").strip().lower() in {"administrador", "admin", "superadmin"}


def _fake_build_view_buttons_html(_view_buttons: object = None) -> str:
    return ""


def _fake_get_colores_context() -> dict[str, str]:
    return {
        "primary": "#14532d",
        "secondary": "#0f172a",
    }


fake_main.render_backend_page = _fake_render_backend_page
fake_main._get_user_app_access = _fake_get_user_app_access
fake_main.is_admin_or_superadmin = _fake_is_admin_or_superadmin
fake_main.build_view_buttons_html = _fake_build_view_buttons_html
fake_main.get_colores_context = _fake_get_colores_context
sys.modules["fastapi_modulo.main"] = fake_main


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"x-role": "admin"}


@pytest.fixture
def tenant_headers(auth_headers: dict[str, str]) -> dict[str, str]:
    return {**auth_headers, "x-tenant-id": "tenant-test"}


@pytest.fixture
def app_factory() -> Callable[..., FastAPI]:
    from fastapi_modulo.modulos_sipet.modulo_base.controladores.modulo_base import router

    def _factory(*, user_role: str = "usuario", tenant_id: str = "test") -> FastAPI:
        app = FastAPI()

        @app.middleware("http")
        async def inject_context(request: Request, call_next):
            request.state.user_role = request.headers.get("x-role", user_role)
            request.state.tenant_id = request.headers.get("x-tenant-id", tenant_id)
            return await call_next(request)

        app.include_router(router)
        return app

    return _factory


@pytest.fixture
def client_factory(app_factory: Callable[..., FastAPI]) -> Callable[..., TestClient]:
    def _factory(*, user_role: str = "usuario", tenant_id: str = "test") -> TestClient:
        return TestClient(app_factory(user_role=user_role, tenant_id=tenant_id))

    return _factory


@pytest.fixture
def client(client_factory: Callable[..., TestClient]) -> TestClient:
    return client_factory()
