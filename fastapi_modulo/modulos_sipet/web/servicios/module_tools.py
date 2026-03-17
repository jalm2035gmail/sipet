from __future__ import annotations

from pathlib import Path

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.responses import HTMLResponse, Response

from fastapi_modulo.modulos_sipet.web.controladores.backend_shell import render_backend_page
from fastapi_modulo.modulos_sipet.web.servicios.access_service import (
    require_app_access as require_app_access_service,
    require_screen_access as require_screen_access_service,
)
from fastapi_modulo.modulos_sipet.web.servicios.template_context_service import build_backend_context
from fastapi_modulo.modulos_sipet.web.servicios.template_service import render_no_access_module_page


def read_text_file(path: str | Path, fallback: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError:
        return fallback


def text_asset_response(
    path: str | Path,
    *,
    media_type: str,
    fallback: str,
    status_code: int = 200,
) -> Response:
    return Response(read_text_file(path, fallback), media_type=media_type, status_code=status_code)


def asset_version(path: str | Path) -> str:
    try:
        return str(int(Path(path).stat().st_mtime))
    except OSError:
        return "0"


def versioned_asset_url(asset_url: str, path: str | Path) -> str:
    separator = "&" if "?" in asset_url else "?"
    return f"{asset_url}{separator}v={asset_version(path)}"


def scoped_text_asset_response(
    base_dir: str | Path,
    asset_name: str,
    *,
    media_type: str,
    fallback: str,
) -> Response:
    base_path = Path(base_dir).resolve()
    target_path = (base_path / asset_name).resolve()
    try:
        target_path.relative_to(base_path)
    except ValueError:
        return Response(fallback, media_type=media_type, status_code=404)
    if not target_path.exists():
        return Response(fallback, media_type=media_type, status_code=404)
    return text_asset_response(target_path, media_type=media_type, fallback=fallback)


def render_backend_page_html(
    request: Request,
    *,
    title: str,
    description: str,
    content: str,
    hide_floating_actions: bool = True,
    show_page_header: bool = False,
) -> HTMLResponse:
    return render_backend_page(
        request,
        title=title,
        description=description,
        content=content,
        hide_floating_actions=hide_floating_actions,
        show_page_header=show_page_header,
    )


def build_module_backend_context(
    request: Request,
    *,
    title: str,
    description: str = "",
    content: str = "",
    **extra: object,
) -> dict:
    return build_backend_context(
        request,
        title=title,
        description=description,
        content=content,
        **extra,
    )


def render_no_access_page(
    request: Request,
    *,
    title: str,
    description: str,
    message: str = "Sin acceso, consulte con el administrador",
) -> HTMLResponse:
    return render_no_access_module_page(
        request,
        title=title,
        description=description,
        message=message,
    )


def require_app_access(request: Request, app_name: str, detail: str) -> None:
    return require_app_access_service(request, app_name, detail)


def require_screen_access(request: Request, screen_name: str, detail: str, app_name: str = "") -> None:
    return require_screen_access_service(request, screen_name, detail, app_name=app_name)


def json_ok(payload: dict | None = None, status_code: int = 200) -> JSONResponse:
    body = {"success": True}
    if isinstance(payload, dict):
        body.update(payload)
    return JSONResponse(body, status_code=status_code)


def json_error(message: str, *, status_code: int = 400, code: str = "") -> JSONResponse:
    body = {"success": False, "error": str(message)}
    if code:
        body["code"] = code
    return JSONResponse(body, status_code=status_code)
