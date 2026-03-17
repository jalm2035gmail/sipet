from __future__ import annotations

from fastapi_modulo.modulos_sipet.modulo_base.bootstrap import init_modulo_base
from fastapi_modulo.modulos_sipet.modulo_base.controladores.api import router as api_router
from fastapi_modulo.modulos_sipet.modulo_base.controladores.assets import router as assets_router
from fastapi_modulo.modulos_sipet.modulo_base.controladores.dependencies import require_modulo_base_access
from fastapi_modulo.modulos_sipet.modulo_base.controladores.pages import router as pages_router
from fastapi_modulo.modulos_sipet.modulo_base.core.router import ModuleRouterBuilder

MODULE_ROUTERS = [
    pages_router,
    api_router,
    assets_router,
]

router = ModuleRouterBuilder(
    access_dependency=require_modulo_base_access,
    init_module=init_modulo_base,
).build_root_router(MODULE_ROUTERS)
