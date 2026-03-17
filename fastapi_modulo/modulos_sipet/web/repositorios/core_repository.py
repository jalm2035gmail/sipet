from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import func

from fastapi_modulo.modulos_sipet.web.modelos.core_models import Colores, Rol, Usuario


def find_user_by_login(db, *, login_value: str, login_hash: str = ""):
    normalized_login = (login_value or "").strip().lower()
    if not normalized_login and not login_hash:
        return None
    user = None
    if login_hash:
        user = db.query(Usuario).filter(Usuario.usuario_hash == login_hash).first()
        if not user:
            user = db.query(Usuario).filter(Usuario.correo_hash == login_hash).first()
    if not user and normalized_login:
        user = db.query(Usuario).filter(func.lower(Usuario.usuario) == normalized_login).first()
    if not user and normalized_login:
        user = db.query(Usuario).filter(func.lower(Usuario.correo) == normalized_login).first()
    return user


def find_user_by_id(db, user_id: int):
    return db.query(Usuario).filter(Usuario.id == int(user_id)).first()


def find_role_name_by_id(db, role_id: int) -> str:
    role = db.query(Rol).filter(Rol.id == int(role_id)).first()
    return str(getattr(role, "nombre", "") or "").strip()


def list_color_values(db) -> dict[str, str]:
    return {
        str(row.key or "").strip(): str(row.value or "").strip()
        for row in db.query(Colores).all()
    }


def list_users_basic(db, limit: int = 100) -> list[dict[str, Any]]:
    rows = db.query(Usuario).limit(max(1, int(limit))).all()
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
