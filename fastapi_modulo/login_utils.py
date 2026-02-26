# -*- coding: utf-8 -*-
"""
Utilidades para la identidad de login.
"""
import os
import json
from typing import Dict
from fastapi_modulo.login_identity_constants import DEFAULT_LOGIN_IDENTITY

def _build_login_asset_url(filename, default):
    version = "1"
    selected = filename or default
    return f"/templates/imagenes/{selected}?v={version}"

def _load_login_identity():
    app_env = (os.environ.get("APP_ENV") or os.environ.get("ENVIRONMENT") or "development").strip().lower()
    runtime_store_dir = (os.environ.get("RUNTIME_STORE_DIR") or f"fastapi_modulo/runtime_store/{app_env}").strip()
    path = (
        os.environ.get("IDENTIDAD_LOGIN_CONFIG_PATH")
        or os.path.join(runtime_store_dir, "identidad_login.json")
    )
    if not os.path.exists(path):
        return DEFAULT_LOGIN_IDENTITY.copy()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        return DEFAULT_LOGIN_IDENTITY.copy()
    return {**DEFAULT_LOGIN_IDENTITY, **data}

def get_login_identity_context() -> Dict[str, str]:
    data = _load_login_identity()
    return {
        "login_favicon_url": _build_login_asset_url(
            data.get("favicon_filename"),
            DEFAULT_LOGIN_IDENTITY["favicon_filename"],
        ),
        "login_logo_url": _build_login_asset_url(
            data.get("logo_filename"),
            DEFAULT_LOGIN_IDENTITY["logo_filename"],
        ),
        "login_bg_desktop_url": _build_login_asset_url(
            data.get("desktop_bg_filename"),
            DEFAULT_LOGIN_IDENTITY["desktop_bg_filename"],
        ),
        "login_bg_mobile_url": _build_login_asset_url(
            data.get("mobile_bg_filename"),
            DEFAULT_LOGIN_IDENTITY["mobile_bg_filename"],
        ),
        "login_company_short_name": data.get("company_short_name") or DEFAULT_LOGIN_IDENTITY["company_short_name"],
        "login_message": data.get("login_message") or DEFAULT_LOGIN_IDENTITY["login_message"],
    }
