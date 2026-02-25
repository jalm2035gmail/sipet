import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter()
CRECIMIENTO_GENERAL_TEMPLATE_PATH = os.path.join(
    "fastapi_modulo", "templates", "modulos", "proyectando", "crecimiento_general.html"
)


@router.get("/proyectando/crecimiento-general", response_class=HTMLResponse)
def proyectando_crecimiento_general_page(request: Request):
    try:
        with open(CRECIMIENTO_GENERAL_TEMPLATE_PATH, "r", encoding="utf-8") as fh:
            content = fh.read()
    except OSError:
        content = "<p>No se pudo cargar la vista de crecimiento general.</p>"
    return request.app.state.templates.TemplateResponse(
        "base.html",
        {
            "request": request,
            "title": "Crecimiento general",
            "description": "",
            "page_title": "Crecimiento general",
            "page_description": "",
            "section_label": "",
            "section_title": "",
            "content": content,
            "hide_floating_actions": True,
            "show_page_header": False,
            "view_buttons_html": "",
        },
    )


@router.get("/proyectando/crecimiento-general/activo-total", response_class=HTMLResponse)
def proyectando_crecimiento_activo_total_page(request: Request):
    return RedirectResponse(url="/proyectando/crecimiento-general", status_code=307)
