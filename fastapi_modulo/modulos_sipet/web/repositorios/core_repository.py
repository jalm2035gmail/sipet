from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from fastapi_modulo.modulos_sipet.web.modelos.core_models import Colores, Rol, Usuario


def _safe_first(query, *, context: str = ""):
    try:
        return query.first()
    except SQLAlchemyError as exc:
        print(f"[web.core_repository] query skipped in {context or 'unknown'}: {exc}", flush=True)
        return None


def _safe_all(query, *, context: str = ""):
    try:
        return query.all()
    except SQLAlchemyError as exc:
        print(f"[web.core_repository] query skipped in {context or 'unknown'}: {exc}", flush=True)
        return []


def find_user_by_login(db, *, login_value: str, login_hash: str = ""):
    normalized_login = (login_value or "").strip().lower()
    if not normalized_login and not login_hash:
        return None
    user = None
    if login_hash:
        user = _safe_first(
            db.query(Usuario).filter(Usuario.usuario_hash == login_hash),
            context="find_user_by_login.usuario_hash",
        )
        if not user:
            user = _safe_first(
                db.query(Usuario).filter(Usuario.correo_hash == login_hash),
                context="find_user_by_login.correo_hash",
            )
    if not user and normalized_login:
        user = _safe_first(
            db.query(Usuario).filter(func.lower(Usuario.usuario) == normalized_login),
            context="find_user_by_login.username",
        )
    if not user and normalized_login:
        user = _safe_first(
            db.query(Usuario).filter(func.lower(Usuario.correo) == normalized_login),
            context="find_user_by_login.email",
        )
    return user


def find_user_by_id(db, user_id: int):
    return _safe_first(
        db.query(Usuario).filter(Usuario.id == int(user_id)),
        context="find_user_by_id",
    )


def find_role_name_by_id(db, role_id: int) -> str:
    role = _safe_first(
        db.query(Rol).filter(Rol.id == int(role_id)),
        context="find_role_name_by_id",
    )
    return str(getattr(role, "nombre", "") or "").strip()


def list_color_values(db) -> dict[str, str]:
    return {
        str(row.key or "").strip(): str(row.value or "").strip()
        for row in _safe_all(db.query(Colores), context="list_color_values")
    }


def list_users_basic(db, limit: int = 100) -> list[dict[str, Any]]:
    rows = _safe_all(
        db.query(Usuario).limit(max(1, int(limit))),
        context="list_users_basic",
    )
    return [
        {
            "id": int(getattr(row, "id", 0) or 0),
            "usuario": str(getattr(row, "usuario", "") or ""),
            "rol_id": int(getattr(row, "rol_id", 0) or 0),
            "totp_enabled": bool(getattr(row, "totp_enabled", False)),
            "totp_secret": str(getattr(row, "totp_secret", "") or ""),
            "backendauthn_credential_id": str(getattr(row, "backendauthn_credential_id", "") or ""),
            "backendauthn_public_key": str(getattr(row, "backendauthn_public_key", "") or ""),
        }
        for row in rows
    ]


__all__ = [
    "find_role_name_by_id",
    "find_user_by_id",
    "find_user_by_login",
    "list_color_values",
    "list_users_basic",
]
