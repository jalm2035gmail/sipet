from __future__ import annotations

import json
import os
from typing import Any, Optional

import httpx

from fastapi_modulo.modulos.web.servicios.redis_security_service import cache_json, get_cached_json

IDENTITY_HTTP_TIMEOUT_SECONDS = float((os.environ.get("IDENTITY_HTTP_TIMEOUT_SECONDS") or "2.5").strip() or "2.5")
REMOTE_BRANDING_URL = (os.environ.get("REMOTE_BRANDING_URL") or "").strip()
REMOTE_CATALOGS_URL = (os.environ.get("REMOTE_CATALOGS_URL") or "").strip()
REMOTE_IDENTITY_TOKEN = (os.environ.get("REMOTE_IDENTITY_TOKEN") or "").strip()
REMOTE_BRANDING_CACHE_SECONDS = int((os.environ.get("REMOTE_BRANDING_CACHE_SECONDS") or "300").strip() or "300")
REMOTE_CATALOGS_CACHE_SECONDS = int((os.environ.get("REMOTE_CATALOGS_CACHE_SECONDS") or "300").strip() or "300")


def _default_headers() -> dict[str, str]:
    headers = {"accept": "application/json"}
    if REMOTE_IDENTITY_TOKEN:
        headers["authorization"] = f"Bearer {REMOTE_IDENTITY_TOKEN}"
    return headers


def _http_get_json(url: str, *, params: Optional[dict[str, Any]] = None) -> Optional[dict[str, Any]]:
    target = str(url or "").strip()
    if not target:
        return None
    try:
        with httpx.Client(timeout=IDENTITY_HTTP_TIMEOUT_SECONDS, follow_redirects=True) as client:
            response = client.get(target, params=params or None, headers=_default_headers())
            response.raise_for_status()
            payload = response.json()
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def fetch_remote_branding(*, host: str = "", tenant_id: str = "") -> Optional[dict[str, Any]]:
    cache_key = f"{host}:{tenant_id or 'default'}"
    cached = get_cached_json("remote_branding", cache_key)
    if cached is not None:
        return cached
    payload = _http_get_json(REMOTE_BRANDING_URL, params={"host": host, "tenant_id": tenant_id} if host or tenant_id else None)
    if not payload:
        return None
    cache_json("remote_branding", cache_key, payload, REMOTE_BRANDING_CACHE_SECONDS)
    return payload


def fetch_remote_catalog(*, catalog_name: str, tenant_id: str = "") -> Optional[dict[str, Any]]:
    cache_key = f"{catalog_name}:{tenant_id or 'default'}"
    cached = get_cached_json("remote_catalog", cache_key)
    if cached is not None:
        return cached
    payload = _http_get_json(
        REMOTE_CATALOGS_URL,
        params={"catalog": catalog_name, "tenant_id": tenant_id} if catalog_name or tenant_id else None,
    )
    if not payload:
        return None
    cache_json("remote_catalog", cache_key, payload, REMOTE_CATALOGS_CACHE_SECONDS)
    return payload


def merge_remote_branding(local_data: dict[str, str], *, host: str = "", tenant_id: str = "") -> dict[str, str]:
    merged = dict(local_data or {})
    payload = fetch_remote_branding(host=host, tenant_id=tenant_id)
    if not payload:
        return merged
    branding = payload.get("branding", payload)
    if not isinstance(branding, dict):
        return merged
    allowed_fields = {
        "login_favicon_url",
        "login_logo_url",
        "login_bg_desktop_url",
        "login_bg_mobile_url",
        "login_company_short_name",
        "login_message",
        "menu_position",
    }
    for key, value in branding.items():
        if key in allowed_fields and isinstance(value, str) and value.strip():
            merged[key] = value.strip()
    return merged


def export_remote_config_snapshot(*, host: str = "", tenant_id: str = "") -> str:
    payload = {
        "branding": fetch_remote_branding(host=host, tenant_id=tenant_id) or {},
        "catalogs": fetch_remote_catalog(catalog_name="default", tenant_id=tenant_id) or {},
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
