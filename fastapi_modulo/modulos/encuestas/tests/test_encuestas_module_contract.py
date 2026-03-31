from __future__ import annotations

from pathlib import Path

from fastapi_modulo.modulos.encuestas.__manifest__ import MANIFEST
from fastapi_modulo.modulos.encuestas.controladores.encuesta import _response_asset_urls


MODULE_ROOT = Path(__file__).resolve().parents[1]


def test_encuestas_manifest_declares_module_assets() -> None:
    assets = MANIFEST.get("assets") or {}
    declared_css = set(assets.get("css") or [])
    declared_js = set(assets.get("js") or [])

    css_files = {
        str(path.relative_to(MODULE_ROOT)).replace("\\", "/")
        for path in MODULE_ROOT.rglob("*.css")
        if "tests" not in path.parts
    }
    js_files = {
        str(path.relative_to(MODULE_ROOT)).replace("\\", "/")
        for path in MODULE_ROOT.rglob("*.js")
        if "tests" not in path.parts
    }

    assert css_files.issubset(declared_css)
    assert js_files.issubset(declared_js)


def test_encuestas_declares_own_tests() -> None:
    test_files = [path for path in (MODULE_ROOT / "tests").glob("test_*.py") if path.is_file()]

    assert test_files


def test_response_page_uses_module_asset_routes() -> None:
    assets = _response_asset_urls()
    public_assets = _response_asset_urls(public=True)

    assert assets["css_url"].startswith("/modulos/encuestas/encuesta.css")
    assert assets["js_url"].startswith("/modulos/encuestas/encuesta_response.js")
    assert public_assets["css_url"].startswith("/api/public/encuestas-static/encuesta.css")
    assert public_assets["js_url"].startswith("/api/public/encuestas-static/encuesta_response.js")
