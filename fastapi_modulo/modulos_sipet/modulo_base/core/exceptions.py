from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from fastapi_modulo.modulos_sipet.modulo_base.modelos.schemas import APIErrorDetail, APIErrorResponse


class ModuleBaseError(Exception):
    status_code = 400
    error_type = "module_base_error"

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        error_type: str | None = None,
        payload: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.payload = payload
        if status_code is not None:
            self.status_code = status_code
        if error_type is not None:
            self.error_type = error_type

    def to_response(self) -> APIErrorResponse:
        return APIErrorResponse(
            ok=False,
            message=self.message,
            data=self.payload,
            errors=[APIErrorDetail(type=self.error_type, message=self.message)],
        )


class ModuleBasePermissionError(ModuleBaseError):
    status_code = 403
    error_type = "permission_error"


class ModuleBaseValidationError(ModuleBaseError):
    status_code = 422
    error_type = "validation_error"


def install_module_exception_handlers(app: FastAPI) -> None:
    if ModuleBaseError not in app.exception_handlers:
        async def _module_base_error_handler(_: Request, exc: ModuleBaseError) -> JSONResponse:
            body = exc.to_response()
            return JSONResponse(body.model_dump(), status_code=exc.status_code)

        app.add_exception_handler(ModuleBaseError, _module_base_error_handler)

    if RequestValidationError not in app.exception_handlers:
        async def _validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
            body = APIErrorResponse(
                ok=False,
                message="Solicitud invalida",
                errors=[
                    APIErrorDetail(
                        type="validation_error",
                        message=error["msg"],
                        field=".".join(str(item) for item in error["loc"]),
                    )
                    for error in exc.errors()
                ],
            )
            return JSONResponse(body.model_dump(), status_code=422)

        app.add_exception_handler(RequestValidationError, _validation_error_handler)
