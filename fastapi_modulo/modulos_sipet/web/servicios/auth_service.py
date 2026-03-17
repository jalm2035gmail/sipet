from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import time
from typing import Any, Optional

from cryptography.fernet import Fernet, InvalidToken
from fastapi import Request, Response
from passlib.context import CryptContext

from fastapi_modulo.core import db as core_db
from fastapi_modulo.modulos_sipet.web.repositorios.core_repository import (
    find_role_name_by_id,
    find_user_by_id as repository_find_user_by_id,
    find_user_by_login as repository_find_user_by_login,
)
from fastapi_modulo.modulos_sipet.web.repositorios.security_repository import (
    count_active_sessions,
    log_login_attempt,
    revoke_user_sessions,
    store_user_session,
)
from fastapi_modulo.modulos_sipet.web.servicios.access_service import normalize_role_name, sensitive_lookup_hash
from fastapi_modulo.modulos_sipet.web.servicios.redis_security_service import (
    mark_session_active,
    rate_limit_clear,
    rate_limit_get,
    rate_limit_increment,
    sensitive_endpoint_key,
)
from fastapi_modulo.modulos_sipet.web.servicios.security_policy_service import max_concurrent_sessions, should_revoke_other_sessions
from fastapi_modulo.modulos_sipet.web.servicios.session_service import (
    SESSION_MAX_AGE_SECONDS,
    apply_auth_cookies,
    build_password_fingerprint,
    normalize_tenant_id,
)

LOGIN_RATE_LIMIT_WINDOW_SECONDS = int((os.environ.get("LOGIN_RATE_LIMIT_WINDOW_SECONDS") or "300").strip() or "300")
LOGIN_RATE_LIMIT_MAX_ATTEMPTS = int((os.environ.get("LOGIN_RATE_LIMIT_MAX_ATTEMPTS") or "7").strip() or "7")
SENSITIVE_ENDPOINT_RATE_LIMIT_MAX_ATTEMPTS = int((os.environ.get("SENSITIVE_ENDPOINT_RATE_LIMIT_MAX_ATTEMPTS") or "20").strip() or "20")
BCRYPT_ROUNDS = int((os.environ.get("AUTH_BCRYPT_ROUNDS") or "12").strip() or "12")
PASSWORD_MIN_LENGTH = int((os.environ.get("PASSWORD_MIN_LENGTH") or "10").strip() or "10")
SENSITIVE_DATA_SECRET = (
    os.environ.get("SENSITIVE_DATA_SECRET")
    or os.environ.get("AUTH_COOKIE_SECRET")
    or os.environ.get("SECRET_KEY")
    or "cambia-este-secreto-en-produccion"
).strip()
_LOGIN_ATTEMPTS: dict[str, list[float]] = {}
def _build_password_context() -> CryptContext:
    preferred = CryptContext(
        schemes=["bcrypt_sha256", "pbkdf2_sha256"],
        deprecated="auto",
        bcrypt__rounds=BCRYPT_ROUNDS,
        pbkdf2_sha256__default_rounds=120_000,
    )
    try:
        probe = preferred.hash("Abcd1234!!")
        if preferred.verify("Abcd1234!!", probe):
            return preferred
    except Exception:
        pass
    return CryptContext(
        schemes=["pbkdf2_sha256"],
        deprecated="auto",
        pbkdf2_sha256__default_rounds=120_000,
    )


PASSWORD_CONTEXT = _build_password_context()


def _sensitive_fernet() -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(SENSITIVE_DATA_SECRET.encode("utf-8")).digest())
    return Fernet(key)


def encrypt_sensitive(value: Optional[str]) -> Optional[str]:
    raw = (value or "").strip()
    if not raw:
        return value
    if raw.startswith("enc$"):
        return raw
    token = _sensitive_fernet().encrypt(raw.encode("utf-8")).decode("utf-8")
    return f"enc${token}"


def decrypt_sensitive(value: Optional[str]) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    if not raw.startswith("enc$"):
        return raw
    try:
        return _sensitive_fernet().decrypt(raw[4:].encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError):
        return ""


def _auth_client_key(request: Request) -> str:
    forwarded_for = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
    if forwarded_for:
        return forwarded_for
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def request_user_agent(request: Request) -> str:
    return (request.headers.get("user-agent") or "").strip()


def request_ip(request: Request) -> str:
    return _auth_client_key(request)


def request_tenant_id(request: Request) -> str:
    return normalize_tenant_id(
        getattr(request.state, "tenant_id", None)
        or request.cookies.get("tenant_id")
        or os.environ.get("DEFAULT_TENANT_ID", "default")
    )


def is_login_rate_limited(request: Request) -> bool:
    key = _auth_client_key(request)
    username = (
        getattr(request.state, "pending_username", None)
        or request.query_params.get("usuario")
        or request.headers.get("x-auth-username")
        or ""
    ).strip().lower()
    ip_count = rate_limit_get("ip", key)
    if ip_count >= max(1, LOGIN_RATE_LIMIT_MAX_ATTEMPTS):
        return True
    if username:
        if rate_limit_get("user", username) >= max(1, LOGIN_RATE_LIMIT_MAX_ATTEMPTS):
            return True
        if rate_limit_get("ip_user", f"{key}:{username}") >= max(1, LOGIN_RATE_LIMIT_MAX_ATTEMPTS):
            return True
    now = time.time()
    window_start = now - max(1, LOGIN_RATE_LIMIT_WINDOW_SECONDS)
    attempts = [ts for ts in _LOGIN_ATTEMPTS.get(key, []) if ts >= window_start]
    _LOGIN_ATTEMPTS[key] = attempts
    return len(attempts) >= max(1, LOGIN_RATE_LIMIT_MAX_ATTEMPTS)


def register_failed_login_attempt(request: Request) -> None:
    key = _auth_client_key(request)
    username = (
        getattr(request.state, "pending_username", None)
        or request.query_params.get("usuario")
        or request.headers.get("x-auth-username")
        or ""
    ).strip().lower()
    rate_limit_increment("ip", key, LOGIN_RATE_LIMIT_WINDOW_SECONDS)
    if username:
        rate_limit_increment("user", username, LOGIN_RATE_LIMIT_WINDOW_SECONDS)
        rate_limit_increment("ip_user", f"{key}:{username}", LOGIN_RATE_LIMIT_WINDOW_SECONDS)
    now = time.time()
    window_start = now - max(1, LOGIN_RATE_LIMIT_WINDOW_SECONDS)
    attempts = [ts for ts in _LOGIN_ATTEMPTS.get(key, []) if ts >= window_start]
    attempts.append(now)
    _LOGIN_ATTEMPTS[key] = attempts


def clear_failed_login_attempts(request: Request) -> None:
    key = _auth_client_key(request)
    username = (
        getattr(request.state, "pending_username", None)
        or request.query_params.get("usuario")
        or request.headers.get("x-auth-username")
        or ""
    ).strip().lower()
    _LOGIN_ATTEMPTS.pop(key, None)
    rate_limit_clear("ip", key)
    if username:
        rate_limit_clear("user", username)
        rate_limit_clear("ip_user", f"{key}:{username}")


def is_sensitive_endpoint_rate_limited(request: Request, endpoint_name: str = "") -> bool:
    client_key = _auth_client_key(request)
    endpoint_key = sensitive_endpoint_key(endpoint_name or request.url.path)
    return rate_limit_get("sensitive_endpoint", f"{client_key}:{endpoint_key}") >= max(1, SENSITIVE_ENDPOINT_RATE_LIMIT_MAX_ATTEMPTS)


def register_sensitive_endpoint_hit(request: Request, endpoint_name: str = "") -> None:
    client_key = _auth_client_key(request)
    endpoint_key = sensitive_endpoint_key(endpoint_name or request.url.path)
    rate_limit_increment("sensitive_endpoint", f"{client_key}:{endpoint_key}", LOGIN_RATE_LIMIT_WINDOW_SECONDS)


def record_login_attempt(request: Request, username: str, success: bool) -> None:
    log_login_attempt(
        tenant_id=request_tenant_id(request),
        username=(username or "").strip(),
        ip=request_ip(request),
        user_agent=request_user_agent(request),
        success=success,
    )
    from fastapi_modulo.modulos_sipet.web.servicios.audit_service import record_security_event

    record_security_event(
        request,
        "login_success" if success else "login_failed",
        username=(username or "").strip(),
        success=success,
    )


def find_user_by_login(db, login_value: str):
    normalized_login = (login_value or "").strip().lower()
    if not normalized_login:
        return None
    return repository_find_user_by_login(db, login_value=normalized_login, login_hash=sensitive_lookup_hash(normalized_login))


def find_user_by_id(db, user_id: int):
    return repository_find_user_by_id(db, user_id)


def get_session_local():
    return core_db.SessionLocal


def hash_password(password: str) -> str:
    return PASSWORD_CONTEXT.hash(password)


def password_strength_errors(password: str) -> list[str]:
    value = str(password or "")
    errors: list[str] = []
    if len(value) < PASSWORD_MIN_LENGTH:
        errors.append(f"min_length:{PASSWORD_MIN_LENGTH}")
    if not re.search(r"[A-Z]", value):
        errors.append("missing_uppercase")
    if not re.search(r"[a-z]", value):
        errors.append("missing_lowercase")
    if not re.search(r"\d", value):
        errors.append("missing_digit")
    if not re.search(r"[^A-Za-z0-9]", value):
        errors.append("missing_special")
    common_values = {"123456", "12345678", "password", "qwerty", "demodemo", "admin123"}
    if value.strip().lower() in common_values:
        errors.append("common_password")
    return errors


def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    errors = password_strength_errors(password)
    return (len(errors) == 0, errors)


def assert_password_strength(password: str) -> None:
    ok, errors = validate_password_strength(password)
    if not ok:
        raise ValueError(",".join(errors))


def verify_password(password: str, stored_hash: str) -> bool:
    stored = (stored_hash or "").strip()
    if not stored:
        return False
    try:
        algo, iterations, salt, digest_hex = stored.split("$", 3)
        if algo != "pbkdf2_sha256":
            allow_legacy_plaintext = (os.environ.get("ALLOW_LEGACY_PLAINTEXT_PASSWORDS") or "").strip().lower() in {
                "1",
                "true",
                "yes",
                "on",
            }
            if allow_legacy_plaintext:
                return hmac.compare_digest(password, stored)
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except Exception:
        allow_legacy_plaintext = (os.environ.get("ALLOW_LEGACY_PLAINTEXT_PASSWORDS") or "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if allow_legacy_plaintext:
            return hmac.compare_digest(password, stored)
        return False


def needs_password_rehash(stored_hash: str) -> bool:
    stored = (stored_hash or "").strip()
    if not stored:
        return False
    if stored.startswith("$2") or stored.startswith("$bcrypt-sha256$"):
        try:
            return bool(PASSWORD_CONTEXT.needs_update(stored))
        except Exception:
            return True
    return True


def verify_password_with_policy(password: str, stored_hash: str) -> tuple[bool, Optional[str]]:
    stored = (stored_hash or "").strip()
    if not stored:
        return False, None
    if stored.startswith("$2"):
        try:
            verified, replacement = PASSWORD_CONTEXT.verify_and_update(password, stored)
            return bool(verified), replacement
        except Exception:
            return False, None
    verified = verify_password(password, stored)
    if not verified:
        return False, None
    return True, hash_password(password) if needs_password_rehash(stored) else None


def rehash_user_password_if_needed(db, user, plain_password: str) -> bool:
    verified, replacement_hash = verify_password_with_policy(plain_password, getattr(user, "contrasena", "") or "")
    if not verified:
        return False
    if replacement_hash and replacement_hash != (getattr(user, "contrasena", "") or ""):
        user.contrasena = replacement_hash
        db.add(user)
        db.commit()
    return True


def resolve_user_role_name(db, user) -> str:
    role_name = "usuario"
    if user.rol_id:
        role_name = normalize_role_name(find_role_name_by_id(db, user.rol_id))
    elif user.role:
        role_name = normalize_role_name(user.role)
    return role_name


def password_fingerprint_for_user(user) -> str:
    return build_password_fingerprint(getattr(user, "contrasena", "") or "")


def is_password_fingerprint_valid(db, username: str, expected_fingerprint: str) -> bool:
    if not expected_fingerprint:
        return True
    user = find_user_by_login(db, username)
    if not user:
        return False
    return hmac.compare_digest(password_fingerprint_for_user(user), expected_fingerprint)


def get_user_totp_secret(user, role_name: str) -> str:
    from fastapi_modulo.modulos_sipet.web.servicios.mfa_service import get_user_totp_secret as get_totp_secret

    return get_totp_secret(user, role_name)

def verify_totp_code(secret: str, code: str) -> bool:
    from fastapi_modulo.modulos_sipet.web.servicios.mfa_service import verify_totp_code as verify_code

    return verify_code(secret, code)


def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def b64url_decode(value: str) -> bytes:
    raw = (value or "").strip()
    if not raw:
        return b""
    raw += "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(raw.encode("ascii"))


def passkey_rp_id(request: Request) -> str:
    from fastapi_modulo.modulos_sipet.web.servicios.passkey_service import passkey_rp_id as resolve_rp_id

    return resolve_rp_id(request)


def passkey_origin(request: Request) -> str:
    from fastapi_modulo.modulos_sipet.web.servicios.passkey_service import passkey_origin as resolve_origin

    return resolve_origin(request)


def build_passkey_token(action: str, user_id: int, challenge: str, rp_id: str, origin: str) -> str:
    from fastapi_modulo.modulos_sipet.web.servicios.passkey_service import build_passkey_token as build_token

    return build_token(action, user_id, challenge, rp_id, origin)


def read_passkey_token(token: str, expected_action: str) -> Optional[dict[str, Any]]:
    from fastapi_modulo.modulos_sipet.web.servicios.passkey_service import read_passkey_token as read_token

    return read_token(token, expected_action)


def build_mfa_gate_token(user_id: int) -> str:
    from fastapi_modulo.modulos_sipet.web.servicios.passkey_service import build_mfa_gate_token as build_token

    return build_token(user_id)


def parse_client_data(client_data_b64: str) -> Optional[dict[str, Any]]:
    from fastapi_modulo.modulos_sipet.web.servicios.passkey_service import parse_client_data as parse_payload

    return parse_payload(client_data_b64)


def is_demo_account(username: str) -> bool:
    return (username or "").strip().lower() == "demo"


def build_passkey_registration(request: Request, user, username: str) -> tuple[dict[str, Any], str]:
    from fastapi_modulo.modulos_sipet.web.servicios.passkey_service import build_passkey_registration as build_registration

    return build_registration(request, user, username)


def build_passkey_authentication(request: Request, user) -> tuple[dict[str, Any], str]:
    from fastapi_modulo.modulos_sipet.web.servicios.passkey_service import build_passkey_authentication as build_authentication

    return build_authentication(request, user)


def set_passkey_cookie(response: Response, cookie_name: str, token: str) -> None:
    from fastapi_modulo.modulos_sipet.web.servicios.passkey_service import set_passkey_cookie as set_cookie

    set_cookie(response, cookie_name, token)


def apply_login_session(
    response: Response,
    request: Request,
    username: str,
    role_name: str,
    user_id: Optional[int] = None,
    password_fingerprint: str = "",
) -> None:
    tenant_id = request_tenant_id(request)
    normalized_role = normalize_role_name(role_name)
    session_jti = apply_auth_cookies(
        response,
        request,
        username,
        normalized_role,
        password_fingerprint=password_fingerprint,
    )
    if user_id:
        active_sessions_before = count_active_sessions(user_id=int(user_id), tenant_id=tenant_id)
        if should_revoke_other_sessions(role_name=normalized_role, tenant_id=tenant_id, user_id=user_id):
            revoke_user_sessions(user_id=int(user_id), tenant_id=tenant_id, keep_session_jti=session_jti)
        elif active_sessions_before >= max_concurrent_sessions(role_name=normalized_role, tenant_id=tenant_id, user_id=user_id):
            revoke_user_sessions(user_id=int(user_id), tenant_id=tenant_id)
    if user_id:
        from datetime import datetime, timedelta

        expires_at = datetime.utcnow() + timedelta(seconds=SESSION_MAX_AGE_SECONDS)
        store_user_session(
            user_id=int(user_id),
            tenant_id=tenant_id,
            session_jti=session_jti,
            ip=request_ip(request),
            user_agent=request_user_agent(request),
            expires_at=expires_at,
        )
        mark_session_active(
            session_jti,
            {
                "user_id": int(user_id),
                "tenant_id": tenant_id,
                "username": username,
                "role": normalized_role,
            },
            SESSION_MAX_AGE_SECONDS,
        )
        from fastapi_modulo.modulos_sipet.web.servicios.audit_service import record_security_event

        record_security_event(
            request,
            "session_created",
            user_id=int(user_id),
            username=username,
            metadata={"session_jti": session_jti, "role": normalized_role},
        )
