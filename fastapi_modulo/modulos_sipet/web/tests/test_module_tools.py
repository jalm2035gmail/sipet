from __future__ import annotations

import sys
import tempfile
import types
from pathlib import Path

import pytest
from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse

import fastapi_modulo.modulos_sipet.web.servicios.module_tools as module_tools
from fastapi_modulo.modulos_sipet.web.servicios.module_tools import (
    asset_version,
    build_module_backend_context,
    json_error,
    json_ok,
    read_text_file,
    render_backend_page_html,
    render_no_access_page,
    require_app_access,
    require_screen_access,
    scoped_text_asset_response,
    text_asset_response,
    versioned_asset_url,
)

fake_main = types.ModuleType("fastapi_modulo.main")


def _fake_render_backend_page(
    request: Request,
    title: str,
    description: str = "",
    content: str = "",
    **_: object,
) -> HTMLResponse:
    return HTMLResponse(f"<html><title>{title}</title><body>{content}</body></html>")


def _fake_render_no_access_module_page(
    request: Request,
    title: str,
    description: str = "",
    message: str = "",
) -> HTMLResponse:
    return HTMLResponse(f"<html><title>{title}</title><body>{message}</body></html>", status_code=403)


def _fake_get_user_app_access(request: Request) -> list[str]:
    return getattr(request.state, "app_access", [])


def _fake_is_admin_or_superadmin(request: Request) -> bool:
    return getattr(request.state, "is_admin", False)


fake_main.render_backend_page = _fake_render_backend_page
fake_main._render_no_access_module_page = _fake_render_no_access_module_page
fake_main._get_user_app_access = _fake_get_user_app_access
fake_main.is_admin_or_superadmin = _fake_is_admin_or_superadmin
fake_main.get_colores_context = lambda: {}
fake_main.build_view_buttons_html = lambda *_args, **_kwargs: ""
sys.modules["fastapi_modulo.main"] = fake_main


class _State:
    app_access = ["CRM"]
    is_admin = False


class _Request:
    state = _State()


def test_read_text_file_returns_fallback() -> None:
    assert read_text_file("/missing/file.txt", "fallback") == "fallback"


def test_text_asset_response_reads_content() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        asset = Path(temp_dir) / "asset.js"
        asset.write_text("console.log('ok')", encoding="utf-8")
        response = text_asset_response(asset, media_type="application/javascript", fallback="x")
        assert response.status_code == 200
        assert response.body == b"console.log('ok')"


def test_scoped_text_asset_response_blocks_escape() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        response = scoped_text_asset_response(
            temp_dir,
            "../evil.js",
            media_type="application/javascript",
            fallback="blocked",
        )
        assert response.status_code == 404


def test_render_helpers_and_require_access() -> None:
    request = _Request()
    module_tools.render_backend_page = _fake_render_backend_page
    module_tools.render_no_access_module_page = _fake_render_no_access_module_page
    module_tools.require_app_access_service = lambda req, app_name, detail: None if app_name == "CRM" else (_ for _ in ()).throw(Exception(detail))
    module_tools.require_screen_access_service = lambda req, screen_name, detail, app_name="": None if screen_name == "/crm" else (_ for _ in ()).throw(Exception(detail))
    module_tools.build_backend_context = lambda req, **kwargs: {"title": kwargs.get("title"), "content": kwargs.get("content")}
    page = render_backend_page_html(request, title="T", description="D", content="OK")
    denied = render_no_access_page(request, title="X", description="Y")
    assert page.status_code == 200
    assert denied.status_code == 403
    require_app_access(request, "CRM", "forbidden")
    require_screen_access(request, "/crm", "forbidden")
    with pytest.raises(Exception):
        require_app_access(request, "Intelicoop", "forbidden")
    with pytest.raises(Exception):
        require_screen_access(request, "/pld", "forbidden")
    assert build_module_backend_context(request, title="Panel", content="ok")["title"] == "Panel"


def test_json_helpers_and_asset_versioning(tmp_path: Path) -> None:
    asset = tmp_path / "asset.css"
    asset.write_text("body{}", encoding="utf-8")
    ok_response = json_ok({"data": 1})
    error_response = json_error("fallo", status_code=422, code="invalid")
    assert isinstance(ok_response, JSONResponse)
    assert ok_response.body == b'{"success":true,"data":1}'
    assert error_response.status_code == 422
    assert asset_version(asset) != "0"
    assert versioned_asset_url("/static/asset.css", asset).startswith("/static/asset.css?v=")
