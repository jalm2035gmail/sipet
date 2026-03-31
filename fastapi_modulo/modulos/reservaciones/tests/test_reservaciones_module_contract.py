from __future__ import annotations

from pathlib import Path

from scripts.validate_module_architecture import validate_module
from fastapi_modulo.modulos.reservaciones.__manifest__ import MANIFEST
from fastapi_modulo.modulos.reservaciones.controladores.reservaciones import router


MODULE_ROOT = Path(__file__).resolve().parents[1]


def test_reservaciones_passes_architecture_validation() -> None:
    result = validate_module(MODULE_ROOT)

    assert result.ok is True


def test_reservaciones_manifest_declares_module_js_assets() -> None:
    assets = MANIFEST.get("assets") or {}
    declared_js = set(assets.get("js") or [])
    js_files = {
        str(path.relative_to(MODULE_ROOT)).replace("\\", "/")
        for path in MODULE_ROOT.rglob("*.js")
        if "tests" not in path.parts
    }

    assert js_files.issubset(declared_js)


def test_reservaciones_router_imports_successfully() -> None:
    paths = {getattr(route, "path", "") for route in router.routes}

    assert "/reservaciones" in paths
    assert "/api/reservaciones/citas" in paths
