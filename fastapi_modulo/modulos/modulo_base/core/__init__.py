from fastapi_modulo.modulos.modulo_base.core.audit import TenantAuditMixin
from fastapi_modulo.modulos.modulo_base.core.assets import ModuleAssetManager
from fastapi_modulo.modulos.modulo_base.core.module import BaseModule, ModuleConfig
from fastapi_modulo.modulos.modulo_base.core.permissions import (
    STANDARD_MODULE_ACTIONS,
    ModulePermission,
    ModulePermissionAction,
    ModulePermissionRegistry,
    build_standard_permissions,
)
from fastapi_modulo.modulos.modulo_base.core.repository import BaseRepository, SQLAlchemyRepository
from fastapi_modulo.modulos.modulo_base.core.responses import ModuleResponseBuilder
from fastapi_modulo.modulos.modulo_base.core.router import ModuleRouterBuilder
from fastapi_modulo.modulos.modulo_base.core.service import BaseModuleService, BaseService

__all__ = [
    "BaseModuleService",
    "BaseModule",
    "BaseRepository",
    "BaseService",
    "ModuleAssetManager",
    "ModuleConfig",
    "ModulePermission",
    "ModulePermissionAction",
    "ModulePermissionRegistry",
    "ModuleResponseBuilder",
    "ModuleRouterBuilder",
    "STANDARD_MODULE_ACTIONS",
    "SQLAlchemyRepository",
    "TenantAuditMixin",
    "build_standard_permissions",
]
