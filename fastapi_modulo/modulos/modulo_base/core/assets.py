from __future__ import annotations

from fastapi import Response

from fastapi_modulo.modulos.modulo_base.core.module import ModuleConfig
from fastapi_modulo.modulos.web.servicios.module_tools import read_text_file, text_asset_response


class ModuleAssetManager:
    def __init__(self, config: ModuleConfig) -> None:
        self.config = config

    def render_view(self, name: str, fallback: str = "") -> str:
        return read_text_file(self.config.views_dir / name, fallback)

    def css_response(self) -> Response:
        return text_asset_response(
            self.config.css_path,
            media_type="text/css",
            fallback=f"/* {self.config.key} css */",
        )

    def js_response(self) -> Response:
        return text_asset_response(
            self.config.js_path,
            media_type="application/javascript",
            fallback=f"console.error('{self.config.key} js no disponible');",
        )
