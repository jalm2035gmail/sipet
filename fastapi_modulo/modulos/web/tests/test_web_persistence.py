from __future__ import annotations

import sys
import types

from sqlalchemy import create_engine

from fastapi_modulo.db import MAIN
from fastapi_modulo.modulos.web.modelos.db_models import (
    WebLoginAttempt,
    WebMfaChallenge,
    WebSecurityEvent,
    WebUserPreference,
    WebUserSession,
)
from fastapi_modulo.modulos.web.servicios.session_service import build_password_fingerprint, build_session_cookie, read_session_cookie


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
    original_module = sys.modules.get("fastapi_modulo.modulos.web.repositorios.security_repository")
    try:
        fake_repo = types.ModuleType("fastapi_modulo.modulos.web.repositorios.security_repository")
        fake_repo.is_session_active = lambda _jti: True
        sys.modules["fastapi_modulo.modulos.web.repositorios.security_repository"] = fake_repo
        payload = read_session_cookie(token)
    finally:
        if original_module is None:
            sys.modules.pop("fastapi_modulo.modulos.web.repositorios.security_repository", None)
        else:
            sys.modules["fastapi_modulo.modulos.web.repositorios.security_repository"] = original_module
    assert payload is not None
    assert payload["session_jti"] == "abc123"
    assert payload["password_fingerprint"] == build_password_fingerprint("hash-demo")
