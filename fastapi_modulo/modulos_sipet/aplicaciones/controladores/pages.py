from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from fastapi_modulo.modulos_sipet.aplicaciones.controladores.dependencies import (
    require_applications_permission,
    APPLICATIONS_PERMISSION_VIEW,
)
from fastapi_modulo.modulos_sipet.web.servicios.module_tools import render_backend_page_html
from fastapi_modulo.modulos_sipet.web.servicios.template_service import get_templates

TEMPLATE_NAME = "modulos_sipet/aplicaciones/vistas/aplicaciones.html"

router = APIRouter()


@router.get("/inicio", response_class=HTMLResponse)
def inicio_redirect() -> RedirectResponse:
    return RedirectResponse(url="/aplicaciones", status_code=307)


@router.get("/modulos", response_class=HTMLResponse)
def aplicaciones_legacy_redirect() -> RedirectResponse:
    return RedirectResponse(url="/aplicaciones", status_code=307)


@router.get("/aplicaciones", response_class=HTMLResponse)
def aplicaciones_page(request: Request):
    require_applications_permission(request, APPLICATIONS_PERMISSION_VIEW)
    template = get_templates().env.get_template(TEMPLATE_NAME)
    content = template.render(applications_css_url="/api/aplicaciones/assets/aplicaciones.css")
    return render_backend_page_html(
        request,
        title="Aplicaciones",
        description="Panel de módulos instalados.",
        content=content,
        show_page_header=False,
    )


@router.get("/api/aplicaciones/assets/aplicaciones.css")
def aplicaciones_css_asset():
    from fastapi_modulo.modulos_sipet.web.servicios.module_tools import text_asset_response
    return text_asset_response(
        "fastapi_modulo/modulos_sipet/aplicaciones/static/css/aplicaciones.css",
        media_type="text/css",
        fallback="",
    )


@router.get("/api/aplicaciones/permisos")
def aplicaciones_permissions(request: Request):
    from fastapi_modulo.modulos_sipet.aplicaciones.controladores.dependencies import get_applications_permissions
    require_applications_permission(request, APPLICATIONS_PERMISSION_VIEW)
    return get_applications_permissions(request)


__all__ = ["router"]
