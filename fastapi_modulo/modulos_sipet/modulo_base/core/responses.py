from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from fastapi_modulo.modulos_sipet.modulo_base.core.assets import ModuleAssetManager
from fastapi_modulo.modulos_sipet.modulo_base.core.module import ModuleConfig
from fastapi_modulo.modulos_sipet.modulo_base.modelos.schemas import APIErrorDetail, APIResponse

class ModuleResponseBuilder:
    def __init__(self, config: ModuleConfig, assets: ModuleAssetManager) -> None:
        self.config = config
        self.assets = assets

    def page(self, request: Request, *, fallback: str = ""):
        return self.assets.template_response(request, self.config.template_name, fallback=fallback)

    def success_response(
        self,
        payload: dict[str, Any] | list[Any] | None = None,
        *,
        message: str = "",
        status_code: int = 200,
        errors: list[APIErrorDetail] | None = None,
    ) -> JSONResponse:
        body = APIResponse(ok=True, message=message, data=payload, errors=errors or [])
        return JSONResponse(body.model_dump(), status_code=status_code)

    def error_response(
        self,
        message: str,
        *,
        payload: dict[str, Any] | list[Any] | None = None,
        status_code: int = 400,
        errors: list[APIErrorDetail] | None = None,
    ) -> JSONResponse:
        body = APIResponse(
            ok=False,
            message=message,
            data=payload,
            errors=errors or [APIErrorDetail(type="error", message=message)],
        )
        return JSONResponse(body.model_dump(), status_code=status_code)

    def forbidden_response(
        self,
        message: str = "Acceso denegado",
        *,
        payload: dict[str, Any] | list[Any] | None = None,
        errors: list[APIErrorDetail] | None = None,
    ) -> JSONResponse:
        return self.error_response(
            message,
            payload=payload,
            status_code=403,
            errors=errors or [APIErrorDetail(type="permission_error", message=message)],
        )

    def json(self, payload: dict[str, Any] | list[Any] | None = None, *, status_code: int = 200, message: str = "") -> JSONResponse:
        if status_code >= 400:
            return self.error_response(message or "Error", payload=payload, status_code=status_code)
        return self.success_response(payload, message=message, status_code=status_code)
