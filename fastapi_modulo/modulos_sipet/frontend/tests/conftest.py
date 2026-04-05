"""
tests/conftest.py  —  Frontend module test fixtures
─────────────────────────────────────────────────────────────────────────────
Fixtures compartidos para las pruebas del módulo frontend.

• Usa SQLite :memory: para aislar cada test de la BD real.
• Parchea core_db para que el store use el engine in-memory.
• Parchea servicios externos (auth, session, ui_shell) con stubs mínimos.
"""

from __future__ import annotations

import os
import sys
import types
from typing import Generator

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("REDIS_URL", "")          # sin Redis en tests
os.environ.setdefault("FRONTEND_LEGACY_MIGRATION_ENABLED", "false")

# ── Stubs de módulos externos que el store / servicios importan ───────────────

def _install_core_db_stub(engine):
    """Reemplaza core_db con un stub que usa el engine SQLite in-memory."""
    Session = sessionmaker(bind=engine)

    stub = types.ModuleType("fastapi_modulo.core.db")
    stub.MAIN = _real_MAIN()
    stub.get_engine_for_host          = lambda host=None: engine
    stub.get_session_factory_for_host = lambda host=None: Session
    stub.get_request_host             = lambda: "test"
    stub.get_current_database_info    = lambda host=None: {"url": str(engine.url)}
    sys.modules["fastapi_modulo.core.db"] = stub
    return stub


def _real_MAIN():
    from fastapi_modulo.core.db import MAIN
    return MAIN


def _stub_auth_service():
    stub = types.ModuleType("fastapi_modulo.modulos_sipet.web.servicios.auth_service")
    stub.get_session_local    = lambda: (lambda: None)
    stub.find_user_by_login   = lambda db, u: None
    stub.resolve_post_login_redirect = lambda db, role, uid: "/inicio"
    sys.modules["fastapi_modulo.modulos_sipet.web.servicios.auth_service"] = stub


def _stub_session_service():
    stub = types.ModuleType("fastapi_modulo.modulos_sipet.web.servicios.session_service")
    stub.AUTH_COOKIE_NAME   = "session"
    stub.read_session_cookie = lambda token: None
    sys.modules["fastapi_modulo.modulos_sipet.web.servicios.session_service"] = stub


def _stub_access_service():
    stub = types.ModuleType("fastapi_modulo.modulos_sipet.web.servicios.access_service")
    stub.require_screen_access    = lambda request, screen, detail="": None
    stub.get_user_backend_roles   = lambda request, username: []
    stub.get_user_app_access_level= lambda request, app: "full_access"
    stub.normalize_role_name      = lambda role: (role or "").strip().lower()
    sys.modules["fastapi_modulo.modulos_sipet.web.servicios.access_service"] = stub


def _stub_ui_shell_service():
    stub = types.ModuleType("fastapi_modulo.modulos_sipet.web.servicios.ui_shell_service")
    stub.get_colores_context = lambda: {"sidebar-bottom": "#0f172a", "primary": "#14532d"}
    sys.modules["fastapi_modulo.modulos_sipet.web.servicios.ui_shell_service"] = stub


def _stub_login_identity_service():
    stub = types.ModuleType("fastapi_modulo.modulos_sipet.web.servicios.login_identity_service")
    stub._load_login_identity = lambda: {"menu_position": "left", "login_favicon_url": ""}
    sys.modules["fastapi_modulo.modulos_sipet.web.servicios.login_identity_service"] = stub


def _stub_builder_access():
    stub = types.ModuleType("fastapi_modulo.modulos_sipet.frontend.servicios.builder_access")
    stub.require_write = lambda request: None
    sys.modules["fastapi_modulo.modulos_sipet.frontend.servicios.builder_access"] = stub


# Install lightweight stubs once at collection time (no Redis, no real DB)
_stub_auth_service()
_stub_session_service()
_stub_access_service()
_stub_ui_shell_service()
_stub_login_identity_service()


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def mem_engine():
    """SQLite in-memory engine con todas las tablas del módulo frontend."""
    from fastapi_modulo.core.db import MAIN
    from fastapi_modulo.modulos_sipet.frontend.modelos.frontend_db_models import (
        FrontendBrand,
        FrontendContact,
        FrontendGalleryImage,
        FrontendPage,
        FrontendPageVersion,
        FrontendTasa,
    )
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    MAIN.metadata.create_all(
        bind=engine,
        tables=[
            FrontendPage.__table__,
            FrontendPageVersion.__table__,
            FrontendContact.__table__,
            FrontendBrand.__table__,
            FrontendTasa.__table__,
            FrontendGalleryImage.__table__,
        ],
    )
    return engine


@pytest.fixture()
def db_session(mem_engine):
    """Sesión SQLAlchemy sobre el engine in-memory."""
    Session = sessionmaker(bind=mem_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture()
def patched_store(mem_engine, monkeypatch):
    """
    Parcha core_db dentro del store para que use el engine in-memory.
    Invalida la caché interna del store para que use el nuevo engine.
    """
    Session = sessionmaker(bind=mem_engine)

    import fastapi_modulo.modulos_sipet.frontend.modelos.frontend_store as store_mod
    monkeypatch.setattr(
        store_mod.core_db, "get_engine_for_host",
        lambda host=None: mem_engine, raising=False
    )
    monkeypatch.setattr(
        store_mod.core_db, "get_session_factory_for_host",
        lambda host=None: Session, raising=False
    )
    monkeypatch.setattr(
        store_mod.core_db, "get_request_host",
        lambda: "test", raising=False
    )
    monkeypatch.setattr(
        store_mod.core_db, "get_current_database_info",
        lambda host=None: {"url": str(mem_engine.url)}, raising=False
    )
    # pre-mark DB ready so _ensure_frontend_storage_ready skips create_all
    store_mod._ready_databases.add(str(mem_engine.url))
    yield store_mod
    store_mod._ready_databases.discard(str(mem_engine.url))


@pytest.fixture()
def gallery_app(patched_store, tmp_path, monkeypatch):
    """TestClient apuntando al gallery_controller con galería en tmp_path."""
    _stub_builder_access()

    gallery_dir = str(tmp_path / "gallery")
    os.makedirs(gallery_dir, exist_ok=True)

    import fastapi_modulo.modulos_sipet.frontend.controladores.gallery_controller as gc
    monkeypatch.setattr(gc, "_GALLERY_DIR", gallery_dir)

    # stub cache_service to be a no-op
    import fastapi_modulo.modulos_sipet.frontend.servicios.cache_service as cs
    monkeypatch.setattr(cs, "get", lambda key: None)
    monkeypatch.setattr(cs, "set", lambda key, value, ttl=None: None)
    monkeypatch.setattr(cs, "delete", lambda *keys: None)

    app = FastAPI()

    @app.middleware("http")
    async def inject_user(request: Request, call_next):
        request.state.user_name = "testuser"
        request.state.user_role = "administrador"
        return await call_next(request)

    app.include_router(gc.router)
    return TestClient(app, raise_server_exceptions=True)
