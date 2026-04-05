"""
tests/test_builder_access.py
─────────────────────────────────────────────────────────────────────────────
Pruebas de builder_access.py y permisos del builder.

Cubre:
  • get_builder_access_level devuelve nivel correcto según screen levels.
  • require_write permite full_access y special_permissions.
  • require_write bloquea read_only con HTTP 403.
  • require_write bloquea no_access con HTTP 403.
  • Formulario de contacto valida email y texto vacío.
"""

from __future__ import annotations

import re
import uuid
from unittest.mock import patch

import pytest
from fastapi import HTTPException, Request
from starlette.datastructures import Headers


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_request(screen_levels: dict) -> Request:
    """Crea un Request minimal con state.screen_levels."""
    scope = {
        "type":    "http",
        "method":  "GET",
        "path":    "/",
        "headers": [],
        "query_string": b"",
    }
    req = Request(scope)
    req.state.screen_levels = screen_levels
    return req


def _levels_for(level: str) -> dict:
    return {"frontend.builder": {level: True}}


# ── get_builder_access_level ─────────────────────────────────────────────────

def test_full_access_level_resolved():
    from fastapi_modulo.modulos_sipet.frontend.servicios.builder_access import (
        get_builder_access_level,
    )
    from fastapi_modulo.modulos_sipet.web.servicios import access_service

    req = _make_request(_levels_for("full_access"))
    with patch.object(access_service, "get_user_screen_access_levels", return_value=_levels_for("full_access")):
        level = get_builder_access_level(req)
    assert level == "full_access"


def test_read_only_level_resolved():
    from fastapi_modulo.modulos_sipet.frontend.servicios.builder_access import (
        get_builder_access_level,
    )
    from fastapi_modulo.modulos_sipet.web.servicios import access_service

    req = _make_request(_levels_for("read_only"))
    with patch.object(access_service, "get_user_screen_access_levels", return_value=_levels_for("read_only")):
        level = get_builder_access_level(req)
    assert level == "read_only"


def test_no_levels_returns_no_access():
    from fastapi_modulo.modulos_sipet.frontend.servicios.builder_access import (
        get_builder_access_level,
    )
    from fastapi_modulo.modulos_sipet.web.servicios import access_service

    req = _make_request({})
    with patch.object(access_service, "get_user_screen_access_levels", return_value={}):
        level = get_builder_access_level(req)
    assert level == "no_access"


# ── require_write ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("level", ["full_access", "special_permissions"])
def test_require_write_allows_write_levels(level):
    from fastapi_modulo.modulos_sipet.frontend.servicios.builder_access import require_write
    from fastapi_modulo.modulos_sipet.web.servicios import access_service

    req = _make_request(_levels_for(level))
    with patch.object(access_service, "get_user_screen_access_levels", return_value=_levels_for(level)):
        require_write(req)   # Should not raise


@pytest.mark.parametrize("level", ["read_only", "user_only", "department_only", "no_access"])
def test_require_write_blocks_non_write_levels(level):
    from fastapi_modulo.modulos_sipet.frontend.servicios.builder_access import require_write
    from fastapi_modulo.modulos_sipet.web.servicios import access_service

    req = _make_request(_levels_for(level))
    with patch.object(access_service, "get_user_screen_access_levels", return_value=_levels_for(level)):
        with pytest.raises(HTTPException) as exc_info:
            require_write(req)
    assert exc_info.value.status_code == 403


# ── Formulario de contacto (validaciones básicas) ─────────────────────────────

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_contact(name: str, email: str, message: str) -> list[str]:
    """Replica la lógica de validación de contactos del controlador."""
    errors = []
    if not name.strip():
        errors.append("nombre_requerido")
    if not _EMAIL_RE.match(email.strip()):
        errors.append("email_invalido")
    if not message.strip():
        errors.append("mensaje_requerido")
    return errors


def test_contact_valid_passes():
    errs = _validate_contact("Ana", "ana@example.com", "Hola")
    assert errs == []


def test_contact_empty_name_fails():
    errs = _validate_contact("", "ana@ex.com", "Hola")
    assert "nombre_requerido" in errs


def test_contact_invalid_email_fails():
    for bad_email in ("noatsign", "missing@", "@nodomain", "a@b", ""):
        errs = _validate_contact("Ana", bad_email, "Hola")
        assert "email_invalido" in errs, f"Expected error for: {bad_email!r}"


def test_contact_valid_email_passes():
    for good_email in ("a@b.co", "user.name+tag@example.org", "x@y.z"):
        errs = _validate_contact("Ana", good_email, "Hola")
        assert "email_invalido" not in errs, f"Should pass: {good_email!r}"


def test_contact_empty_message_fails():
    errs = _validate_contact("Ana", "ana@ex.com", "   ")
    assert "mensaje_requerido" in errs


def test_contact_all_empty_has_three_errors():
    errs = _validate_contact("", "", "")
    assert len(errs) == 3
