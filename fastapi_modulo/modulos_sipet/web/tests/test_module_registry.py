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
    monkeypatch.setattr(module_registry, "is_supported_module", lambda _: True)
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


def test_list_modules_payload_skips_legacy_modules(monkeypatch) -> None:
    legacy_module = module_registry.ModuleDefinition(
        key="legacy_demo",
        label="Legacy",
        description="Legacy",
        manifest_file="fastapi_modulo/modulos/legacy_demo/__manifest__.py",
        route="/legacy",
    )

    monkeypatch.setattr(module_registry, "MODULE_DEFINITIONS", [legacy_module])
    monkeypatch.setattr(module_registry, "_read_module_state_map", lambda: {})

    payload = module_registry.list_modules_payload(tenant_key="default")

    assert payload == []


def test_multitienda_module_is_registered() -> None:
    module = module_registry.MODULES_BY_KEY["multitienda"]

    assert module.route == "/multitienda"
    assert module.app_access_name == "Multitienda"
    assert module.router_specs[0].module_path == "fastapi_modulo.modulos.multitienda.controladores.multitienda"


def test_multitienda_wrapper_exposes_mount() -> None:
    mod = importlib.import_module("fastapi_modulo.modulos.multitienda.controladores.multitienda")
    paths = [getattr(route, "path", "") for route in mod.router.routes]

    assert "/multitienda" in paths


def test_list_modules_payload_discovers_new_manifest_on_refresh(monkeypatch, tmp_path) -> None:
    module_dir = tmp_path / "nuevo_modulo"
    module_dir.mkdir()
    manifest_path = module_dir / "__manifest__.py"
    manifest_path.write_text(
        "MANIFEST = {\n"
        "    'name': 'nuevo_modulo',\n"
        "    'label': 'Nuevo modulo',\n"
        "    'description': 'Detectado desde tests.',\n"
        "    'route': '/nuevo-modulo',\n"
        "    'icon': 'fa-solid fa-box',\n"
        "    'installable': True,\n"
        "}\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(module_registry, "MODULE_DEFINITIONS", [])
    monkeypatch.setattr(module_registry, "MODULES_BY_KEY", {})
    monkeypatch.setattr(module_registry, "APP_ACCESS_TO_MODULE", {})
    monkeypatch.setattr(module_registry, "_read_module_state_map", lambda: {})
    monkeypatch.setattr(module_registry, "is_module_enabled", lambda key, tenant_key=None: True)
    monkeypatch.setattr(
        module_registry,
        "_iter_discoverable_manifest_files",
        lambda: [("fastapi_modulo.modulos", str(manifest_path))],
    )

    payload = module_registry.list_modules_payload(refresh=True, include_legacy=True)

    assert [item["key"] for item in payload] == ["nuevo_modulo"]
    assert payload[0]["label"] == "Nuevo modulo"
    assert payload[0]["route"] == "/nuevo-modulo"
