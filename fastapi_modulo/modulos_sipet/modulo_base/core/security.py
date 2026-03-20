from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from fastapi import HTTPException
from jose import JWTError, jwt
from fastapi_modulo.core.security_compat import ensure_bcrypt_passlib_compat

ensure_bcrypt_passlib_compat()

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SENSITIVE_ACTION_MODULE_ACTIVATE = "module_activate"
SENSITIVE_ACTION_MODULE_DEACTIVATE = "module_deactivate"
SENSITIVE_ACTION_PACKAGE_IMPORT = "package_import"
SENSITIVE_ACTION_PROTOCOL_SYNC = "protocol_sync"

SUPPORTED_SENSITIVE_ACTIONS = {
    SENSITIVE_ACTION_MODULE_ACTIVATE,
    SENSITIVE_ACTION_MODULE_DEACTIVATE,
    SENSITIVE_ACTION_PACKAGE_IMPORT,
    SENSITIVE_ACTION_PROTOCOL_SYNC,
}

ADMIN_ROLES = {"admin", "administrador", "superadmin", "superadministrador"}


def _security_secret() -> str:
    return (
        os.environ.get("MODULE_SECURITY_SECRET")
        or os.environ.get("AUTH_COOKIE_SECRET")
        or os.environ.get("SECRET_KEY")
        or "modulo-base-security-dev-secret"
    )


def _security_algorithm() -> str:
    return "HS256"


def _security_ttl_seconds(env_var: str, default: int) -> int:
    raw = (os.environ.get(env_var) or str(default)).strip()
    try:
        return max(60, int(raw))
    except ValueError:
        return default


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def hash_sensitive_secret(secret: str) -> str:
    normalized = str(secret or "").strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="Se requiere un secreto para firmar la operacion.")
    return pwd_context.hash(normalized)


def verify_sensitive_secret(secret: str, hashed_secret: str) -> bool:
    normalized = str(secret or "").strip()
    stored = str(hashed_secret or "").strip()
    if not normalized or not stored:
        return False
    try:
        return pwd_context.verify(normalized, stored)
    except Exception:
        return False


def require_admin_operation(user_role: str, *, action: str) -> None:
    normalized_role = str(user_role or "").strip().lower()
    if normalized_role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail=f"La accion '{action}' requiere privilegios administrativos.")


def issue_temporary_token(
    *,
    subject: str,
    module_key: str,
    purpose: str,
    extra: dict[str, Any] | None = None,
    ttl_seconds: int | None = None,
) -> dict[str, Any]:
    issued_at = _utcnow()
    expires_at = issued_at + timedelta(seconds=ttl_seconds or _security_ttl_seconds("MODULE_SECURITY_TEMP_TOKEN_TTL", 300))
    payload = {
        "sub": str(subject or "").strip(),
        "module_key": str(module_key or "").strip(),
        "purpose": str(purpose or "").strip(),
        "kind": "temporary",
        "nonce": secrets.token_hex(12),
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
        "extra": extra or {},
    }
    return {
        "token": jwt.encode(payload, _security_secret(), algorithm=_security_algorithm()),
        "expires_at": expires_at.isoformat(),
        "subject": payload["sub"],
        "module_key": payload["module_key"],
        "purpose": payload["purpose"],
    }


def verify_temporary_token(
    *,
    token: str,
    subject: str,
    module_key: str,
    purpose: str,
) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, _security_secret(), algorithms=[_security_algorithm()])
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Token temporal invalido.") from exc
    if str(payload.get("kind") or "").strip() != "temporary":
        raise HTTPException(status_code=403, detail="El token no corresponde a un token temporal.")
    if str(payload.get("sub") or "").strip() != str(subject or "").strip():
        raise HTTPException(status_code=403, detail="El token temporal no corresponde al sujeto actual.")
    if str(payload.get("module_key") or "").strip() != str(module_key or "").strip():
        raise HTTPException(status_code=403, detail="El token temporal no corresponde al modulo solicitado.")
    if str(payload.get("purpose") or "").strip() != str(purpose or "").strip():
        raise HTTPException(status_code=403, detail="El token temporal no corresponde al proposito solicitado.")
    return payload


def issue_sensitive_action_token(
    *,
    subject: str,
    action: str,
    module_key: str,
    secret: str,
    secret_verifier: Callable[[str], bool] | None = None,
    secret_hash: str = "",
    ttl_seconds: int | None = None,
) -> dict[str, Any]:
    normalized_action = str(action or "").strip()
    if normalized_action not in SUPPORTED_SENSITIVE_ACTIONS:
        raise HTTPException(status_code=400, detail="Accion sensible no soportada.")
    normalized_secret = str(secret or "").strip()
    if not normalized_secret:
        raise HTTPException(status_code=401, detail="Confirmacion sensible invalida.")
    verified = False
    if secret_verifier is not None:
        verified = bool(secret_verifier(normalized_secret))
    elif secret_hash:
        verified = verify_sensitive_secret(normalized_secret, secret_hash)
    if not verified:
        raise HTTPException(status_code=401, detail="Confirmacion sensible invalida.")
    return issue_temporary_token(
        subject=subject,
        module_key=module_key,
        purpose=normalized_action,
        extra={"scope": "sensitive_action"},
        ttl_seconds=ttl_seconds or _security_ttl_seconds("MODULE_SECURITY_SENSITIVE_ACTION_TTL", 300),
    )


def verify_sensitive_action_token(
    *,
    token: str,
    subject: str,
    action: str,
    module_key: str,
) -> dict[str, Any]:
    normalized_action = str(action or "").strip()
    if normalized_action not in SUPPORTED_SENSITIVE_ACTIONS:
        raise HTTPException(status_code=400, detail="Accion sensible no soportada.")
    payload = verify_temporary_token(
        token=token,
        subject=subject,
        module_key=module_key,
        purpose=normalized_action,
    )
    extra = payload.get("extra") or {}
    if str(extra.get("scope") or "").strip() != "sensitive_action":
        raise HTTPException(status_code=403, detail="El token no corresponde a una operacion sensible.")
    return payload


def issue_signed_authorization(
    *,
    subject: str,
    module_key: str,
    action: str,
    permissions: list[str] | None = None,
    ttl_seconds: int | None = None,
) -> dict[str, Any]:
    issued_at = _utcnow()
    expires_at = issued_at + timedelta(seconds=ttl_seconds or _security_ttl_seconds("MODULE_SECURITY_SIGNED_AUTH_TTL", 600))
    payload = {
        "sub": str(subject or "").strip(),
        "module_key": str(module_key or "").strip(),
        "action": str(action or "").strip(),
        "kind": "signed_authorization",
        "permissions": permissions or [],
        "nonce": secrets.token_hex(12),
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return {
        "token": jwt.encode(payload, _security_secret(), algorithm=_security_algorithm()),
        "expires_at": expires_at.isoformat(),
        "subject": payload["sub"],
        "module_key": payload["module_key"],
        "action": payload["action"],
        "permissions": payload["permissions"],
    }


def verify_signed_authorization(
    *,
    token: str,
    subject: str,
    module_key: str,
    action: str,
    required_permission: str = "",
) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, _security_secret(), algorithms=[_security_algorithm()])
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Autorizacion firmada invalida.") from exc
    if str(payload.get("kind") or "").strip() != "signed_authorization":
        raise HTTPException(status_code=403, detail="El token no corresponde a una autorizacion firmada.")
    if str(payload.get("sub") or "").strip() != str(subject or "").strip():
        raise HTTPException(status_code=403, detail="La autorizacion firmada no corresponde al sujeto actual.")
    if str(payload.get("module_key") or "").strip() != str(module_key or "").strip():
        raise HTTPException(status_code=403, detail="La autorizacion firmada no corresponde al modulo solicitado.")
    if str(payload.get("action") or "").strip() != str(action or "").strip():
        raise HTTPException(status_code=403, detail="La autorizacion firmada no corresponde a la accion solicitada.")
    permissions = [str(item).strip() for item in payload.get("permissions") or [] if str(item).strip()]
    if required_permission and required_permission not in permissions:
        raise HTTPException(status_code=403, detail="La autorizacion firmada no contiene el permiso requerido.")
    payload["permissions"] = permissions
    return payload


__all__ = [
    "ADMIN_ROLES",
    "SENSITIVE_ACTION_MODULE_ACTIVATE",
    "SENSITIVE_ACTION_MODULE_DEACTIVATE",
    "SENSITIVE_ACTION_PACKAGE_IMPORT",
    "SENSITIVE_ACTION_PROTOCOL_SYNC",
    "SUPPORTED_SENSITIVE_ACTIONS",
    "hash_sensitive_secret",
    "issue_sensitive_action_token",
    "issue_signed_authorization",
    "issue_temporary_token",
    "require_admin_operation",
    "verify_sensitive_action_token",
    "verify_signed_authorization",
    "verify_sensitive_secret",
    "verify_temporary_token",
]
