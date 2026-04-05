from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request

from fastapi_modulo.core.module_registry import list_modules_payload
from fastapi_modulo.modulos_sipet.web.servicios.access_service import (
    can_assign_role,
    get_role_permission_catalog,
    get_user_screen_access_levels,
    is_admin_or_superadmin,
    is_superadmin,
    normalize_role_name,
    save_role_permission_profile,
)


_EMPRESA_SCREEN = "empresa"
_EMPRESA_ROLES_SCREEN = "empresa.roles"
_EMPRESA_ACCESS_SCREEN = "empresa.acceso"


def _screen_level_enabled(entry: Any, *level_keys: str) -> bool:
    if isinstance(entry, bool):
        return entry
    if not isinstance(entry, dict):
        return False
    return any(bool(entry.get(level_key)) for level_key in level_keys)


def empresa_permissions(request: Request) -> dict[str, bool]:
    if is_admin_or_superadmin(request):
        return {
            "ver_branding": True,
            "editar_branding": True,
            "ver_usuarios": True,
            "gestionar_usuarios": True,
            "ver_acceso": True,
            "gestionar_acceso": True,
            "ver_datos": True,
            "ver_plantillas": True,
            "editar_plantillas": True,
        }
    levels = get_user_screen_access_levels(request)
    entry = levels.get(_EMPRESA_SCREEN) or {}
    roles_entry = levels.get(_EMPRESA_ROLES_SCREEN) or {}
    access_entry = levels.get(_EMPRESA_ACCESS_SCREEN) or {}
    if isinstance(entry, bool):
        return {
            key: entry
            for key in (
                "ver_branding",
                "editar_branding",
                "ver_usuarios",
                "gestionar_usuarios",
                "ver_acceso",
                "gestionar_acceso",
                "ver_datos",
                "ver_plantillas",
                "editar_plantillas",
            )
        }
    full = bool(entry.get("full_access"))
    editor = bool(entry.get("special_permissions"))
    gestor = bool(entry.get("department_only"))
    lector = bool(entry.get("read_only"))
    roles_admin = _screen_level_enabled(roles_entry, "full_access")
    roles_reader = _screen_level_enabled(roles_entry, "full_access", "read_only")
    access_admin = roles_admin or _screen_level_enabled(access_entry, "full_access")
    access_reader = roles_reader or _screen_level_enabled(access_entry, "full_access", "read_only")
    usuarios_admin = _screen_level_enabled(entry, "full_access")
    return {
        "ver_branding": full or editor or lector,
        "editar_branding": full or editor,
        "ver_usuarios": full or gestor or lector,
        "gestionar_usuarios": full or gestor,
        "ver_acceso": full or usuarios_admin or access_reader,
        "gestionar_acceso": full or access_admin,
        "ver_datos": full,
        "ver_plantillas": full or editor or lector,
        "editar_plantillas": full or editor,
    }


def require_empresa_permission(request: Request, permission: str) -> None:
    if not empresa_permissions(request).get(permission):
        raise HTTPException(status_code=403, detail="No tienes permiso para esta acción en Empresa.")


def validate_role_permission_management(request: Request, role_name: str) -> str:
    normalized = normalize_role_name(role_name)
    if normalized in {"superadministrador", "administrador_multiempresa"} and not is_superadmin(request):
        raise HTTPException(status_code=403, detail="No puedes administrar ese rol.")
    if not can_assign_role(request, normalized) and normalized not in {"autoridades", "departamento", "usuario", "administrador"}:
        if not is_admin_or_superadmin(request):
            raise HTTPException(status_code=403, detail="No puedes administrar ese rol.")
    elif not can_assign_role(request, normalized):
        raise HTTPException(status_code=403, detail="No puedes administrar ese rol.")
    return normalized


def get_role_permission_profiles_payload(request: Request) -> list[dict[str, Any]]:
    return get_role_permission_catalog(request)


def save_role_permission_profile_payload(request: Request, payload: Any) -> dict[str, Any]:
    role_name = validate_role_permission_management(request, payload.role_name)
    return save_role_permission_profile(
        role_name=role_name,
        description=payload.description,
        screen_access_levels=payload.screen_access_levels,
        conversation_access=payload.conversation_access,
        backend_roles=payload.backend_roles,
        permission_flags=payload.permission_flags,
    )


def build_screen_access_catalog() -> dict[str, Any]:
    catalog: dict[str, Any] = {}
    for item in list_modules_payload():
        key = str(item.get("key") or "")
        screens = item.get("screen_access_levels")
        if isinstance(screens, dict) and screens:
            catalog[key] = {
                "module_label": str(item.get("label") or key),
                "screens": screens,
            }
    return catalog
