from __future__ import annotations

from pathlib import Path

from fastapi_modulo.modulos.personalizacion.__manifest__ import MANIFEST


MODULE_ROOT = Path(__file__).resolve().parents[1]


def test_personalizacion_manifest_declares_module_assets() -> None:
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


def test_personalizacion_declares_own_tests() -> None:
    test_files = [path for path in (MODULE_ROOT / "tests").glob("test_*.py") if path.is_file()]

    assert test_files
