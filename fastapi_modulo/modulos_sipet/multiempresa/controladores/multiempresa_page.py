from __future__ import annotations

import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response

from fastapi_modulo.modulos_sipet.web.controladores.backend_shell import render_backend_page
from fastapi_modulo.modulos.multiempresa.controladores.multiempresa_access_service import get_me_scope

_MODULE_ROOT = os.path.dirname(os.path.dirname(__file__))

router = APIRouter()


@router.get("/multiempresa", response_class=HTMLResponse)
def multiempresa_page(request: Request):
    get_me_scope(request)
    html_path = os.path.join(_MODULE_ROOT, "vistas", "multiempresa.html")
    with open(html_path, encoding="utf-8") as f:
        content = f.read()
    return render_backend_page(
        request,
        title="Multiempresa",
        description="Administración de empresas del sistema SIPET.",
        content=content,
        hide_floating_actions=True,
        show_page_header=False,
    )


@router.get("/api/multiempresa/assets/multiempresa.js")
def multiempresa_js():
    js_path = os.path.join(_MODULE_ROOT, "static", "js", "multiempresa.js")
    with open(js_path, encoding="utf-8") as f:
        content = f.read()
    return Response(content=content, media_type="application/javascript")


@router.get("/api/multiempresa/assets/multiempresa.css")
def multiempresa_css():
    css_path = os.path.join(_MODULE_ROOT, "static", "css", "multiempresa.css")
    with open(css_path, encoding="utf-8") as f:
        content = f.read()
    return Response(content=content, media_type="text/css")
