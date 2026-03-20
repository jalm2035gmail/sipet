from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response
from fastapi_modulo.modulos_sipet.web.servicios.module_tools import (
    read_text_file,
    render_backend_page_html,
    render_no_access_page,
    scoped_text_asset_response,
    text_asset_response,
)

router = APIRouter()

MODULE_DIR = Path(__file__).resolve().parents[1]
VIEWS_DIR = MODULE_DIR / "vistas"
STATIC_CSS_DIR = MODULE_DIR / "static" / "css"
STATIC_JS_DIR = MODULE_DIR / "static" / "js"
LEGACY_TEMPLATES_DIR = Path("fastapi_modulo") / "templates" / "modulos" / "activo_fijo"


def _render_legacy_template_page(
    request: Request,
    *,
    filename: str,
    title: str,
    description: str,
) -> HTMLResponse:
    template_path = LEGACY_TEMPLATES_DIR / filename
    content = read_text_file(template_path, "")
    if not content:
        return render_no_access_page(
            request,
            title=title,
            description=description,
        )
    return render_backend_page_html(
        request,
        title=title,
        description=description,
        content=content,
        show_page_header=True,
    )


@router.get("/activo-fijo", response_class=HTMLResponse)
def activo_fijo_page(request: Request):
    html_path = VIEWS_DIR / "activo_fijo.html"
    menus_path = VIEWS_DIR / "activo_fijo_menus.html"
    content = read_text_file(html_path, "<p>No se pudo cargar Activo Fijo.</p>")
    menus_content = read_text_file(menus_path, "")
    content = content.replace("<!-- AF_MODULE_MENUS -->", menus_content)
    return render_backend_page_html(
        request,
        title="Gestión de Activo Fijo",
        description="Depreciaciones, asignaciones, mantenimiento y bajas de activos.",
        content=content,
        show_page_header=False,
    )


@router.get("/api/activo-fijo/assets/activo_fijo.css")
def activo_fijo_css():
    return text_asset_response(
        STATIC_CSS_DIR / "activo_fijo.css",
        media_type="text/css",
        fallback="/* activo fijo css no disponible */",
    )


@router.get("/api/activo-fijo/assets/activo_fijo/{asset_name}.js")
def activo_fijo_js_asset(asset_name: str):
    return scoped_text_asset_response(
        STATIC_JS_DIR / "activo_fijo",
        f"{asset_name}.js",
        media_type="application/javascript",
        fallback="console.error('Activo fijo JS no disponible');",
    )


@router.get("/api/activo-fijo/assets/activo_fijo.js")
def activo_fijo_js_legacy_asset():
    content = (
        "import '/api/activo-fijo/assets/activo_fijo/index.js';\n"
    )
    return Response(content=content, media_type="application/javascript")


@router.get("/activo-fijo/custodia", response_class=HTMLResponse)
def activo_fijo_custodia_page(request: Request):
    return _render_legacy_template_page(
        request,
        filename="custodia.html",
        title="Custodia",
        description="Préstamo y resguardo de activos fijos.",
    )


@router.get("/activo-fijo/flotilla", response_class=HTMLResponse)
def activo_fijo_flotilla_page(request: Request):
    return _render_legacy_template_page(
        request,
        filename="flotilla.html",
        title="Flotilla",
        description="Gestión de flotilla vehicular.",
    )


@router.get("/activo-fijo/salones", response_class=HTMLResponse)
def activo_fijo_salones_page(request: Request):
    return _render_legacy_template_page(
        request,
        filename="salones.html",
        title="Salones",
        description="Solicitud y gestión de salas de capacitación.",
    )
