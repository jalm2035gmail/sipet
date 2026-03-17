from __future__ import annotations

from fastapi_modulo.modulos_sipet.modulo_base.bootstrap import MODULE_CONFIG, asset_manager
from fastapi_modulo.modulos_sipet.modulo_base.core.router import ModuleRouterBuilder


def modulo_base_css():
    return asset_manager.css_response()


def modulo_base_js():
    return asset_manager.js_response()


router = ModuleRouterBuilder.build_asset_router(
    css_endpoint=modulo_base_css,
    js_endpoint=modulo_base_js,
    assets_prefix=MODULE_CONFIG.assets_prefix,
    asset_basename=MODULE_CONFIG.key,
)
