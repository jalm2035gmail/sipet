from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode

from fastapi_modulo.modulos_sipet.web.servicios import template_service


def auth_page_error(request: Request, message: str, status_code: int):
    username = str(getattr(request.state, "pending_username", "") or "").strip()
    query = {"error": message}
    if username:
        query["usuario"] = username
    return RedirectResponse(url=f"/backend/login?{urlencode(query)}", status_code=303)


def auth_json_error(message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse({"success": False, "error": message}, status_code=status_code)
