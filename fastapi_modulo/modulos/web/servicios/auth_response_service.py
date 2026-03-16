from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from fastapi_modulo.modulos.web.servicios import template_service


def auth_page_error(request: Request, message: str, status_code: int):
    return template_service.render_login_template(
        request,
        login_error=message,
        status_code=status_code,
    )


def auth_json_error(message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse({"success": False, "error": message}, status_code=status_code)
