from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SENSITIVE_ACTION_PROTOCOL_SYNC = "protocol_sync"
SENSITIVE_ACTION_PACKAGE_UPLOAD = "package_upload"
SENSITIVE_ACTION_PACKAGE_ROLLBACK = "package_rollback"
SUPPORTED_SENSITIVE_ACTIONS = {
    SENSITIVE_ACTION_PROTOCOL_SYNC,
    SENSITIVE_ACTION_PACKAGE_UPLOAD,
    SENSITIVE_ACTION_PACKAGE_ROLLBACK,
}


def _secret_key() -> str:
    return (
        os.environ.get("APPLICATIONS_CHALLENGE_SECRET")
        or os.environ.get("AUTH_COOKIE_SECRET")
        or os.environ.get("SECRET_KEY")
        or "applications-challenge-dev-secret"
    )


def _algorithm() -> str:
    return "HS256"


def _token_ttl_seconds() -> int:
    raw = (os.environ.get("APPLICATIONS_CHALLENGE_TTL_SECONDS") or "300").strip()
    try:
        return max(60, int(raw))
    except ValueError:
        return 300


def _get_user_password_hash(username: str) -> str:
    from fastapi_modulo.core import db as core_db
    from fastapi_modulo.modulos_sipet.web.servicios import auth_service

    normalized = str(username or "").strip()
    if not normalized:
        return ""
    db = core_db.SessionLocal()
    try:
        user = auth_service.find_user_by_login(db, normalized)
        if not user:
            return ""
        return str(getattr(user, "contrasena", "") or "").strip()
    finally:
        db.close()


def _verify_password(password: str, stored_hash: str) -> bool:
    from fastapi_modulo.modulos_sipet.web.servicios.auth_service import verify_password as verify_auth_password

    stored = str(stored_hash or "").strip()
    if not stored:
        return False
    try:
        if stored.startswith("$2"):
            return pwd_context.verify(password, stored)
    except Exception:
        return False
    return verify_auth_password(password, stored)


def issue_sensitive_action_token(
    *,
    username: str,
    password: str,
    action: str,
    module_key: str = "",
) -> dict[str, str]:
    normalized_action = str(action or "").strip()
    if normalized_action not in SUPPORTED_SENSITIVE_ACTIONS:
        raise HTTPException(status_code=400, detail="Acción sensible no soportada.")
    stored_hash = _get_user_password_hash(username)
    if not _verify_password(password, stored_hash):
        raise HTTPException(status_code=401, detail="Confirmación de contraseña inválida.")
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=_token_ttl_seconds())
    payload = {
        "sub": str(username or "").strip(),
        "action": normalized_action,
        "module_key": str(module_key or "").strip(),
        "nonce": secrets.token_hex(12),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return {
        "token": jwt.encode(payload, _secret_key(), algorithm=_algorithm()),
        "expires_at": expires_at.isoformat(),
        "action": normalized_action,
        "module_key": str(module_key or "").strip(),
    }


def verify_sensitive_action_token(
    *,
    token: str,
    username: str,
    action: str,
    module_key: str = "",
) -> None:
    normalized_action = str(action or "").strip()
    if normalized_action not in SUPPORTED_SENSITIVE_ACTIONS:
        raise HTTPException(status_code=400, detail="Acción sensible no soportada.")
    try:
        payload = jwt.decode(token, _secret_key(), algorithms=[_algorithm()])
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Token de confirmación inválido.") from exc
    if str(payload.get("sub") or "").strip() != str(username or "").strip():
        raise HTTPException(status_code=403, detail="El token de confirmación no corresponde al usuario actual.")
    if str(payload.get("action") or "").strip() != normalized_action:
        raise HTTPException(status_code=403, detail="El token de confirmación no corresponde a esta acción.")
    if str(payload.get("module_key") or "").strip() != str(module_key or "").strip():
        raise HTTPException(status_code=403, detail="El token de confirmación no corresponde al módulo solicitado.")


__all__ = [
    "SENSITIVE_ACTION_PACKAGE_ROLLBACK",
    "SENSITIVE_ACTION_PACKAGE_UPLOAD",
    "SENSITIVE_ACTION_PROTOCOL_SYNC",
    "SUPPORTED_SENSITIVE_ACTIONS",
    "issue_sensitive_action_token",
    "verify_sensitive_action_token",
]
