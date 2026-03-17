from __future__ import annotations

import base64
import json
import os
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import Request, Response
from jose import JWTError, jwt

from fastapi_modulo.modulos_sipet.web.repositorios.security_repository import (
    consume_mfa_challenge,
    get_active_mfa_challenge,
    store_mfa_challenge,
)
from fastapi_modulo.modulos_sipet.web.servicios.auth_service import decrypt_sensitive, request_tenant_id
from fastapi_modulo.modulos_sipet.web.servicios.redis_security_service import (
    cache_json,
    delete_cached,
    get_cached_json,
)

PASSKEY_COOKIE_REGISTER = "passkey_register"
PASSKEY_COOKIE_AUTH = "passkey_auth"
PASSKEY_COOKIE_MFA_GATE = "passkey_mfa_gate"
PASSKEY_CHALLENGE_TTL_SECONDS = 300
JWT_ALGORITHM = "HS256"
AUTH_COOKIE_SECRET = (
    os.environ.get("AUTH_COOKIE_SECRET")
    or os.environ.get("SECRET_KEY")
    or "cambia-este-secreto-en-produccion"
).strip()
COOKIE_SECURE = (os.environ.get("COOKIE_SECURE") or "").strip().lower() in {"1", "true", "yes", "on"}


def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def b64url_decode(value: str) -> bytes:
    raw = (value or "").strip()
    if not raw:
        return b""
    raw += "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(raw.encode("ascii"))


def passkey_rp_id(request: Request) -> str:
    host = (request.url.hostname or "").strip().lower()
    if host:
        return host
    host_header = (request.headers.get("host") or "").split(":")[0].strip().lower()
    return host_header or "localhost"


def passkey_origin(request: Request) -> str:
    origin_header = (request.headers.get("origin") or "").strip()
    if origin_header:
        return origin_header
    return f"{request.url.scheme}://{request.url.netloc}"


def build_passkey_token(action: str, user_id: int, challenge: str, rp_id: str, origin: str) -> str:
    return jwt.encode(
        {
            "sub": str(int(user_id)),
            "mfa_step": action,
            "challenge_id": challenge,
            "rp_id": rp_id,
            "origin": origin,
            "jti": uuid.uuid4().hex,
            "tenant_id": "default",
            "exp": datetime.utcnow() + timedelta(seconds=PASSKEY_CHALLENGE_TTL_SECONDS),
        },
        AUTH_COOKIE_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def build_internal_token(
    *,
    user_id: int,
    tenant_id: str,
    mfa_step: str,
    challenge_id: str,
    origin: str = "",
    rp_id: str = "",
) -> tuple[str, str]:
    token_jti = uuid.uuid4().hex
    token = jwt.encode(
        {
            "sub": str(int(user_id)),
            "tenant_id": tenant_id,
            "mfa_step": mfa_step,
            "challenge_id": challenge_id,
            "origin": origin,
            "rp_id": rp_id,
            "jti": token_jti,
            "exp": datetime.utcnow() + timedelta(seconds=PASSKEY_CHALLENGE_TTL_SECONDS),
        },
        AUTH_COOKIE_SECRET,
        algorithm=JWT_ALGORITHM,
    )
    return token, token_jti


def read_passkey_token(token: str, expected_action: str) -> Optional[dict[str, Any]]:
    try:
        data = jwt.decode(token, AUTH_COOKIE_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None
    if not isinstance(data, dict) or str(data.get("mfa_step", "")) != expected_action:
        return None
    try:
        user_id = int(data.get("sub"))
        token_jti = str(data.get("jti", "")).strip()
        challenge = str(data.get("challenge_id", "")).strip()
        cached = get_cached_json("challenge", token_jti)
        if cached is not None:
            if (
                int(cached.get("user_id") or 0) != user_id
                or str(cached.get("challenge_type") or "") != expected_action
                or str(cached.get("challenge") or "") != challenge
            ):
                return None
        else:
            challenge_row = get_active_mfa_challenge(
                user_id=user_id,
                challenge_type=expected_action,
                token_jti=token_jti,
            )
            if challenge_row is None or challenge_row.challenge != challenge:
                return None
        return {
            "action": str(data.get("mfa_step", "")),
            "user_id": user_id,
            "tenant_id": str(data.get("tenant_id", "")).strip(),
            "challenge": challenge,
            "rp_id": str(data.get("rp_id", "")),
            "origin": str(data.get("origin", "")),
            "jti": token_jti,
        }
    except (TypeError, ValueError):
        return None


def build_mfa_gate_token(user_id: int) -> str:
    token, _ = build_internal_token(
        user_id=user_id,
        tenant_id="default",
        mfa_step="mfa_gate",
        challenge_id=uuid.uuid4().hex,
    )
    return token


def issue_mfa_gate_token(request: Request, user_id: int) -> str:
    challenge_id = uuid.uuid4().hex
    token, token_jti = build_internal_token(
        user_id=user_id,
        tenant_id=request_tenant_id(request),
        mfa_step="mfa_gate",
        challenge_id=challenge_id,
    )
    store_mfa_challenge(
        user_id=int(user_id),
        challenge_type="mfa_gate",
        token_jti=token_jti,
        challenge=challenge_id,
        origin="",
        rp_id="",
        expires_at=datetime.utcnow() + timedelta(seconds=PASSKEY_CHALLENGE_TTL_SECONDS),
    )
    cache_json(
        "challenge",
        token_jti,
        {
            "user_id": int(user_id),
            "challenge_type": "mfa_gate",
            "challenge": challenge_id,
            "tenant_id": request_tenant_id(request),
        },
        PASSKEY_CHALLENGE_TTL_SECONDS,
    )
    return token


def parse_client_data(client_data_b64: str) -> Optional[dict[str, Any]]:
    try:
        client_data_bytes = b64url_decode(client_data_b64)
        payload = json.loads(client_data_bytes.decode("utf-8"))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    payload["_raw_bytes"] = client_data_bytes
    return payload


def build_passkey_registration(request: Request, user, username: str) -> tuple[dict[str, Any], str]:
    username_plain = decrypt_sensitive(user.usuario) or username
    display_name = (user.full_name or "").strip() or username_plain
    challenge = b64url_encode(secrets.token_bytes(32))
    rp_id = passkey_rp_id(request)
    origin = passkey_origin(request)
    token, token_jti = build_internal_token(
        user_id=user.id,
        tenant_id=request_tenant_id(request),
        mfa_step="register",
        challenge_id=challenge,
        rp_id=rp_id,
        origin=origin,
    )
    store_mfa_challenge(
        user_id=int(user.id),
        challenge_type="register",
        token_jti=token_jti,
        challenge=challenge,
        origin=origin,
        rp_id=rp_id,
        expires_at=datetime.utcnow() + timedelta(seconds=PASSKEY_CHALLENGE_TTL_SECONDS),
    )
    cache_json(
        "challenge",
        token_jti,
        {
            "user_id": int(user.id),
            "challenge_type": "register",
            "challenge": challenge,
            "tenant_id": request_tenant_id(request),
            "origin": origin,
            "rp_id": rp_id,
        },
        PASSKEY_CHALLENGE_TTL_SECONDS,
    )
    options: dict[str, Any] = {
        "challenge": challenge,
        "rp": {"name": "SIPET", "id": rp_id},
        "user": {
            "id": b64url_encode(f"user:{user.id}".encode("utf-8")),
            "name": username_plain,
            "displayName": display_name,
        },
        "pubKeyCredParams": [{"type": "public-key", "alg": -7}],
        "timeout": 60000,
        "attestation": "none",
        "authenticatorSelection": {
            "authenticatorAttachment": "platform",
            "residentKey": "preferred",
            "userVerification": "preferred",
        },
    }
    if user.backendauthn_credential_id:
        options["excludeCredentials"] = [{"id": user.backendauthn_credential_id, "type": "public-key", "transports": ["internal"]}]
    return options, token


def build_passkey_authentication(request: Request, user) -> tuple[dict[str, Any], str]:
    challenge = b64url_encode(secrets.token_bytes(32))
    rp_id = passkey_rp_id(request)
    origin = passkey_origin(request)
    token, token_jti = build_internal_token(
        user_id=user.id,
        tenant_id=request_tenant_id(request),
        mfa_step="auth",
        challenge_id=challenge,
        rp_id=rp_id,
        origin=origin,
    )
    store_mfa_challenge(
        user_id=int(user.id),
        challenge_type="auth",
        token_jti=token_jti,
        challenge=challenge,
        origin=origin,
        rp_id=rp_id,
        expires_at=datetime.utcnow() + timedelta(seconds=PASSKEY_CHALLENGE_TTL_SECONDS),
    )
    cache_json(
        "challenge",
        token_jti,
        {
            "user_id": int(user.id),
            "challenge_type": "auth",
            "challenge": challenge,
            "tenant_id": request_tenant_id(request),
            "origin": origin,
            "rp_id": rp_id,
        },
        PASSKEY_CHALLENGE_TTL_SECONDS,
    )
    options = {
        "challenge": challenge,
        "rpId": rp_id,
        "timeout": 60000,
        "userVerification": "preferred",
        "allowCredentials": [{"id": user.backendauthn_credential_id, "type": "public-key", "transports": ["internal"]}],
    }
    return options, token


def set_passkey_cookie(response: Response, cookie_name: str, token: str) -> None:
    response.set_cookie(
        cookie_name,
        token,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        max_age=PASSKEY_CHALLENGE_TTL_SECONDS,
    )


def consume_passkey_challenge(user_id: int, challenge_type: str, token_jti: str, challenge: str) -> None:
    delete_cached("challenge", token_jti)
    consume_mfa_challenge(
        user_id=int(user_id),
        challenge_type=challenge_type,
        token_jti=token_jti,
        challenge=challenge,
    )


def list_registered_passkeys(user) -> list[dict[str, Any]]:
    credential_id = str(getattr(user, "backendauthn_credential_id", "") or "").strip()
    if not credential_id:
        return []
    return [
        {
            "credential_id": credential_id,
            "label": "Passkey principal",
            "sign_count": int(getattr(user, "backendauthn_sign_count", 0) or 0),
            "device_type": "platform",
            "revocable": True,
        }
    ]


def revoke_registered_passkey(db, user, credential_id: str) -> bool:
    current = str(getattr(user, "backendauthn_credential_id", "") or "").strip()
    if not current or current != str(credential_id or "").strip():
        return False
    user.backendauthn_credential_id = None
    user.backendauthn_public_key = None
    user.backendauthn_sign_count = 0
    db.add(user)
    db.commit()
    return True
