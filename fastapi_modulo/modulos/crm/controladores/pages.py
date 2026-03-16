from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response

from fastapi_modulo.modulos.crm.crm_menu import get_crm_menu_item
from fastapi_modulo.modulos.crm.controladores.utils import (
    CRM_CSS_PATH,
    CRM_JS_DIR,
    CRM_JS_PATH,
    load_crm_page_content,
    render_no_access_crm_page,
)
from fastapi_modulo.modulos.web.servicios.module_tools import (
    render_backend_page_html,
    scoped_text_asset_response,
    text_asset_response,
)

router = APIRouter()


@router.get("/crm", response_class=HTMLResponse)
def crm_page(request: Request):
    return render_backend_page_html(
        request,
        title="CRM",
        description="Gestión de contactos, oportunidades, actividades y campañas.",
        content=load_crm_page_content(),
        show_page_header=False,
    )


@router.get("/api/crm/assets/crm.js")
def crm_js_asset() -> Response:
    return text_asset_response(
        CRM_JS_PATH,
        media_type="application/javascript",
        fallback="console.error('CRM JS no disponible');",
    )


@router.get("/api/crm/assets/crm.css")
def crm_css_asset() -> Response:
    return text_asset_response(
        CRM_CSS_PATH,
        media_type="text/css",
        fallback="/* CRM CSS no disponible */",
    )


@router.get("/api/crm/assets/{asset_name:path}")
def crm_js_module_asset(asset_name: str) -> Response:
    return scoped_text_asset_response(
        CRM_JS_DIR,
        asset_name,
        media_type="application/javascript",
        fallback="console.error('CRM JS no disponible');",
    )


def _render_menu_page(request: Request, panel_id: str) -> HTMLResponse:
    item = get_crm_menu_item(panel_id)
    return render_no_access_crm_page(
        request,
        title=item.label,
        description=item.description,
    )


@router.get("/crm/contactos", response_class=HTMLResponse)
def crm_contactos_page(request: Request):
    return _render_menu_page(request, "contactos")


@router.get("/crm/oportunidades", response_class=HTMLResponse)
def crm_oportunidades_page(request: Request):
    return _render_menu_page(request, "oportunidades")


@router.get("/crm/actividades", response_class=HTMLResponse)
def crm_actividades_page(request: Request):
    return _render_menu_page(request, "actividades")


@router.get("/crm/notas", response_class=HTMLResponse)
def crm_notas_page(request: Request):
    return _render_menu_page(request, "notas")


@router.get("/crm/campanias", response_class=HTMLResponse)
def crm_campanias_page(request: Request):
    return _render_menu_page(request, "campanias")
