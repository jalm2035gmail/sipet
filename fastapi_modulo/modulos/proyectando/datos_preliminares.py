import os

from fastapi import APIRouter, Body, Request
from fastapi.responses import HTMLResponse
from fastapi_modulo.modulos.proyectando.data_store import (
    DEFAULT_DATOS_GENERALES,
    load_datos_preliminares_store,
    save_datos_preliminares_store,
)

router = APIRouter()
DATOS_PRELIMINARES_TEMPLATE_PATH = os.path.join(
    "fastapi_modulo", "templates", "modulos", "proyectando", "datos_preliminares.html"
)


def _get_colores_context() -> dict:
    from fastapi_modulo.main import get_colores_context
    return get_colores_context()


@router.post("/api/proyectando/datos-preliminares/datos-generales")
async def guardar_datos_preliminares_generales(data: dict = Body(...)):
    current = load_datos_preliminares_store()
    updated = dict(current)
    for key in DEFAULT_DATOS_GENERALES.keys():
        if key in data:
            updated[key] = str(data.get(key) or "").strip()
    save_datos_preliminares_store(updated)
    return {"success": True, "data": updated}


@router.get("/api/proyectando/datos-preliminares")
async def obtener_datos_preliminares():
    return {"success": True, "data": load_datos_preliminares_store()}


@router.get("/proyectando/datos-preliminares", response_class=HTMLResponse)
def proyectando_datos_preliminares_page(request: Request):
    try:
        with open(DATOS_PRELIMINARES_TEMPLATE_PATH, "r", encoding="utf-8") as fh:
            content = fh.read()
    except OSError:
        content = "<p>No se pudo cargar la vista de datos preliminares.</p>"

    return request.app.state.templates.TemplateResponse(
        "base.html",
        {
            "request": request,
            "title": "Datos preliminares",
            "description": "",
            "page_title": "Datos preliminares",
            "page_description": "",
            "section_label": "",
            "section_title": "",
            "content": content,
            "hide_floating_actions": True,
            "show_page_header": False,
            "view_buttons_html": "",
            "colores": _get_colores_context(),
        },
    )
