from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from fastapi_modulo.modulos_sipet.modulo_base.core.assets import ModuleAssetManager
from fastapi_modulo.modulos_sipet.modulo_base.core.exceptions import install_module_exception_handlers
from fastapi_modulo.modulos_sipet.modulo_base.core.module import BaseModule, ModuleConfig
from fastapi_modulo.modulos_sipet.modulo_base.core.permissions import ModulePermissionRegistry
from fastapi_modulo.modulos_sipet.modulo_base.core.responses import ModuleResponseBuilder
from fastapi_modulo.modulos_sipet.modulo_base.repositorios.common import ensure_modulo_base_schema

MODULE_DIR = Path(__file__).resolve().parent

MODULE_CONFIG = ModuleConfig(
    key="modulo_base",
    name="Modulo base",
    base_path=MODULE_DIR,
    route="/modulo-base",
    api_prefix="/api/modulo-base",
    uses_migrations=True,
    requires_data_bootstrap=False,
    requires_seeds=False,
    allow_create_all_in_dev=True,
    description="Framework interno para construir modulos SIPET con contratos reutilizables.",
    sections=(
        "core",
        "controladores",
        "modelos",
        "migrations",
        "repositorios",
        "servicios",
        "seguridad",
        "vistas",
        "static",
        "tests",
    ),
)

asset_manager = ModuleAssetManager(MODULE_CONFIG)
response_builder = ModuleResponseBuilder(MODULE_CONFIG, asset_manager)
permission_registry = ModulePermissionRegistry(
    module_name=MODULE_CONFIG.key,
    permissions_path=MODULE_DIR / "seguridad" / "permisos.json",
    detail="Acceso restringido al módulo base",
)


class ModuloBaseModule(BaseModule):
    def __init__(self) -> None:
        permissions = [permission.code for permission in permission_registry.load()]
        super().__init__(MODULE_CONFIG, permissions=permissions)
        self.router = None
        self.assets: dict[str, str] = {}

    def init(self) -> None:
        ensure_modulo_base_schema(
            allow_create_all_in_dev=self.config.allow_create_all_in_dev,
            uses_migrations=self.config.uses_migrations,
        )
        if self.requires_data_bootstrap:
            bootstrap_modulo_base_data()
        if self.requires_seeds:
            seed_modulo_base_data()

    def register_routes(self, app: FastAPI) -> None:
        from fastapi_modulo.modulos_sipet.modulo_base.controladores.modulo_base import router

        install_module_exception_handlers(app)
        self.router = router
        app.include_router(router)

    def register_assets(self) -> None:
        self.assets = {
            "css": str(MODULE_CONFIG.css_path),
            "js": str(MODULE_CONFIG.js_path),
        }


module = ModuloBaseModule()


def bootstrap_modulo_base_data() -> None:
    return None


def seed_modulo_base_data() -> None:
    return None


def init_modulo_base() -> None:
    module.init()
