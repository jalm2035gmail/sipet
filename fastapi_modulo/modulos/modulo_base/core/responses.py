from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse

from fastapi_modulo.modulos.modulo_base.core.assets import ModuleAssetManager
from fastapi_modulo.modulos.modulo_base.core.module import ModuleConfig
from fastapi_modulo.modulos.modulo_base.modelos.schemas import APIResponse
from fastapi_modulo.modulos.web.servicios.module_tools import render_backend_page_html


class ModuleResponseBuilder:
    def __init__(self, config: ModuleConfig, assets: ModuleAssetManager) -> None:
        self.config = config
        self.assets = assets

    def page(self, request: Request, *, fallback: str = "") -> HTMLResponse:
        content = self.assets.render_view(self.config.template_name, fallback)
        content = content.replace("{{MODULO_BASE_NAVBAR}}", self.assets.render_view(self.config.navbar_name))
        content = content.replace("{{MODULO_BASE_SIDEBAR}}", self.assets.render_view(self.config.sidebar_name))
        return render_backend_page_html(
            request,
            title=self.config.name,
            description=self.config.description,
            content=content,
            show_page_header=False,
        )

    def success_response(
        self,
        payload: dict[str, Any] | list[Any] | None = None,
        *,
        message: str = "",
        status_code: int = 200,
    ) -> JSONResponse:
        body = APIResponse(ok=True, message=message, data=payload)
        return JSONResponse(body.model_dump(), status_code=status_code)

    def error_response(
        self,
        message: str,
        *,
        payload: dict[str, Any] | list[Any] | None = None,
        status_code: int = 400,
    ) -> JSONResponse:
        body = APIResponse(ok=False, message=message, data=payload)
        return JSONResponse(body.model_dump(), status_code=status_code)

    def forbidden_response(
        self,
        message: str = "Acceso denegado",
        *,
        payload: dict[str, Any] | list[Any] | None = None,
    ) -> JSONResponse:
        return self.error_response(message, payload=payload, status_code=403)

    def json(self, payload: dict[str, Any] | list[Any] | None = None, *, status_code: int = 200, message: str = "") -> JSONResponse:
        if status_code >= 400:
            return self.error_response(message or "Error", payload=payload, status_code=status_code)
        return self.success_response(payload, message=message, status_code=status_code)
