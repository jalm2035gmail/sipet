import os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()
NO_ACCESO_TEMPLATE_PATH = os.path.join("fastapi_modulo", "templates", "no_acceso.html")


def _get_colores_context() -> dict:
    from fastapi_modulo.main import get_colores_context
    return get_colores_context()

@router.get("/proyectando/no-acceso", response_class=HTMLResponse)
def proyectando_no_acceso_page(request: Request):
    try:
        with open(NO_ACCESO_TEMPLATE_PATH, "r", encoding="utf-8") as fh:
            content = fh.read()
    except OSError:
        content = "<p>No hay acceso a esta sección.</p>"
    return request.app.state.templates.TemplateResponse(
        "base.html",
        {
            "request": request,
            "title": "No hay acceso",
            "description": "Acceso denegado a esta sección.",
            "page_title": "No hay acceso",
            "page_description": "Acceso denegado a esta sección.",
            "section_label": "",
            "section_title": "",
            "content": content,
            "hide_floating_actions": True,
            "show_page_header": False,
            "view_buttons_html": "",
            "colores": _get_colores_context(),
        },
    )
