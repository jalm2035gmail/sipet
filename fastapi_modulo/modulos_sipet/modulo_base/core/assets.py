from __future__ import annotations

from typing import Any

from fastapi import Request, Response
from fastapi.templating import Jinja2Templates

from fastapi_modulo.modulos_sipet.modulo_base.core.module import ModuleConfig
from fastapi_modulo.modulos_sipet.web.servicios.module_tools import read_text_file, text_asset_response, versioned_asset_url


class ModuleAssetManager:
    def __init__(self, config: ModuleConfig) -> None:
        self.config = config
        self.templates = Jinja2Templates(directory=str(self.config.views_dir))

    def render_view(self, name: str, fallback: str = "") -> str:
        return read_text_file(self.config.views_dir / name, fallback)

    def build_template_context(self, request: Request, *, fallback: str = "", extra: dict[str, Any] | None = None) -> dict[str, Any]:
        context = {
            "request": request,
            "module_name": self.config.name,
            "module_key": self.config.key,
            "module_description": self.config.description,
            "module_sections": self.config.sections,
            "module_route": self.config.route,
            "fallback": fallback,
            "asset_urls": {
                "css": versioned_asset_url(f"{self.config.assets_prefix}/{self.config.key}.css", self.config.css_path),
                "js": versioned_asset_url(f"{self.config.assets_prefix}/{self.config.key}.js", self.config.js_path),
            },
        }
        if extra:
            context.update(extra)
        return context

    def template_response(self, request: Request, name: str, *, fallback: str = "", extra: dict[str, Any] | None = None) -> Response:
        context = self.build_template_context(request, fallback=fallback, extra=extra)
        return self.templates.TemplateResponse(name, context)

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
