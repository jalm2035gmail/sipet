from __future__ import annotations

import json

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from fastapi_modulo.modulos_sipet.aplicaciones.controladores.dependencies import (
    APPLICATIONS_PERMISSION_VIEW,
    get_applications_permissions,
    request_actor_context,
    require_applications_permission,
)
from fastapi_modulo.modulos_sipet.aplicaciones.servicios.catalog_service import decorate_modules_payload
from fastapi_modulo.modulos_sipet.web.servicios.module_tools import render_backend_page_html, text_asset_response
from fastapi_modulo.modulos_sipet.web.servicios.template_service import get_templates

TEMPLATE_NAME = "modulos/aplicaciones/vistas/aplicaciones.html"
CSS_PATH = "fastapi_modulo/modulos/aplicaciones/static/css/aplicaciones.css"
JS_PATH = "fastapi_modulo/modulos/aplicaciones/static/js/aplicaciones.js"

router = APIRouter()


def load_aplicaciones_page(modules: list[dict]) -> str:
    template = get_templates().env.get_template(TEMPLATE_NAME)
    return template.render(
        applications_bootstrap=json.dumps({"modules": modules}, ensure_ascii=True),
        applications_css_url="/api/aplicaciones/assets/aplicaciones.css",
        applications_js_url="/api/aplicaciones/assets/aplicaciones.js",
    )


@router.get("/modulos", response_class=HTMLResponse)
def aplicaciones_legacy_redirect() -> RedirectResponse:
    return RedirectResponse(url="/aplicaciones", status_code=307)


@router.get("/aplicaciones", response_class=HTMLResponse)
def aplicaciones_page(request: Request):
    require_applications_permission(request, APPLICATIONS_PERMISSION_VIEW)
    actor = request_actor_context(request)
    return render_backend_page_html(
        request,
        title="Gobierno de aplicaciones",
        description="Catalogo, estado operativo, paquetes y auditoria del protocolo de modulos.",
        content=load_aplicaciones_page(decorate_modules_payload(tenant_key=actor["tenant_key"] or actor["tenant_id"] or None)),
        show_page_header=False,
    )


@router.get("/api/aplicaciones/assets/aplicaciones.css")
def aplicaciones_css_asset() -> Response:
    return text_asset_response(
        CSS_PATH,
        media_type="text/css",
        fallback="/* Aplicaciones CSS no disponible */",
    )


@router.get("/api/aplicaciones/assets/aplicaciones.js")
def aplicaciones_js_asset() -> Response:
    return text_asset_response(
        JS_PATH,
        media_type="application/javascript",
        fallback="console.error('Aplicaciones JS no disponible');",
    )


@router.get("/api/aplicaciones/permisos")
def aplicaciones_permissions(request: Request):
    require_applications_permission(request, APPLICATIONS_PERMISSION_VIEW)
    return get_applications_permissions(request)


__all__ = ["router", "load_aplicaciones_page"]
