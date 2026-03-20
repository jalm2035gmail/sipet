from __future__ import annotations

import importlib

from fastapi_modulo.core import module_registry


def test_list_modules_payload_uses_manifest_fafa_when_icon_is_missing(monkeypatch) -> None:
    module = module_registry.ModuleDefinition(
        key="empresa",
        label="Empresa",
        description="Configuración institucional.",
        route="/identidad-institucional",
        icon="",
    )
    monkeypatch.setattr(module_registry, "MODULE_DEFINITIONS", [module])
    monkeypatch.setattr(module_registry, "_read_module_state_map", lambda: {})
    monkeypatch.setattr(module_registry, "is_module_enabled", lambda key, tenant_key=None: True)
    monkeypatch.setattr(
        module_registry,
        "_load_module_metadata",
        lambda _: {
            "manifest": {
                "label": "Empresa",
                "route": "/identidad-institucional",
                "fafa": "fa-solid fa-building",
            }
        },
    )

    payload = module_registry.list_modules_payload(tenant_key="default")

    assert len(payload) == 1
    assert payload[0]["icon"] == "fa-solid fa-building"


def test_multitienda_module_is_registered() -> None:
    module = module_registry.MODULES_BY_KEY["multitienda"]

    assert module.route == "/multitienda"
    assert module.app_access_name == "Multitienda"
    assert module.router_specs[0].module_path == "fastapi_modulo.modulos.multitienda.controladores.multitienda"


def test_multitienda_wrapper_exposes_mount() -> None:
    mod = importlib.import_module("fastapi_modulo.modulos.multitienda.controladores.multitienda")
    paths = [getattr(route, "path", "") for route in mod.router.routes]

    assert "/multitienda" in paths
