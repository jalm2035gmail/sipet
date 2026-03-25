from __future__ import annotations

import os
import sys
import types
from pathlib import Path
from typing import Callable, Iterable

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

TEST_DB_PATH = Path("/tmp") / f"sipet_intelicoop_tests_{os.getpid()}.sqlite3"
os.environ["APP_ENV"] = "test"
os.environ["SQLITE_DB_PATH"] = str(TEST_DB_PATH)


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
        "administrador",
        "admin",
        "superadministrador",
        "superadmin",
    }


fake_main.render_backend_page = _fake_render_backend_page
fake_main._get_user_app_access = _fake_get_user_app_access
fake_main.is_admin_or_superadmin = _fake_is_admin_or_superadmin
sys.modules["fastapi_modulo.main"] = fake_main


import fastapi_modulo.core.db as core_db


TEST_DB_URL = f"sqlite:///{TEST_DB_PATH}"
TEST_ENGINE = core_db.create_engine_for_url(TEST_DB_URL)
TEST_SESSION_FACTORY = sessionmaker(bind=TEST_ENGINE, autocommit=False, autoflush=False)

core_db.get_engine_for_host = lambda host=None: TEST_ENGINE
core_db.get_session_factory_for_host = lambda host=None: TEST_SESSION_FACTORY
core_db.get_current_engine = lambda: TEST_ENGINE
core_db.engine = TEST_ENGINE


@pytest.fixture
def fake_render_backend_page() -> Callable[..., HTMLResponse]:
    return _fake_render_backend_page


@pytest.fixture
def build_client() -> Callable[[object | None], TestClient]:
    from fastapi_modulo.modulos.intelicoop.controladores.intelicoop import require_intelicoop_access, router

    def _factory(access_override: object | None = None) -> TestClient:
        app = FastAPI()

        @app.middleware("http")
        async def inject_test_session(request: Request, call_next):
            request.state.user_name = request.headers.get("x-user", "tester")
            request.state.user_role = request.headers.get("x-role", "usuario")
            request.state.tenant_id = "test"
            return await call_next(request)

        app.include_router(router)
        app.dependency_overrides[require_intelicoop_access] = access_override or (lambda: None)
        return TestClient(app)

    return _factory


@pytest.fixture
def strict_intelicoop_access() -> Callable[[Request], None]:
    def _fake_require_access(request: Request) -> None:
        role = request.headers.get("x-role", "").strip().lower()
        if role in {"admin", "administrador", "superadmin", "superadministrador"}:
            return
        raw = request.headers.get("x-app-access", "")
        access = {item.strip() for item in raw.split(",") if item.strip()}
        if "Intelicoop" not in access:
            raise HTTPException(status_code=403, detail="Acceso restringido a Intelicoop")

    return _fake_require_access


@pytest.fixture
def auth_headers() -> Callable[..., dict[str, str]]:
    def _factory(*access: str, role: str = "admin", user: str = "tester") -> dict[str, str]:
        headers = {"x-role": role, "x-user": user}
        if access:
            headers["x-app-access"] = ",".join(access)
        return headers

    return _factory


@pytest.fixture
def reset_tables() -> Callable[[Iterable[object]], None]:
    from fastapi_modulo.core.db import MAIN, engine

    def _reset(tables: Iterable[object]) -> None:
        table_list = list(tables)
        engine.dispose()
        db_path = getattr(engine.url, "database", None)
        if db_path:
            db_file = Path(db_path)
            for suffix in ("", "-wal", "-shm", "-journal"):
                candidate = Path(f"{db_file}{suffix}") if suffix else db_file
                if candidate.exists():
                    candidate.unlink()
        try:
            from fastapi_modulo.modulos.intelicoop.modelos import store_legacy

            store_legacy._SCHEMA_READY_HOSTS.clear()
        except Exception:
            pass
        MAIN.metadata.create_all(bind=engine, tables=table_list, checkfirst=True)

    return _reset
