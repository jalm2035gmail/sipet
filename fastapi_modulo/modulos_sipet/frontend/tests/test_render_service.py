"""
tests/test_render_service.py
─────────────────────────────────────────────────────────────────────────────
Pruebas de render_service — renderizado público de páginas.

• Render inline (sin Jinja2) produce HTML válido con gjs_html.
• Render con página sin HTML produce HTML de fallback (no exception).
• is_home se resuelve correctamente desde el store.
• Cache hit evita que el controlador vuelva a llamar al store.
"""

from __future__ import annotations

import uuid
from unittest.mock import patch, MagicMock

import pytest
from fastapi.responses import HTMLResponse


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def simple_page():
    return {
        "id":        uuid.uuid4().hex,
        "slug":      "inicio",
        "title":     "Inicio",
        "gjs_html":  "<section><h1>Hola mundo</h1></section>",
        "gjs_css":   "h1 { color: red; }",
        "published": True,
        "is_home":   True,
        "blocks":    [],
        "meta":      {},
    }


# ── render_service.render_page ────────────────────────────────────────────────

def test_render_page_returns_html_response(simple_page):
    """render_page devuelve HTMLResponse con el contenido de gjs_html."""
    from fastapi_modulo.modulos_sipet.frontend.servicios import render_service

    with patch.object(render_service, "_try_jinja_render", return_value=None):
        result = render_service.render_page(simple_page)

    assert isinstance(result, HTMLResponse)
    assert b"Hola mundo" in result.body


def test_render_page_includes_css(simple_page):
    from fastapi_modulo.modulos_sipet.frontend.servicios import render_service

    with patch.object(render_service, "_try_jinja_render", return_value=None):
        result = render_service.render_page(simple_page)

    assert b"color: red" in result.body


def test_render_page_empty_html_does_not_raise():
    """Página sin gjs_html ni blocks no levanta excepción."""
    from fastapi_modulo.modulos_sipet.frontend.servicios import render_service

    page = {
        "id": uuid.uuid4().hex, "slug": "empty",
        "title": "Empty", "gjs_html": "", "gjs_css": "",
        "published": True, "is_home": False, "blocks": [], "meta": {},
    }
    with patch.object(render_service, "_try_jinja_render", return_value=None):
        result = render_service.render_page(page)
    assert isinstance(result, HTMLResponse)


def test_render_page_jinja_used_when_available(simple_page):
    """Si _try_jinja_render devuelve HTML, se usa directamente."""
    from fastapi_modulo.modulos_sipet.frontend.servicios import render_service

    expected = HTMLResponse("<html><body>jinja</body></html>")
    with patch.object(render_service, "_try_jinja_render", return_value=expected):
        result = render_service.render_page(simple_page)
    assert result is expected


# ── page_service.resolve_public_home_slug ─────────────────────────────────────

def test_resolve_public_home_slug_returns_home_if_no_is_home_page(patched_store):
    from fastapi_modulo.modulos_sipet.frontend.servicios.page_service import resolve_public_home_slug
    # No pages → default slug should be "inicio"
    slug = resolve_public_home_slug()
    assert isinstance(slug, str)
    assert slug != ""


def test_resolve_public_home_slug_returns_custom_slug(patched_store):
    store = patched_store
    from fastapi_modulo.modulos_sipet.frontend.servicios.page_service import resolve_public_home_slug

    pid = uuid.uuid4().hex
    store.upsert_page(pid, {"slug": "bienvenida", "title": "Bienvenida", "is_home": True, "published": True})
    slug = resolve_public_home_slug()
    assert slug == "bienvenida"


# ── Caché: cache miss → render → cache set  ───────────────────────────────────

def test_render_result_can_be_cached_and_retrieved(simple_page):
    """Simula el patrón cache-aside: miss → render → set → hit."""
    from fastapi_modulo.modulos_sipet.frontend.servicios import render_service, cache_service

    _store: dict = {}

    def fake_get(key):
        return _store.get(key)

    def fake_set(key, value, ttl=None):
        _store[key] = value

    with patch.object(cache_service, "get", side_effect=fake_get), \
         patch.object(cache_service, "set", side_effect=fake_set), \
         patch.object(render_service, "_try_jinja_render", return_value=None):

        cache_key = f"page:{simple_page['slug']}"

        # Cache miss
        cached = cache_service.get(cache_key)
        assert cached is None

        # Render and store
        result = render_service.render_page(simple_page)
        html   = result.body.decode()
        cache_service.set(cache_key, html)

        # Cache hit
        cached = cache_service.get(cache_key)
        assert cached == html
        assert "Hola mundo" in cached
