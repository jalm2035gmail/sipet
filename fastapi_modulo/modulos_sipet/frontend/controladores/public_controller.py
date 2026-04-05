"""
controladores/public_controller.py
─────────────────────────────────────────────────────────────────────────────
Rutas de servicio público de páginas construidas en el frontend builder.

Rutas:
  GET /p/{slug}           → página pública (con caché)
  GET /backend/{slug}     → alias legacy, redirige a /web/{slug}
  GET /web/{slug}         → página pública por alias web (con caché)
  GET /p-preview/{slug}   → preview de borrador sin caché
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse

from fastapi_modulo.modulos_sipet.frontend.modelos.frontend_store import (
    get_page_by_slug as store_get_page_by_slug,
)
from fastapi_modulo.modulos_sipet.frontend.servicios import cache_service
from fastapi_modulo.modulos_sipet.frontend.servicios.render_service import render_page as render_public_page

router = APIRouter(tags=["Public Pages"])

_404_HTML = "<h1 style='font-family:sans-serif;padding:40px'>Página no encontrada</h1>"


@router.get("/p/{slug}", response_class=HTMLResponse)
def public_page(slug: str):
    cached = cache_service.get(slug)
    if cached:
        return HTMLResponse(cached)
    page = store_get_page_by_slug(slug, published_only=True)
    if not page:
        return HTMLResponse(_404_HTML, status_code=404)
    response = render_public_page(page)
    cache_service.set(slug, response.body.decode("utf-8"))
    return response


@router.get("/backend/{slug}", response_class=HTMLResponse)
def public_page_backend(slug: str):
    """Alias legacy: redirige páginas públicas de /backend/<slug> a /web/<slug>."""
    return RedirectResponse(url=f"/web/{slug}", status_code=307)


@router.get("/web/{slug}", response_class=HTMLResponse)
def public_page_web_alias(slug: str):
    cache_key = f"web:{slug}"
    cached = cache_service.get(cache_key)
    if cached:
        return HTMLResponse(cached)
    page = store_get_page_by_slug(slug, published_only=True)
    if not page:
        return HTMLResponse(_404_HTML, status_code=404)
    response = render_public_page(page)
    cache_service.set(cache_key, response.body.decode("utf-8"))
    return response


@router.get("/p-preview/{slug}", response_class=HTMLResponse)
def preview_page(slug: str):
    """Preview de borrador — sin caché, accesible desde el builder."""
    page = store_get_page_by_slug(slug, published_only=False)
    if not page:
        return HTMLResponse(_404_HTML, status_code=404)
    return render_public_page(page)
