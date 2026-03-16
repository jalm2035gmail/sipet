from __future__ import annotations

import os
from pathlib import Path

from fastapi import Request
from fastapi.responses import HTMLResponse

from fastapi_modulo.modulos.crm.crm_menu import render_crm_menu
from fastapi_modulo.modulos.web.servicios.module_tools import read_text_file, render_no_access_page

MODULE_DIR = Path(__file__).resolve().parents[1]
CRM_TEMPLATE_PATH = MODULE_DIR / "vistas" / "crm.html"
CRM_CSS_PATH = MODULE_DIR / "static" / "css" / "crm.css"
CRM_JS_DIR = MODULE_DIR / "static" / "js" / "crm"
CRM_JS_PATH = CRM_JS_DIR / "main.js"
def load_crm_page_content(active_panel: str = "contactos") -> str:
    content = read_text_file(CRM_TEMPLATE_PATH, "<p>No se pudo cargar la vista CRM.</p>")
    return content.replace("{{CRM_MENU}}", render_crm_menu(active_panel))


def render_no_access_crm_page(
    request: Request,
    *,
    title: str,
    description: str,
) -> HTMLResponse:
    return render_no_access_page(
        request,
        title=title,
        description=description,
    )
