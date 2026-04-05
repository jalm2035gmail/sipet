from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, Request

from fastapi_modulo.modulos_sipet.web.servicios.access_service import get_current_role, get_user_app_access


def get_me_scope(request: Request) -> Optional[str]:
    """
    Verifica acceso y retorna el filtro de tenant:
    - None → acceso irrestricto (superadmin, administrador_multiempresa)
    - str  → empresa del usuario (administrador, app_access)
    Lanza 403 si no tiene acceso.
    """
    role = get_current_role(request)

    if role in ("superadministrador", "administrador_multiempresa"):
        return None

    if role == "administrador":
        tenant = (getattr(request.state, "tenant_id", None) or "").strip()
        if not tenant:
            raise HTTPException(
                status_code=403,
                detail="El administrador no tiene empresa asignada (tenant_id vacío)",
            )
        return tenant

    if "Multiempresa" in get_user_app_access(request):
        tenant = (getattr(request.state, "tenant_id", None) or "").strip()
        return tenant or "default"

    raise HTTPException(status_code=403, detail="Acceso restringido al módulo Multiempresa")


def require_full_access(request: Request) -> None:
    """Solo superadministrador y administrador_multiempresa pueden crear/eliminar empresas."""
    role = get_current_role(request)
    if role not in ("superadministrador", "administrador_multiempresa"):
        raise HTTPException(
            status_code=403,
            detail="Solo superadministrador o administrador_multiempresa puede realizar esta operación",
        )


def get_scope_info(request: Request) -> dict:
    """Retorna nivel de acceso y permisos del usuario actual."""
    tenant_filter = get_me_scope(request)
    role = get_current_role(request)

    if role == "superadministrador":
        nivel = "superadmin"
    elif role == "administrador_multiempresa":
        nivel = "multiempresa"
    else:
        nivel = "admin"

    return {
        "nivel": nivel,
        "tenant_filter": tenant_filter,
        "puede_crear": nivel in ("superadmin", "multiempresa"),
        "puede_eliminar": nivel in ("superadmin", "multiempresa"),
    }
