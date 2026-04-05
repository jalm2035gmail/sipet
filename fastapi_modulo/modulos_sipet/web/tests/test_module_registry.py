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


def test_list_modules_payload_includes_modules_directory_entries(monkeypatch) -> None:
    legacy_module = module_registry.ModuleDefinition(
        key="organizacion_demo",
        label="Organizacion",
        description="Organizacion",
        manifest_file="fastapi_modulo/modulos/legacy_demo/__manifest__.py",
        route="/legacy",
    )

    monkeypatch.setattr(module_registry, "MODULE_DEFINITIONS", [legacy_module])
    monkeypatch.setattr(module_registry, "_read_module_state_map", lambda: {})
    monkeypatch.setattr(module_registry, "is_module_enabled", lambda key, tenant_key=None: True)

    payload = module_registry.list_modules_payload(tenant_key="default")

    assert [item["key"] for item in payload] == ["organizacion_demo"]


def test_multitienda_module_is_registered() -> None:
    module = module_registry.MODULES_BY_KEY["multitienda"]

    assert module.route == "/multitienda"
    assert module.app_access_name == "Multitienda"
    assert module.router_specs[0].module_path == "fastapi_modulo.modulos.multitienda.controladores.multitienda"


def test_backend_module_payload_uses_settings_route() -> None:
    backend_payload = next(item for item in module_registry.list_modules_payload() if item["key"] == "backend")

    assert backend_payload["route"] == "/ajustes/configuracion"


def test_intelicoop_module_is_supported() -> None:
    module = module_registry.MODULES_BY_KEY["intelicoop"]

    assert module_registry.is_supported_module(module) is True


def test_multitienda_wrapper_exposes_mount() -> None:
    mod = importlib.import_module("fastapi_modulo.modulos.multitienda.controladores.multitienda")
    paths = [getattr(route, "path", "") for route in mod.router.routes]

    assert "/multitienda" in paths


def test_set_module_enabled_inserts_missing_setting_row(monkeypatch) -> None:
    module = module_registry.ModuleDefinition(
        key="multitienda",
        label="Multitienda",
        description="Marketplace multitienda.",
        route="/multitienda",
        manageable=True,
    )
    monkeypatch.setattr(module_registry, "MODULES_BY_KEY", {"multitienda": module})
    monkeypatch.setattr(module_registry, "is_supported_module", lambda _: True)
    monkeypatch.setattr(module_registry, "_ensure_module_settings_table", lambda: None)
    monkeypatch.setattr(
        module_registry,
        "list_modules_payload",
        lambda: [{"key": "multitienda", "enabled": True}],
    )

    statements: list[str] = []

    class _Result:
        def __init__(self, rowcount: int) -> None:
            self.rowcount = rowcount

    class _Conn:
        def execute(self, statement, params):
            sql = str(statement)
            statements.append(sql)
            if "UPDATE system_module_settings" in sql:
                return _Result(0)
            return _Result(1)

    class _Begin:
        def __enter__(self):
            return _Conn()

        def __exit__(self, exc_type, exc, tb):
            return False

    class _Engine:
        def begin(self):
            return _Begin()

    monkeypatch.setattr(module_registry, "get_admin_engine", lambda: _Engine())

    payload = module_registry.set_module_enabled("multitienda", True)

    assert payload["key"] == "multitienda"
    assert payload["restart_required"] is True
    assert any("UPDATE system_module_settings" in sql for sql in statements)
    assert any("INSERT INTO system_module_settings" in sql for sql in statements)


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


def test_refresh_module_registry_skips_manifest_already_registered(monkeypatch, tmp_path) -> None:
    module_dir = tmp_path / "identidad_institucional"
    module_dir.mkdir()
    manifest_path = module_dir / "__manifest__.py"
    manifest_path.write_text(
        "MANIFEST = {\n"
        "    'name': 'identidad_institucional',\n"
        "    'label': 'Empresa',\n"
        "    'description': 'Duplicado.',\n"
        "    'route': '/identidad-institucional',\n"
        "    'icon': 'fa-solid fa-building',\n"
        "    'installable': True,\n"
        "}\n",
        encoding="utf-8",
    )

    existing = module_registry.ModuleDefinition(
        key="empresa",
        label="Empresa",
        description="Configuración institucional.",
        route="/identidad-institucional",
        icon="fa-solid fa-building",
        manifest_file="fastapi_modulo/modulos_sipet/identidad_institucional/__manifest__.py",
    )
    monkeypatch.setattr(module_registry, "MODULE_DEFINITIONS", [existing])
    monkeypatch.setattr(module_registry, "MODULES_BY_KEY", {"empresa": existing})
    monkeypatch.setattr(module_registry, "APP_ACCESS_TO_MODULE", {})
    monkeypatch.setattr(
        module_registry,
        "_iter_discoverable_manifest_files",
        lambda: [("fastapi_modulo.modulos", str(manifest_path))],
    )

    discovered = module_registry.refresh_module_registry_from_disk()

    assert discovered == []
    assert [module.key for module in module_registry.MODULE_DEFINITIONS] == ["empresa"]


def test_is_module_enabled_returns_true_when_router_module_is_enabled_for_any_tenant(monkeypatch) -> None:
    module = module_registry.ModuleDefinition(
        key="encuestas",
        label="Encuestas",
        description="Campañas y resultados.",
        route="/encuestas",
        manageable=True,
        default_enabled=False,
        router_specs=[module_registry.RouterSpec("fastapi_modulo.modulos.encuestas.controladores.encuesta")],
    )
    monkeypatch.setattr(module_registry, "MODULES_BY_KEY", {"encuestas": module})
    monkeypatch.setattr(module_registry, "is_supported_module", lambda _: True)
    monkeypatch.setattr(module_registry, "_read_installed_app_keys_for_tenant", lambda tenant_key: None)
    monkeypatch.setattr(module_registry, "_read_module_state_map", lambda: {"encuestas": 0})
    monkeypatch.setattr(module_registry, "_has_enabled_tenant_installation", lambda module_key: module_key == "encuestas")

    assert module_registry.is_module_enabled("encuestas") is True


def test_read_installed_app_keys_for_tenant_returns_none_when_tenant_has_no_rows(monkeypatch) -> None:
    class _Query:
        def __init__(self, rows):
            self._rows = rows

        def filter(self, *args, **kwargs):
            return self

        def first(self):
            return self._rows[0] if self._rows else None

        def all(self):
            return self._rows

    class _Session:
        def query(self, *args, **kwargs):
            return _Query([])

        def close(self):
            return None

    monkeypatch.setattr(module_registry, "get_admin_session_factory", lambda: (lambda: _Session()))

    assert module_registry._read_installed_app_keys_for_tenant("oaxaca") is None


def test_read_installed_app_keys_for_tenant_uses_local_alias_fallback(monkeypatch) -> None:
    class _Query:
        def __init__(self, rows):
            self._rows = rows

        def filter(self, *args, **kwargs):
            return self

        def first(self):
            return self._rows[0] if self._rows else None

        def all(self):
            return self._rows

    class _Session:
        def __init__(self):
            self._queries = [
                [],
                [("multitienda",)],
            ]

        def query(self, *args, **kwargs):
            return _Query(self._queries.pop(0))

        def close(self):
            return None

    monkeypatch.setattr(module_registry, "get_admin_session_factory", lambda: (lambda: _Session()))

    assert module_registry._read_installed_app_keys_for_tenant("default") == {"multitienda"}
