from __future__ import annotations

import sys
import types
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from fastapi_modulo.core.db import MAIN
from fastapi_modulo.modulos_sipet.web.modelos.db_models import (
    WebLoginAttempt,
    WebMfaChallenge,
    WebSecurityEvent,
    WebUserPreference,
    WebUserSession,
)
from fastapi_modulo.modulos_sipet.web.repositorios import core_repository
from fastapi_modulo.modulos_sipet.web.servicios import ui_shell_service
from fastapi_modulo.modulos_sipet.web.servicios.session_service import build_password_fingerprint, build_session_cookie, read_session_cookie


def test_web_models_create_tables() -> None:
    engine = create_engine("sqlite:///:memory:")
    MAIN.metadata.create_all(
        bind=engine,
        tables=[
            WebLoginAttempt.__table__,
            WebUserSession.__table__,
            WebMfaChallenge.__table__,
            WebSecurityEvent.__table__,
            WebUserPreference.__table__,
        ],
        checkfirst=True,
    )
    assert WebLoginAttempt.__table__.name in MAIN.metadata.tables
    assert WebUserSession.__table__.name in MAIN.metadata.tables
    assert WebMfaChallenge.__table__.name in MAIN.metadata.tables
    assert WebSecurityEvent.__table__.name in MAIN.metadata.tables
    assert WebUserPreference.__table__.name in MAIN.metadata.tables


def test_session_cookie_roundtrip_includes_jti() -> None:
    token = build_session_cookie(
        "usuario",
        "administrador",
        "default",
        "abc123",
        password_fingerprint=build_password_fingerprint("hash-demo"),
    )
    original_module = sys.modules.get("fastapi_modulo.modulos_sipet.web.repositorios.security_repository")
    try:
        fake_repo = types.ModuleType("fastapi_modulo.modulos_sipet.web.repositorios.security_repository")
        fake_repo.is_session_active = lambda _jti: True
        sys.modules["fastapi_modulo.modulos_sipet.web.repositorios.security_repository"] = fake_repo
        payload = read_session_cookie(token)
    finally:
        if original_module is None:
            sys.modules.pop("fastapi_modulo.modulos_sipet.web.repositorios.security_repository", None)
        else:
            sys.modules["fastapi_modulo.modulos_sipet.web.repositorios.security_repository"] = original_module
    assert payload is not None
    assert payload["session_jti"] == "abc123"
    assert payload["password_fingerprint"] == build_password_fingerprint("hash-demo")


def test_find_user_by_login_returns_none_when_schema_is_unavailable() -> None:
    class BrokenQuery:
        def filter(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

        def first(self):
            raise OperationalError("SELECT ...", {}, Exception("missing column"))

        def all(self):
            raise OperationalError("SELECT ...", {}, Exception("missing column"))

    fake_db = SimpleNamespace(query=lambda *_args, **_kwargs: BrokenQuery())

    assert core_repository.find_user_by_login(fake_db, login_value="admin", login_hash="hash") is None
    assert core_repository.find_user_by_id(fake_db, 1) is None
    assert core_repository.list_color_values(fake_db) == {}


def test_get_colores_context_uses_defaults_when_table_is_unavailable(monkeypatch) -> None:
    class BrokenSession:
        def query(self, *_args, **_kwargs):
            class BrokenQuery:
                def all(self):
                    raise OperationalError("SELECT ...", {}, Exception("missing table"))

            return BrokenQuery()

        def close(self):
            return None

    monkeypatch.setattr(ui_shell_service, "SessionLocal", lambda: BrokenSession())

    context = ui_shell_service.get_colores_context()

    assert isinstance(context, dict)
    assert context
