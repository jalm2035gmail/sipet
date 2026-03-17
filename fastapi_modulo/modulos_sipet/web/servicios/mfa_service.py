from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import struct
import time

from fastapi import Request

from fastapi_modulo.modulos_sipet.web.servicios.access_service import normalize_role_name

TOTP_PERIOD_SECONDS = int((os.environ.get("TOTP_PERIOD_SECONDS") or "30").strip() or "30")
TOTP_ALLOWED_DRIFT_STEPS = int((os.environ.get("TOTP_ALLOWED_DRIFT_STEPS") or "1").strip() or "1")


def get_user_totp_secret(user, role_name: str) -> str:
    user_secret = (getattr(user, "totp_secret", "") or "").strip()
    user_enabled = bool(getattr(user, "totp_enabled", False))
    if user_enabled and user_secret:
        return user_secret
    if normalize_role_name(role_name) != "autoridades":
        return ""
    return (os.environ.get("AUTHORITIES_TOTP_SECRET") or "").strip()


def normalize_totp_secret(secret: str) -> str:
    return re.sub(r"[^A-Z2-7]", "", (secret or "").strip().upper())


def totp_code_for_counter(secret: str, counter: int) -> str:
    normalized = normalize_totp_secret(secret)
    if not normalized:
        return ""
    padded = normalized + "=" * ((8 - len(normalized) % 8) % 8)
    try:
        key = base64.b32decode(padded, casefold=True)
    except Exception:
        return ""
    digest = hmac.new(key, struct.pack(">Q", int(counter)), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    binary = (
        ((digest[offset] & 0x7F) << 24)
        | ((digest[offset + 1] & 0xFF) << 16)
        | ((digest[offset + 2] & 0xFF) << 8)
        | (digest[offset + 3] & 0xFF)
    )
    return f"{binary % 1000000:06d}"


def verify_totp_code(secret: str, code: str) -> bool:
    normalized_code = re.sub(r"\s+", "", (code or "").strip())
    if not re.fullmatch(r"\d{6}", normalized_code):
        return False
    period = max(1, TOTP_PERIOD_SECONDS)
    current_counter = int(time.time() // period)
    window = max(0, TOTP_ALLOWED_DRIFT_STEPS)
    for drift in range(-window, window + 1):
        if hmac.compare_digest(totp_code_for_counter(secret, current_counter + drift), normalized_code):
            return True
    return False


def finish_mfa_login(
    request: Request,
    response,
    username: str,
    role_name: str,
    user_id: int | None = None,
    password_fingerprint: str = "",
) -> None:
    from fastapi_modulo.modulos_sipet.web.servicios import auth_service, passkey_service

    auth_service.apply_login_session(response, request, username, role_name, user_id, password_fingerprint=password_fingerprint)
    response.delete_cookie(passkey_service.PASSKEY_COOKIE_MFA_GATE)
