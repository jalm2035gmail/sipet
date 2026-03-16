from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import unicodedata
from typing import Optional

from fastapi import HTTPException, Request

from fastapi_modulo.module_registry import get_active_app_access_names, is_app_access_enabled
from fastapi_modulo.modulos.web.servicios.session_service import AUTH_COOKIE_NAME, read_session_cookie


def normalize_role_name(role_name: Optional[str]) -> str:
    raw = (role_name or "").strip().lower()
    if not raw:
        return "usuario"
    normalized = unicodedata.normalize("NFKD", raw)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    if not normalized:
        return "usuario"
    if normalized in {"superadmin", "super_admin", "super_administrador", "superadministrador", "superadministrdor"}:
        return "superadministrador"
    if normalized in {"administrador_multiempresa", "admin_multiempresa", "multiempresa_admin", "administrador_multi"}:
        return "administrador_multiempresa"
    if normalized in {"admin", "administrador", "administador", "administrdor", "admnistrador"}:
        return "administrador"
    from fastapi_modulo.modulos.personalizacion.controladores.roles import ROLE_ALIASES

    return ROLE_ALIASES.get(normalized, normalized)


def get_current_role(request: Request) -> str:
    role = (
        getattr(request.state, "user_role", None)
        or getattr(request.state, "role", None)
        or request.cookies.get("user_role")
        or request.cookies.get("role")
        or request.cookies.get("rol")
        or ""
    )
    if not str(role or "").strip():
        session_data = read_session_cookie(request.cookies.get(AUTH_COOKIE_NAME, ""))
        if isinstance(session_data, dict):
            role = session_data.get("role") or ""
    if not str(role or "").strip():
        role = os.environ.get("DEFAULT_USER_ROLE") or ""
    return normalize_role_name(role)


def is_superadmin(request: Request) -> bool:
    return get_current_role(request) == "superadministrador"


def is_admin(request: Request) -> bool:
    return get_current_role(request) == "administrador"


def is_multiempresa_admin(request: Request) -> bool:
    return get_current_role(request) == "administrador_multiempresa"


def is_admin_or_superadmin(request: Request) -> bool:
    return is_superadmin(request) or is_multiempresa_admin(request) or is_admin(request)


def _sensitive_secret_bytes() -> bytes:
    secret = (
        os.environ.get("SENSITIVE_DATA_SECRET")
        or os.environ.get("AUTH_COOKIE_SECRET")
        or os.environ.get("SECRET_KEY")
        or "cambia-este-secreto-en-produccion"
    )
    return hashlib.sha256(secret.encode("utf-8")).digest()


def sensitive_lookup_hash(value: str) -> str:
    normalized = (value or "").strip().lower()
    return hmac.new(_sensitive_secret_bytes(), normalized.encode("utf-8"), hashlib.sha256).hexdigest()


def _meta_path() -> str:
    app_env = (os.environ.get("APP_ENV") or os.environ.get("ENVIRONMENT") or "development").strip().lower()
    sipet_data_dir = (os.environ.get("SIPET_DATA_DIR") or os.path.expanduser("~/.sipet/data")).strip()
    runtime_dir = (os.environ.get("RUNTIME_STORE_DIR") or os.path.join(sipet_data_dir, "runtime_store", app_env)).strip()
    return os.environ.get("COLAB_META_PATH") or os.path.join(runtime_dir, "colaboradores_meta.json")


def _read_colab_meta() -> dict:
    path = _meta_path()
    if not os.path.exists(path):
        return {}
    try:
        raw = json.loads(open(path, encoding="utf-8").read())
    except Exception:
        return {}
    return raw if isinstance(raw, dict) else {}


def _find_current_user_id(request: Request) -> Optional[str]:
    from fastapi_modulo import main as core

    username = getattr(request.state, "user_name", None) or ""
    if not username:
        return None
    db = core.SessionLocal()
    try:
        user = db.query(core.Usuario).filter(core.Usuario.usuario_hash == sensitive_lookup_hash(username)).first()
        if not user:
            return None
        return str(user.id)
    finally:
        db.close()


def get_user_app_access(request: Request) -> list[str]:
    try:
        if is_superadmin(request):
            return list(get_active_app_access_names())
        user_id = _find_current_user_id(request)
        if not user_id:
            return []
        entry = _read_colab_meta().get(user_id, {})
        if not isinstance(entry, dict):
            return []
        visible: list[str] = []
        seen: set[str] = set()
        direct_access = entry.get("app_access", [])
        if isinstance(direct_access, list):
            for item in direct_access:
                name = str(item).strip()
                if not name or name.lower() in seen:
                    continue
                seen.add(name.lower())
                visible.append(name)
        app_access_levels = entry.get("app_access_levels", {})
        if isinstance(app_access_levels, dict):
            for app_name, levels in app_access_levels.items():
                if not isinstance(levels, dict):
                    continue
                if not any(
                    bool(levels.get(level_key, False))
                    for level_key in ("full_access", "read_only", "department_only", "user_only", "special_permissions")
                ):
                    continue
                name = str(app_name).strip()
                if not name or name.lower() in seen:
                    continue
                seen.add(name.lower())
                visible.append(name)
        return [name for name in visible if is_app_access_enabled(name)]
    except Exception:
        return []


def get_user_strategy_submenu_access_levels(request: Request) -> dict:
    try:
        if is_superadmin(request):
            return {
                "Diagnóstico": {"full_access": True, "read_only": False, "department_only": False, "user_only": False, "special_permissions": False},
                "Plan estratégico": {"full_access": True, "read_only": False, "department_only": False, "user_only": False, "special_permissions": False},
                "POA": {"full_access": True, "read_only": False, "department_only": False, "user_only": False, "special_permissions": False},
                "Tablero de control": {"full_access": True, "read_only": False, "department_only": False, "user_only": False, "special_permissions": False},
                "IA estrategia": {"full_access": True, "read_only": False, "department_only": False, "user_only": False, "special_permissions": False},
            }
        user_id = _find_current_user_id(request)
        if not user_id:
            return {}
        entry = _read_colab_meta().get(user_id, {})
        levels = entry.get("strategy_submenu_access_levels", {}) if isinstance(entry, dict) else {}
        return levels if isinstance(levels, dict) else {}
    except Exception:
        return {}


def get_user_screen_access_levels(request: Request) -> dict:
    try:
        if is_superadmin(request):
            return {"*": {"full_access": True}}
        user_id = _find_current_user_id(request)
        if not user_id:
            return {}
        entry = _read_colab_meta().get(user_id, {})
        levels = entry.get("screen_access_levels", {}) if isinstance(entry, dict) else {}
        if isinstance(levels, dict):
            return levels
    except Exception:
        pass
    raw = (os.environ.get("WEB_SCREEN_ACCESS_JSON") or "").strip()
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def has_screen_access(request: Request, screen_name: str, app_name: str = "") -> bool:
    if is_admin_or_superadmin(request):
        return True
    normalized_screen = str(screen_name or "").strip()
    if not normalized_screen:
        return False
    access = get_user_screen_access_levels(request)
    screen_entry = access.get(normalized_screen) or access.get("*") or {}
    if not isinstance(screen_entry, dict):
        return False
    if app_name and app_name not in get_user_app_access(request):
        return False
    return any(
        bool(screen_entry.get(level_key, False))
        for level_key in ("full_access", "read_only", "department_only", "user_only", "special_permissions")
    )


def require_screen_access(request: Request, screen_name: str, detail: str, app_name: str = "") -> None:
    if not has_screen_access(request, screen_name, app_name=app_name):
        raise HTTPException(status_code=403, detail=detail)


def require_app_access(request: Request, app_name: str, detail: str) -> None:
    if is_admin_or_superadmin(request):
        return
    if app_name not in get_user_app_access(request):
        raise HTTPException(status_code=403, detail=detail)
