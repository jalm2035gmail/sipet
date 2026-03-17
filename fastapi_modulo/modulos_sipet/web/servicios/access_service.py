from __future__ import annotations

import hashlib
import json
import re
import unicodedata

from fastapi import HTTPException, Request

from fastapi_modulo.core.module_registry import list_system_app_access_options
from fastapi_modulo.modulos.personalizacion.controladores.roles import ROLE_ALIASES


def normalize_role_name(role_name: str | None) -> str:
    raw = (role_name or "").strip().lower()
    if not raw:
        return "usuario"
    normalized = unicodedata.normalize("NFKD", raw)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    if normalized in {"superadmin", "super_admin", "super_administrador", "superadministrador"}:
        return "superadministrador"
    return ROLE_ALIASES.get(normalized, normalized or "usuario")


def sensitive_lookup_hash(value: str | None) -> str:
    normalized = str(value or "").strip().lower()
    if not normalized:
        return ""
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_current_role(request: Request) -> str:
    role = (
        getattr(request.state, "user_role", None)
        or getattr(request.state, "role", None)
        or request.cookies.get("user_role")
        or request.cookies.get("role")
        or request.cookies.get("rol")
        or ""
    )
    return normalize_role_name(role)


def get_user_backend_roles(request: Request, username: str | None = None) -> list[str]:
    del username
    raw = getattr(request.state, "backend_roles", None) or request.cookies.get("backend_roles") or "[]"
    if isinstance(raw, list):
        values = raw
    else:
        try:
            values = json.loads(raw)
        except Exception:
            values = []
    if not isinstance(values, list):
        return []
    return [str(item).strip() for item in values if str(item).strip()]


def is_superadmin(request: Request) -> bool:
    return get_current_role(request) == "superadministrador"


def is_multiempresa_admin(request: Request) -> bool:
    return get_current_role(request) == "administrador_multiempresa"


def is_admin(request: Request) -> bool:
    return get_current_role(request) == "administrador"


def is_admin_or_superadmin(request: Request) -> bool:
    return get_current_role(request) in {
        "superadministrador",
        "administrador",
        "administrador_multiempresa",
    }


def require_superadmin(request: Request, detail: str = "Acceso solo para superadministrador") -> None:
    if not is_superadmin(request):
        raise HTTPException(status_code=403, detail=detail)


def require_admin_or_superadmin(request: Request, detail: str = "Acceso solo para administracion") -> None:
    if not is_admin_or_superadmin(request):
        raise HTTPException(status_code=403, detail=detail)


def get_visible_role_names(request: Request) -> list[str]:
    if is_superadmin(request):
        return [
            "superadministrador",
            "administrador_multiempresa",
            "administrador",
            "autoridades",
            "departamento",
            "usuario",
        ]
    if is_admin_or_superadmin(request):
        return ["administrador", "autoridades", "departamento", "usuario"]
    return ["usuario"]


def can_assign_role(request: Request, role_name: str | None) -> bool:
    return normalize_role_name(role_name) in set(get_visible_role_names(request))


def get_user_app_access(request: Request) -> list[str]:
    if is_admin_or_superadmin(request):
        return list(list_system_app_access_options())
    raw = getattr(request.state, "user_app_access", None) or request.cookies.get("user_app_access") or "[]"
    if isinstance(raw, list):
        values = raw
    else:
        try:
            values = json.loads(raw)
        except Exception:
            values = []
    if not isinstance(values, list):
        return []
    return [str(item).strip() for item in values if str(item).strip()]


def get_user_app_access_level(request: Request, app_name: str) -> str:
    return "full_access" if app_name in set(get_user_app_access(request)) else "no_access"


def require_app_access(request: Request, app_name: str, detail: str = "Sin acceso a la aplicacion") -> None:
    if get_user_app_access_level(request, app_name) == "no_access":
        raise HTTPException(status_code=403, detail=detail)


def get_user_strategy_submenu_access_levels(request: Request) -> dict:
    if is_admin_or_superadmin(request):
        return {
            "__all__": {
                "full_access": True,
                "read_only": False,
                "department_only": False,
                "user_only": False,
                "special_permissions": False,
            }
        }
    raw = getattr(request.state, "user_strategy_submenu_access_levels", None) or request.cookies.get(
        "user_strategy_submenu_access_levels"
    ) or "{}"
    if isinstance(raw, dict):
        return raw
    try:
        parsed = json.loads(raw)
    except Exception:
        parsed = {}
    return parsed if isinstance(parsed, dict) else {}


def get_user_strategy_submenu_access_level(request: Request, submenu_name: str) -> str:
    levels = get_user_strategy_submenu_access_levels(request)
    entry = levels.get(submenu_name) or levels.get("__all__") or {}
    if not isinstance(entry, dict):
        return "no_access"
    if entry.get("full_access"):
        return "full_access"
    if entry.get("read_only"):
        return "read_only"
    if entry.get("department_only"):
        return "department_only"
    if entry.get("user_only"):
        return "user_only"
    if entry.get("special_permissions"):
        return "special_permissions"
    return "no_access"


def has_strategy_submenu_access(request: Request, submenu_name: str) -> bool:
    return get_user_strategy_submenu_access_level(request, submenu_name) != "no_access"


def get_user_screen_access_levels(request: Request) -> dict:
    raw = getattr(request.state, "user_screen_access_levels", None) or request.cookies.get("user_screen_access_levels") or "{}"
    if isinstance(raw, dict):
        return raw
    try:
        parsed = json.loads(raw)
    except Exception:
        parsed = {}
    return parsed if isinstance(parsed, dict) else {}


def has_screen_access(request: Request, screen_name: str) -> bool:
    if is_admin_or_superadmin(request):
        return True
    levels = get_user_screen_access_levels(request)
    entry = levels.get(screen_name) or levels.get("__all__") or {}
    if isinstance(entry, bool):
        return entry
    if not isinstance(entry, dict):
        return False
    return any(bool(entry.get(key, False)) for key in ("full_access", "read_only", "department_only", "user_only", "special_permissions"))


def require_screen_access(request: Request, screen_name: str, detail: str = "Sin acceso a la pantalla", app_name: str = "") -> None:
    del app_name
    if not has_screen_access(request, screen_name):
        raise HTTPException(status_code=403, detail=detail)
