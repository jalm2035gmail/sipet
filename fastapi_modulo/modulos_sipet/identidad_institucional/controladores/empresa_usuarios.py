from __future__ import annotations

from typing import Any, Literal, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from fastapi_modulo.modulos_sipet.identidad_institucional.servicios.acceso_empresa_service import require_empresa_permission
from fastapi_modulo.modulos_sipet.identidad_institucional.servicios.usuarios_empresa_service import (
    list_colaboradores_payload,
    save_colaborador_payload,
)
from fastapi_modulo.modulos_sipet.web.controladores.backend_shell import render_backend_page
from fastapi_modulo.modulos_sipet.web.servicios.template_service import get_templates


router = APIRouter()


class ColaboradorPayload(BaseModel):
    id: Optional[int] = None
    nombre: str = ""
    usuario: str = ""
    correo: str = ""
    contrasena: Optional[str] = None
    empleado: bool = False
    totp_enabled: bool = False
    rol: str = "usuario"
    app_access: Optional[Any] = None
    app_access_levels: Optional[Any] = None
    menu_blocks: Optional[Any] = None
    conversation_access: Optional[Any] = None
    inherit_role_permissions: bool = True
    departamento: str = ""
    puesto: str = ""
    celular: str = ""
    jefe_inmediato_id: Optional[int] = None
    imagen: str = ""


def _render_empresa_usuarios_shell(
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


@router.get("/empresa/usuarios", response_class=HTMLResponse)
def empresa_usuarios_page(request: Request):
    return _render_empresa_usuarios_shell(
        request,
        initial_section="usuarios",
        title="Usuarios",
        description="Gestión de usuarios y permisos de acceso.",
        permission="ver_usuarios",
    )


@router.get("/api/colaboradores")
def api_colaboradores_list(
    request: Request,
    limit: Optional[int] = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: str = Query(default=""),
    role: str = Query(default=""),
    is_active: Optional[str] = Query(default=None),
    detail: Literal["full", "light"] = Query(default="full"),
    include_catalogs: Optional[str] = Query(default=None),
):
    require_empresa_permission(request, "ver_usuarios")
    try:
        payload = list_colaboradores_payload(
            request,
            limit=limit,
            offset=offset,
            q=q,
            role=role,
            is_active=is_active,
            detail=detail,
            include_catalogs=include_catalogs,
        )
        return JSONResponse(payload)
    except HTTPException as exc:
        return JSONResponse(
            {"success": False, "error": str(getattr(exc, "detail", "") or "No se pudieron cargar usuarios.")},
            status_code=int(getattr(exc, "status_code", 400) or 400),
        )
    except Exception as exc:
        return JSONResponse({"success": False, "error": str(exc)}, status_code=500)


@router.post("/api/colaboradores")
def api_colaboradores_save(request: Request, payload: ColaboradorPayload):
    require_empresa_permission(request, "gestionar_usuarios")
    try:
        return JSONResponse({"success": True, "data": save_colaborador_payload(request, payload)})
    except HTTPException as exc:
        return JSONResponse(
            {"success": False, "error": str(getattr(exc, "detail", "") or "No se pudo guardar el usuario.")},
            status_code=int(getattr(exc, "status_code", 400) or 400),
        )
    except Exception as exc:
        return JSONResponse({"success": False, "error": str(exc)}, status_code=500)
