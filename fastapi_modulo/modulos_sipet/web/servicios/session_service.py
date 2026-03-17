from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import uuid
from typing import Optional

from fastapi import Request, Response

from fastapi_modulo.core.tenant_context import normalize_host_identifier
from fastapi_modulo.modulos_sipet.web.servicios.redis_security_service import (
    get_active_session,
    is_session_revoked,
)

AUTH_COOKIE_NAME = "auth_session"
CSRF_COOKIE_NAME = "csrf_token"
COOKIE_SECURE = (os.environ.get("COOKIE_SECURE") or "").strip().lower() in {"1", "true", "yes", "on"}
SESSION_MAX_AGE_SECONDS = int((os.environ.get("SESSION_MAX_AGE_SECONDS") or "28800").strip() or "28800")
CSRF_PROTECTION_ENABLED = (os.environ.get("CSRF_PROTECTION_ENABLED") or "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
AUTH_COOKIE_SECRET = (
    os.environ.get("AUTH_COOKIE_SECRET")
    or os.environ.get("SECRET_KEY")
    or "cambia-este-secreto-en-produccion"
).strip()


def normalize_tenant_id(value: Optional[str]) -> str:
    raw = (value or "").strip().lower()
    normalized = re.sub(r"[^a-z0-9._-]+", "-", raw).strip("-._")
    return normalized or "default"


def build_password_fingerprint(password_hash: str) -> str:
    digest = hashlib.sha256((password_hash or "").encode("utf-8")).hexdigest()
    return digest[:24]


def issue_csrf_token() -> str:
    return uuid.uuid4().hex + uuid.uuid4().hex


def build_session_cookie(
    username: str,
    role: str,
    tenant_id: str,
    host: str = "",
    session_jti: Optional[str] = None,
    password_fingerprint: str = "",
) -> str:
    payload_json = json.dumps(
        {
            "u": username.strip(),
            "r": role.strip().lower(),
            "t": normalize_tenant_id(tenant_id),
            "h": normalize_host_identifier(host),
            "j": (session_jti or uuid.uuid4().hex).strip(),
            "pv": str(password_fingerprint or "").strip(),
        },
        separators=(",", ":"),
        ensure_ascii=True,
    )
    payload = base64.urlsafe_b64encode(payload_json.encode("utf-8")).decode("ascii").rstrip("=")
    signature = hmac.new(
        AUTH_COOKIE_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload}.{signature}"


def read_session_cookie(token: str) -> Optional[dict[str, str]]:
    if not token or "." not in token:
        return None
    payload, signature = token.rsplit(".", 1)
    expected_signature = hmac.new(
        AUTH_COOKIE_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        return None
    try:
        padding = "=" * (-len(payload) % 4)
        payload_json = base64.urlsafe_b64decode((payload + padding).encode("ascii")).decode("utf-8")
        data = json.loads(payload_json)
    except (ValueError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    username = str(data.get("u", "")).strip()
    role = str(data.get("r", "")).strip().lower()
    if not username or not role:
        return None
    tenant_id = normalize_tenant_id(str(data.get("t", "")).strip() or os.environ.get("DEFAULT_TENANT_ID", "default"))
    host = normalize_host_identifier(str(data.get("h", "")).strip())
    session_jti = str(data.get("j", "")).strip()
    password_fingerprint = str(data.get("pv", "")).strip()
    if session_jti:
        if is_session_revoked(session_jti):
            return None
        if get_active_session(session_jti) is None:
            from fastapi_modulo.modulos_sipet.web.repositorios.security_repository import is_session_active

            if not is_session_active(session_jti):
                return None
        else:
            return {
                "username": username,
                "role": role,
                "tenant_id": tenant_id,
                "host": host,
                "session_jti": session_jti,
                "password_fingerprint": password_fingerprint,
            }
    return {
        "username": username,
        "role": role,
        "tenant_id": tenant_id,
        "host": host,
        "session_jti": session_jti,
        "password_fingerprint": password_fingerprint,
    }


def request_host(request: Request) -> str:
    return normalize_host_identifier(
        request.headers.get("x-forwarded-host")
        or request.headers.get("host")
        or request.url.hostname
    )


def is_session_bound_to_request(request: Request, session_data: Optional[dict[str, str]]) -> bool:
    if not isinstance(session_data, dict):
        return False
    request_tenant = normalize_tenant_id(
        getattr(request.state, "tenant_id", None)
        or request.cookies.get("tenant_id")
        or os.environ.get("DEFAULT_TENANT_ID", "default")
    )
    request_host_value = request_host(request)
    session_tenant = normalize_tenant_id(str(session_data.get("tenant_id", "")).strip() or "default")
    session_host = normalize_host_identifier(str(session_data.get("host", "")).strip())
    if session_tenant != request_tenant:
        return False
    if session_host and request_host_value and session_host != request_host_value:
        return False
    return True


def apply_auth_cookies(
    response: Response,
    request: Request,
    username: str,
    role_name: str,
    session_jti: Optional[str] = None,
    password_fingerprint: str = "",
    csrf_token: Optional[str] = None,
) -> str:
    tenant_id = normalize_tenant_id(
        getattr(request.state, "tenant_id", None)
        or request.cookies.get("tenant_id")
        or os.environ.get("DEFAULT_TENANT_ID", "default")
    )
    tenant_host = request_host(request)
    resolved_jti = (session_jti or uuid.uuid4().hex).strip()
    resolved_csrf = (csrf_token or issue_csrf_token()).strip()
    cookie_value = build_session_cookie(
        username,
        role_name,
        tenant_id,
        tenant_host,
        resolved_jti,
        password_fingerprint=password_fingerprint,
    )
    for key, value in (
        (AUTH_COOKIE_NAME, cookie_value),
        ("user_role", role_name.strip().lower()),
        ("user_name", username),
        ("tenant_id", tenant_id),
    ):
        response.set_cookie(
            key,
            value,
            httponly=True,
            samesite="lax",
            secure=COOKIE_SECURE,
            max_age=SESSION_MAX_AGE_SECONDS,
        )
    response.set_cookie(
        CSRF_COOKIE_NAME,
        resolved_csrf,
        httponly=False,
        samesite="lax",
        secure=COOKIE_SECURE,
        max_age=SESSION_MAX_AGE_SECONDS,
    )
    return resolved_jti


def clear_auth_cookies(response: Response) -> None:
    for key in (AUTH_COOKIE_NAME, "user_role", "user_name", "tenant_id", CSRF_COOKIE_NAME):
        response.delete_cookie(key)


async def csrf_request_token(request: Request) -> str:
    header_token = (request.headers.get("x-csrf-token") or request.headers.get("x-xsrf-token") or "").strip()
    if header_token:
        return header_token
    content_type = (request.headers.get("content-type") or "").strip().lower()
    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        try:
            form = await request.form()
        except Exception:
            return ""
        return str(form.get("csrf_token") or "").strip()
    return ""


async def validate_csrf_request(request: Request) -> bool:
    cookie_token = (request.cookies.get(CSRF_COOKIE_NAME) or "").strip()
    if not cookie_token:
        return False
    request_token = await csrf_request_token(request)
    if not request_token:
        return False
    return hmac.compare_digest(cookie_token, request_token)


def is_same_origin_request(request: Request) -> bool:
    from urllib.parse import urlparse

    host = (request.headers.get("host") or "").strip().lower()
    forwarded_host = (request.headers.get("x-forwarded-host") or "").split(",")[0].strip().lower()
    effective_host = forwarded_host or host
    if not effective_host:
        return False
    forwarded_proto = (request.headers.get("x-forwarded-proto") or "").split(",")[0].strip().lower()
    effective_scheme = forwarded_proto or request.url.scheme
    current_origin = f"{effective_scheme}://{effective_host}"

    origin = (request.headers.get("origin") or "").strip().rstrip("/")
    if origin:
        origin_normalized = origin.lower()
        if origin_normalized == current_origin:
            return True
        try:
            parsed_origin = urlparse(origin_normalized)
            parsed_current = urlparse(current_origin)
            return parsed_origin.netloc == parsed_current.netloc and parsed_origin.scheme in {"http", "https"}
        except Exception:
            return False

    referer = (request.headers.get("referer") or "").strip()
    if referer:
        parsed = urlparse(referer)
        referer_origin = f"{parsed.scheme}://{parsed.netloc}".rstrip("/").lower()
        if referer_origin == current_origin:
            return True
        parsed_current = urlparse(current_origin)
        return parsed.netloc.lower() == parsed_current.netloc and parsed.scheme in {"http", "https"}

    return False
