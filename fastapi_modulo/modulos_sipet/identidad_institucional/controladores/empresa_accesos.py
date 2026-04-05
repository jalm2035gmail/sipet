from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field, field_validator

from fastapi_modulo.modulos_sipet.identidad_institucional.servicios.acceso_empresa_service import (
    build_screen_access_catalog,
    get_role_permission_profiles_payload,
    require_empresa_permission,
    save_role_permission_profile_payload,
)
from fastapi_modulo.modulos_sipet.web.controladores.backend_shell import render_backend_page
from fastapi_modulo.modulos_sipet.web.servicios.template_service import get_templates


router = APIRouter()


class RolePermissionProfilePayload(BaseModel):
    role_name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=255)
    screen_access_levels: Optional[Any] = None
    conversation_access: Optional[Any] = None
    backend_roles: Optional[Any] = None
    permission_flags: Optional[Any] = None

    @field_validator("role_name", "description", mode="before")
    @classmethod
    def strip_profile_fields(cls, value: str) -> str:
        return str(value or "").strip()


def _render_empresa_shell(
    request: Request,
    *,
    initial_section: str,
    title: str,
    description: str,
    permission: str,
) -> HTMLResponse:
    require_empresa_permission(request, permission)
    template = get_templates().env.get_template("modulos/empresa/usuarios.html")
    content = template.render(initial_section=initial_section)
    return render_backend_page(
        request,
        title=title,
        description=description,
        content=content,
        show_page_header=True,
    )


@router.get("/empresa/usuarios/roles", response_class=HTMLResponse)
def empresa_roles_page(request: Request):
    return _render_empresa_shell(
        request,
        initial_section="roles",
        title="Roles",
        description="Perfiles base de roles y permisos.",
        permission="ver_acceso",
    )


@router.get("/empresa/acceso", response_class=HTMLResponse)
@router.get("/empresa/usuarios/acceso", response_class=HTMLResponse)
def empresa_acceso_page(request: Request):
    return _render_empresa_shell(
        request,
        initial_section="acceso",
        title="Niveles de acceso",
        description="Perfiles de rol y niveles de acceso por módulo.",
        permission="ver_acceso",
    )


@router.get("/empresa/MAIN-datos", response_class=HTMLResponse)
def empresa_main_datos_page(request: Request):
    require_empresa_permission(request, "ver_datos")
    return RedirectResponse(url="/empresa/base-datos", status_code=307)


@router.get("/api/roles-permisos")
def api_role_permission_profiles(request: Request):
    require_empresa_permission(request, "ver_acceso")
    return JSONResponse({"success": True, "data": get_role_permission_profiles_payload(request)})


@router.post("/api/roles-permisos")
def api_role_permission_profiles_save(request: Request, payload: RolePermissionProfilePayload):
    require_empresa_permission(request, "gestionar_acceso")
    try:
        profile = save_role_permission_profile_payload(request, payload)
        return JSONResponse({"success": True, "data": profile})
    except HTTPException as exc:
        return JSONResponse(
            {"success": False, "error": str(getattr(exc, "detail", "") or "No se pudo guardar el perfil.")},
            status_code=int(getattr(exc, "status_code", 400) or 400),
        )


@router.get("/api/screen-access-catalog")
def api_screen_access_catalog(request: Request):
    require_empresa_permission(request, "ver_acceso")
    try:
        return JSONResponse({"success": True, "data": build_screen_access_catalog()})
    except Exception as exc:
        return JSONResponse({"success": False, "error": str(exc)}, status_code=500)
