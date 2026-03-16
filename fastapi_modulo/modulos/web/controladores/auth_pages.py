from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from fastapi_modulo.modulos.web.servicios import template_service

router = APIRouter()


@router.get("/backend/login", response_class=HTMLResponse)
def backend_login(request: Request):
    return template_service.render_login_template(request)


@router.get("/backend/404", response_class=HTMLResponse)
def backend_not_found(request: Request):
    return template_service.render_not_found_template(request)
