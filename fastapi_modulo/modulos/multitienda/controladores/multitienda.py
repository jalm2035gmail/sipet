from __future__ import annotations

from functools import lru_cache
import re

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from fastapi_modulo.modulos.multitienda.controladores.marketplace_backend import (
    build_marketplace_backend_app,
)
from fastapi_modulo.modulos.multitienda.vistas.utils import _prefix_root_relative_urls
from fastapi_modulo.modulos.multitienda.vistas.configuracion import configuracion_html
from fastapi_modulo.modulos.multitienda.vistas.gestion import gestion_html
from fastapi_modulo.modulos.multitienda.vistas.productos import productos_html
from fastapi_modulo.modulos.multitienda.vistas.tienda import tienda_html
from fastapi_modulo.modulos_sipet.web.servicios.template_context_service import build_backend_context
from fastapi_modulo.modulos_sipet.web.servicios.template_service import BACKEND_BASE_TEMPLATE, get_templates

router = APIRouter()
marketplace_app = build_marketplace_backend_app()

_STYLE_RE = re.compile(r"<style>(.*?)</style>", re.IGNORECASE | re.DOTALL)
_MAIN_RE = re.compile(r"<main\b[^>]*>(.*?)</main>", re.IGNORECASE | re.DOTALL)
_SCRIPT_RE = re.compile(r"(<script\b.*?</script>)", re.IGNORECASE | re.DOTALL)

_MODULE_SECTIONS = [
    {"id": "productos", "label": "Productos", "icon": "fa-solid fa-box", "route": "/multitienda/productos"},
    {"id": "configuracion", "label": "Configuración", "icon": "fa-solid fa-gear", "route": "/multitienda/configuracion"},
    {"id": "gestion", "label": "Administración de tiendas", "icon": "fa-solid fa-store", "route": "/multitienda/administracion_tiendas"},
]
_MODULE_NAVBAR_BOOTSTRAP = """
<script>
(function () {
    const menuName = 'Multitienda';
    try {
        window.localStorage.setItem('sipet_active_main_menu_name', menuName);
    } catch (error) {}
})();
</script>
"""
_MODULE_LAYOUT_OVERRIDES = """
<style>
html.ui-sidebar-modern .main-content {
    padding-right: 32px !important;
}

html.ui-sidebar-modern .content-shell,
html.ui-sidebar-modern .content-section,
.multitienda-official-view,
.multitienda-official-view .page {
    width: 100% !important;
    max-width: 100% !important;
}

.multitienda-official-view .page {
    margin: 0 auto !important;
    margin-left: 0 !important;
    padding: 20px 0 40px !important;
    font-size: 16px !important;
}

.multitienda-official-view .title,
.multitienda-official-view .subtitle {
    text-align: center;
}

.multitienda-official-view .section {
    overflow: hidden;
}

.multitienda-official-view .notebook {
    background: #fff;
    border: 1px solid #e6e8ee;
    border-radius: 12px;
    overflow: hidden;
}

.multitienda-official-view .notebook-tabs {
    display: flex;
    flex-wrap: wrap;
    gap: 0;
    border-bottom: 1px solid #e6e8ee;
    background: #f7f8fa;
}

.multitienda-official-view .notebook-tab {
    padding: 12px 22px;
    font-size: 0.9rem;
    font-weight: 600;
    color: #6b7280;
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    cursor: pointer;
    transition: color 0.15s ease, border-color 0.15s ease, background 0.15s ease;
}

.multitienda-official-view .notebook-tab:hover {
    color: #111827;
}

.multitienda-official-view .notebook-tab.active {
    color: #1a6b3c;
    border-bottom-color: #1a6b3c;
    background: #fff;
}

.multitienda-official-view .notebook-panel {
    padding: 24px;
}

.multitienda-official-view .notebook-panel[hidden] {
    display: none !important;
}

.multitienda-official-view .notebook-panel .section {
    margin-bottom: 0;
}

.multitienda-official-view .section-grid {
    display: grid !important;
    grid-template-columns: minmax(0, 1.35fr) minmax(280px, 360px) !important;
    gap: 24px !important;
    align-items: start !important;
}

.multitienda-official-view .field-input,
.multitienda-official-view .field-select,
.multitienda-official-view .avan-input,
.multitienda-official-view input,
.multitienda-official-view select,
.multitienda-official-view textarea {
    max-width: 100%;
}

.multitienda-official-view .logo-box,
.multitienda-official-view .photo-box {
    max-width: 100%;
}

@media (max-width: 1180px) {
    .multitienda-official-view .section-grid {
        grid-template-columns: 1fr !important;
    }
}
</style>
"""


def _build_marketplace_shell_content(document_html: str, section_id: str) -> str:
    prefixed = _prefix_root_relative_urls(document_html, "/multitienda")
    styles = "\n".join(match.group(0) for match in _STYLE_RE.finditer(prefixed))
    main_match = _MAIN_RE.search(prefixed)
    main_markup = main_match.group(1).strip() if main_match else prefixed

    filtered_scripts: list[str] = []
    for match in _SCRIPT_RE.finditer(prefixed):
        script_markup = match.group(1)
        if "/static/js/backend-navbar.js" in script_markup:
            continue
        if "/static/js/backend-sidebar-core.js" in script_markup:
            continue
        if "initBackendSidebarCore" in script_markup:
            continue
        if "backend_template_sidebar_settings" in script_markup:
            continue
        if 'getElementById("menuBtn")' in script_markup:
            continue
        if 'getElementById("menuPanel")' in script_markup:
            continue
        if 'getElementById("sidebarEditor")' in script_markup:
            continue
        filtered_scripts.append(script_markup)

    return (
        '<div class="multitienda-official-view">'
        + _MODULE_NAVBAR_BOOTSTRAP
        + _MODULE_LAYOUT_OVERRIDES
        + styles
        + '<main class="page">'
        + main_markup
        + "</main>"
        + "".join(filtered_scripts)
        + "</div>"
    )


@lru_cache(maxsize=1)
def _cached_management_shell_content() -> str:
    return _build_marketplace_shell_content(gestion_html(), "gestion")


def _render_official_shell(
    request: Request,
    section_id: str,
    document_html: str,
    *,
    content_is_ready: bool = False,
) -> HTMLResponse:
    context = build_backend_context(
        request,
        title="Multitienda",
        subtitle="Marketplace integrado al backend de SIPET.",
        description="Marketplace multitienda con navegación oficial de SIPET.",
        content=document_html if content_is_ready else _build_marketplace_shell_content(document_html, section_id),
        hide_floating_actions=True,
        show_page_header=False,
        page_title="Multitienda",
        page_description="Marketplace en SIPET",
        section_title="Multitienda",
        section_label="Marketplace",
        module_name="Multitienda",
        module_description="Marketplace en SIPET",
        module_icon="fa-solid fa-store",
        current_module="multitienda",
        current_section=section_id,
        module_sections=_MODULE_SECTIONS,
    )
    return get_templates(request).TemplateResponse(BACKEND_BASE_TEMPLATE, context)


@router.get("/multitienda", include_in_schema=False, response_class=HTMLResponse)
def multitienda_entrypoint(request: Request):
    return _render_official_shell(request, "configuracion", configuracion_html())


@router.get("/multitienda/", include_in_schema=False, response_class=HTMLResponse)
def multitienda_entrypoint_slash(request: Request):
    return _render_official_shell(request, "configuracion", configuracion_html())


@router.get("/multitienda/administracion_tiendas", include_in_schema=False, response_class=HTMLResponse)
def multitienda_gestion_entrypoint(request: Request):
    return _render_official_shell(request, "gestion", _cached_management_shell_content(), content_is_ready=True)


@router.get("/multitienda/configuracion", include_in_schema=False, response_class=HTMLResponse)
def multitienda_config_entrypoint(request: Request):
    return _render_official_shell(request, "configuracion", configuracion_html())


@router.get("/multitienda/productos", include_in_schema=False, response_class=HTMLResponse)
def multitienda_productos_entrypoint(request: Request):
    return _render_official_shell(request, "productos", productos_html())


@router.get("/multitienda/tienda", include_in_schema=False, response_class=HTMLResponse)
def multitienda_tienda_entrypoint(request: Request):
    return _render_official_shell(request, "tienda", tienda_html())


router.mount("/multitienda", marketplace_app)

__all__ = ["router"]
