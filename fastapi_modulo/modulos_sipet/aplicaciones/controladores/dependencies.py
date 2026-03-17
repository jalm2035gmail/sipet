from __future__ import annotations

from fastapi import HTTPException, Request

APPLICATIONS_PERMISSION_VIEW = "aplicaciones.ver"
APPLICATIONS_PERMISSION_STATE_EDIT = "aplicaciones.estado.editar"
APPLICATIONS_PERMISSION_PROTOCOL_SYNC = "aplicaciones.protocolo.sincronizar"
APPLICATIONS_PERMISSION_PACKAGES_UPLOAD = "aplicaciones.paquetes.subir"
APPLICATIONS_PERMISSION_AUDIT_VIEW = "aplicaciones.auditoria.ver"

APPLICATIONS_PERMISSION_KEYS = (
    APPLICATIONS_PERMISSION_VIEW,
    APPLICATIONS_PERMISSION_STATE_EDIT,
    APPLICATIONS_PERMISSION_PROTOCOL_SYNC,
    APPLICATIONS_PERMISSION_PACKAGES_UPLOAD,
    APPLICATIONS_PERMISSION_AUDIT_VIEW,
)
APPLICATIONS_ACCESS_ALIASES = (
    "Aplicaciones",
    "Gobierno de Aplicaciones",
    "system_admin",
    "aplicaciones",
)


def require_superadmin(request: Request) -> None:
    from fastapi_modulo.modulos_sipet.web.servicios.access_service import get_current_role

    role = (get_current_role(request) or "").strip().lower()
    if role not in {"superadministrador", "superadmin"}:
        raise HTTPException(status_code=403, detail="Acceso restringido a superadministrador")


def _screen_permission_enabled(request: Request, permission_key: str) -> bool:
    from fastapi_modulo.modulos_sipet.web.servicios.access_service import get_user_screen_access_levels, is_admin_or_superadmin

    if is_admin_or_superadmin(request):
        return True
    access_levels = get_user_screen_access_levels(request)
    entry = access_levels.get(permission_key) or {}
    if not isinstance(entry, dict):
        return False
    return any(
        bool(entry.get(level_key, False))
        for level_key in ("full_access", "read_only", "department_only", "user_only", "special_permissions")
    )


def _get_applications_access_level(request: Request) -> str:
    from fastapi_modulo.modulos_sipet.web.servicios.access_service import get_user_app_access, is_admin_or_superadmin

    if is_admin_or_superadmin(request):
        return "full_access"
    visible_access = {str(item).strip().lower() for item in get_user_app_access(request)}
    if any(alias.lower() in visible_access for alias in APPLICATIONS_ACCESS_ALIASES):
        return "full_access"
    for permission_key in APPLICATIONS_PERMISSION_KEYS:
        if _screen_permission_enabled(request, permission_key):
            return "special_permissions"
    return ""


def get_applications_permissions(request: Request) -> dict[str, bool]:
    explicit = {permission_key: _screen_permission_enabled(request, permission_key) for permission_key in APPLICATIONS_PERMISSION_KEYS}
    if any(explicit.values()):
        if not explicit[APPLICATIONS_PERMISSION_VIEW]:
            explicit[APPLICATIONS_PERMISSION_VIEW] = any(
                explicit[key] for key in APPLICATIONS_PERMISSION_KEYS if key != APPLICATIONS_PERMISSION_VIEW
            )
        return explicit

    level = _get_applications_access_level(request)
    permissions = {permission_key: False for permission_key in APPLICATIONS_PERMISSION_KEYS}
    if level == "full_access":
        return {permission_key: True for permission_key in APPLICATIONS_PERMISSION_KEYS}
    if level in {"read_only", "department_only", "user_only", "special_permissions"}:
        permissions[APPLICATIONS_PERMISSION_VIEW] = True
        permissions[APPLICATIONS_PERMISSION_AUDIT_VIEW] = True
    if level == "special_permissions":
        permissions[APPLICATIONS_PERMISSION_STATE_EDIT] = True
        permissions[APPLICATIONS_PERMISSION_PROTOCOL_SYNC] = True
        permissions[APPLICATIONS_PERMISSION_PACKAGES_UPLOAD] = True
    return permissions


def require_applications_permission(request: Request, permission_key: str) -> None:
    permissions = get_applications_permissions(request)
    if not permissions.get(permission_key, False):
        raise HTTPException(status_code=403, detail="No tienes permiso para realizar esta acción en Aplicaciones.")


def request_actor_context(request: Request) -> dict[str, str]:
    from fastapi_modulo.modulos_sipet.web.servicios.auth_service import request_ip, request_tenant_id

    username = (
        getattr(request.state, "user_name", None)
        or getattr(request.state, "username", None)
        or request.cookies.get("user_name")
        or request.cookies.get("username")
        or ""
    ).strip()
    return {
        "user_id": username,
        "tenant_id": request_tenant_id(request),
        "tenant_key": str(getattr(request.state, "tenant_key", None) or request_tenant_id(request) or "").strip(),
        "ip": request_ip(request),
    }


__all__ = [
    "APPLICATIONS_PERMISSION_AUDIT_VIEW",
    "APPLICATIONS_PERMISSION_PACKAGES_UPLOAD",
    "APPLICATIONS_PERMISSION_PROTOCOL_SYNC",
    "APPLICATIONS_PERMISSION_STATE_EDIT",
    "APPLICATIONS_PERMISSION_VIEW",
    "get_applications_permissions",
    "request_actor_context",
    "require_applications_permission",
    "require_superadmin",
]
