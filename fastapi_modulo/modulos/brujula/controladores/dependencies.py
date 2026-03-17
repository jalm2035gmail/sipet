from __future__ import annotations

from fastapi import Request

from fastapi_modulo.core import db as core_db
from fastapi_modulo.modulos_sipet.web.controladores.backend_shell import render_backend_page
from fastapi_modulo.modulos_sipet.web.servicios.module_tools import require_app_access
from fastapi_modulo.modulos_sipet.web.servicios.session_service import normalize_tenant_id


def get_session_local():
    return core_db.get_session_factory_for_host()


def resolve_current_tenant_id(request: Request | None = None) -> str:
    if request is None:
        return normalize_tenant_id("default")
    tenant_id = (
        getattr(request.state, "tenant_id", None)
        or request.headers.get("x-tenant-id")
        or request.headers.get("x-tenant")
        or request.cookies.get("tenant_id")
        or "default"
    )
    return normalize_tenant_id(tenant_id)


def render_backend_screen(*args, **kwargs):
    return render_backend_page(*args, **kwargs)


def require_brujula_access(request: Request) -> None:
    require_app_access(request, "Brújula", "Acceso restringido al módulo Brújula")
