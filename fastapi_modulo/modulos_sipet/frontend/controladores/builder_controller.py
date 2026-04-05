"""
controladores/builder_controller.py
─────────────────────────────────────────────────────────────────────────────
Rutas del constructor de páginas frontend y de las páginas estáticas del sitio.

Incluye:
  • Acceso al builder HTML (GET /frontend/builder)
  • API de contexto del usuario para la barra superior (GET /api/backend/me)
  • Rutas de páginas estáticas: inicio, descripcion, funcionalidades
"""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from fastapi_modulo.modulos_sipet.frontend.modelos.frontend_store import (
    get_page_by_slug as store_get_page_by_slug,
)
from fastapi_modulo.modulos_sipet.frontend.servicios.frontend_context_service import get_frontend_context
from fastapi_modulo.modulos_sipet.frontend.servicios.page_service import resolve_public_home_slug
from fastapi_modulo.modulos_sipet.frontend.servicios.render_service import render_page as render_public_page
from fastapi_modulo.modulos_sipet.web.servicios.access_service import require_screen_access
from fastapi_modulo.modulos_sipet.web.servicios.template_context_service import get_login_identity_context
from fastapi_modulo.modulos_sipet.web.servicios.template_service import get_templates

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Builder"])

_BUILDER_TEMPLATE        = os.path.join("fastapi_modulo", "modulos_sipet", "frontend", "vistas", "frontend.html")
_FRONTEND_BUILDER_SCREEN = "frontend.builder"


@router.get("/frontend/builder", response_class=HTMLResponse)
def frontend_builder(request: Request):
    require_screen_access(request, _FRONTEND_BUILDER_SCREEN, detail="Sin acceso al constructor frontend.")
    try:
        with open(_BUILDER_TEMPLATE, "r", encoding="utf-8") as fh:
            return HTMLResponse(fh.read())
    except OSError:
        return HTMLResponse("<h1>Template no encontrado</h1>", status_code=500)


@router.get("/api/backend/me")
def api_backend_me(request: Request):
    return get_frontend_context(request)


@router.get("/backend", response_class=HTMLResponse)
def backend(request: Request):
    del request
    return RedirectResponse(url="/web/inicio", status_code=307)


@router.get("/web", response_class=HTMLResponse)
def backend_alias_root(request: Request):
    del request
    return RedirectResponse(url="/web/inicio", status_code=307)


@router.get("/web/inicio", response_class=HTMLResponse)
def web_inicio(request: Request):
    target_slug = resolve_public_home_slug()
    if target_slug != "inicio":
        return RedirectResponse(url=f"/web/{target_slug}", status_code=307)
    page = store_get_page_by_slug("inicio", published_only=True)
    if page:
        return render_public_page(page)
    login_identity = get_login_identity_context(request)
    return get_templates(request).TemplateResponse(
        "frontend/web_blank.html",
        {
            "request":                  request,
            "title":                    "SIPET",
            "app_favicon_url":          login_identity.get("login_favicon_url"),
            "company_logo_url":         login_identity.get("login_logo_url"),
            "login_company_short_name": login_identity.get("login_company_short_name"),
            "menu_position":            login_identity.get("menu_position"),
        },
    )


@router.get("/backend/descripcion", response_class=HTMLResponse)
def backend_descripcion(request: Request):
    del request
    return RedirectResponse(url="/web/descripcion", status_code=307)


@router.get("/web/descripcion", response_class=HTMLResponse)
def web_descripcion(request: Request):
    login_identity = get_login_identity_context(request)
    return get_templates(request).TemplateResponse(
        "frontend/web.html",
        {
            "request":          request,
            "title":            "SIPET",
            "app_favicon_url":  login_identity.get("login_favicon_url"),
            "company_logo_url": login_identity.get("login_logo_url"),
            "menu_position":    login_identity.get("menu_position"),
        },
    )


@router.get("/backend/funcionalidades", response_class=HTMLResponse)
def backend_funcionalidades(request: Request):
    del request
    return RedirectResponse(url="/web/funcionalidades", status_code=307)


@router.get("/web/funcionalidades", response_class=HTMLResponse)
def web_funcionalidades(request: Request):
    login_identity = get_login_identity_context(request)
    return get_templates(request).TemplateResponse(
        "frontend/modulo_funcionalidades.html",
        {
            "request":          request,
            "title":            "Funcionalidades | SIPET",
            "app_favicon_url":  login_identity.get("login_favicon_url"),
            "company_logo_url": login_identity.get("login_logo_url"),
            "menu_position":    login_identity.get("menu_position"),
        },
    )
