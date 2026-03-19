from __future__ import annotations

import asyncio
import sys
import types

from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.exc import OperationalError
from starlette.requests import Request

from fastapi_modulo.modulos_sipet.web.controladores import backend_middleware
from fastapi_modulo.modulos_sipet.web.controladores.auth_api import backend_login_submit
from fastapi_modulo.modulos_sipet.web.controladores.auth_pages import backend_login


def _request(path: str, method: str = "GET", headers: list[tuple[bytes, bytes]] | None = None, cookies: dict[str, str] | None = None):
    request_headers = list(headers or [])
    if cookies:
        cookie_value = "; ".join(f"{key}={value}" for key, value in cookies.items())
        request_headers.append((b"cookie", cookie_value.encode("latin1")))

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    scope = {
        "type": "http",
        "method": method,
        "scheme": "https",
        "path": path,
        "headers": request_headers,
        "app": types.SimpleNamespace(docs_url=None, state=types.SimpleNamespace(database_setup_required=False)),
    }
    return Request(scope, receive=receive)


def _install_frontend_public_path_stub() -> None:
    frontend_module = types.ModuleType("fastapi_modulo.modulos.frontend.controladores.frontend")
    frontend_module._is_public_frontend_page_path = lambda path: False
    sys.modules["fastapi_modulo.modulos.frontend.controladores.frontend"] = frontend_module


def test_is_public_backend_path_allows_login() -> None:
    _install_frontend_public_path_stub()
    request = _request("/backend/login")
    assert backend_middleware.is_public_backend_path(request, "/backend/login") is True


def test_backend_login_redirects_to_database_setup_when_required() -> None:
    _install_frontend_public_path_stub()
    request = _request("/backend/login")
    request.scope["app"] = types.SimpleNamespace(state=types.SimpleNamespace(database_setup_required=True))

    response = backend_login(request)

    assert response.status_code == 303
    assert response.headers["location"] == "/base_datos/inicializar"


def test_backend_login_submit_redirects_to_database_setup_when_required() -> None:
    _install_frontend_public_path_stub()
    request = _request("/backend/login", method="POST")
    request.scope["app"] = types.SimpleNamespace(state=types.SimpleNamespace(database_setup_required=True))

    response = backend_login_submit(request, usuario="admin", contrasena="secret", codigo_autenticador="")

    assert response.status_code == 303
    assert response.headers["location"] == "/base_datos/inicializar"


def test_backend_login_submit_redirects_to_database_setup_when_schema_is_incomplete(monkeypatch) -> None:
    _install_frontend_public_path_stub()
    request = _request("/backend/login", method="POST")
    fake_db = types.SimpleNamespace(close=lambda: None)
    fake_auth_service = types.SimpleNamespace(
        is_login_rate_limited=lambda request: False,
        register_failed_login_attempt=lambda request: None,
        record_login_attempt=lambda request, username, success: None,
        get_session_local=lambda: (lambda: fake_db),
        find_user_by_login=lambda db, username: (_ for _ in ()).throw(OperationalError("SELECT 1", {}, Exception("missing table"))),
    )

    monkeypatch.setattr("fastapi_modulo.modulos_sipet.web.controladores.auth_api.auth_service", fake_auth_service)

    response = backend_login_submit(request, usuario="admin", contrasena="secret", codigo_autenticador="")

    assert response.status_code == 303
    assert response.headers["location"] == "/base_datos/inicializar"
    assert request.app.state.database_setup_required is True


def test_enforce_backend_login_redirects_without_session(monkeypatch) -> None:
    _install_frontend_public_path_stub()
    monkeypatch.setattr(
        backend_middleware.tenant_context,
        "bind_request_tenant_context",
        lambda request: types.SimpleNamespace(context=types.SimpleNamespace(tenant_id="default"), host_token="token", tenant_token="tenant"),
    )
    monkeypatch.setattr(backend_middleware.tenant_context, "reset_request_tenant_context", lambda binding: None)
    monkeypatch.setattr(backend_middleware, "read_session_cookie", lambda token: None)
    async def call_next(_request):
        return HTMLResponse("ok")

    response = asyncio.run(backend_middleware.enforce_backend_login(_request("/inicio"), call_next))
    assert response.status_code == 303


def test_enforce_backend_login_allows_database_api_with_setup_cookie(monkeypatch) -> None:
    _install_frontend_public_path_stub()
    monkeypatch.setattr(
        backend_middleware.tenant_context,
        "bind_request_tenant_context",
        lambda request: types.SimpleNamespace(context=types.SimpleNamespace(tenant_id="default"), host_token="token", tenant_token="tenant"),
    )
    monkeypatch.setattr(backend_middleware.tenant_context, "reset_request_tenant_context", lambda binding: None)
    monkeypatch.setattr(backend_middleware, "read_session_cookie", lambda token: None)
    monkeypatch.setattr(backend_middleware, "_is_setup_authenticated_request", lambda request: True)

    async def call_next(_request):
        return JSONResponse({"ok": True})

    response = asyncio.run(
        backend_middleware.enforce_backend_login(
            _request("/api/base_datos/inicializar", method="POST"),
            call_next,
        )
    )

    assert response.status_code == 200


def test_enforce_backend_login_blocks_csrf(monkeypatch) -> None:
    _install_frontend_public_path_stub()
    monkeypatch.setattr(
        backend_middleware.tenant_context,
        "bind_request_tenant_context",
        lambda request: types.SimpleNamespace(context=types.SimpleNamespace(tenant_id="default"), host_token="token", tenant_token="tenant"),
    )
    monkeypatch.setattr(backend_middleware.tenant_context, "reset_request_tenant_context", lambda binding: None)
    monkeypatch.setattr(
        backend_middleware,
        "read_session_cookie",
        lambda token: {"username": "admin", "role": "administrador", "tenant_id": "default", "password_fingerprint": "abc"},
    )
    monkeypatch.setattr(backend_middleware, "is_session_bound_to_request", lambda request, session_data: True)
    monkeypatch.setattr(backend_middleware, "validate_csrf_request", lambda request: asyncio.sleep(0, result=False))
    monkeypatch.setattr(backend_middleware, "is_same_origin_request", lambda request: False)
    fake_auth_service = types.SimpleNamespace(
        get_session_local=lambda: (lambda: types.SimpleNamespace(close=lambda: None)),
        is_password_fingerprint_valid=lambda db, username, fingerprint: True,
    )
    import fastapi_modulo.modulos_sipet.web.servicios as servicios_pkg

    monkeypatch.setattr(servicios_pkg, "auth_service", fake_auth_service)
    async def call_next(_request):
        return JSONResponse({"ok": True})

    response = asyncio.run(
        backend_middleware.enforce_backend_login(
            _request("/api/secure", method="POST"),
            call_next,
        )
    )
    assert response.status_code == 403


def test_enforce_backend_login_blocks_screen_access(monkeypatch) -> None:
    _install_frontend_public_path_stub()
    monkeypatch.setattr(
        backend_middleware.tenant_context,
        "bind_request_tenant_context",
        lambda request: types.SimpleNamespace(context=types.SimpleNamespace(tenant_id="default"), host_token="token", tenant_token="tenant"),
    )
    monkeypatch.setattr(backend_middleware.tenant_context, "reset_request_tenant_context", lambda binding: None)
    monkeypatch.setattr(
        backend_middleware,
        "read_session_cookie",
        lambda token: {"username": "admin", "role": "administrador", "tenant_id": "default", "password_fingerprint": "abc"},
    )
    monkeypatch.setattr(backend_middleware, "is_session_bound_to_request", lambda request, session_data: True)
    monkeypatch.setattr(backend_middleware, "get_user_screen_access_levels", lambda request: {"/rrhh/privado": {"read_only": False}})
    monkeypatch.setattr(backend_middleware, "has_screen_access", lambda request, screen_name, app_name="": False)
    fake_auth_service = types.SimpleNamespace(
        get_session_local=lambda: (lambda: types.SimpleNamespace(close=lambda: None)),
        is_password_fingerprint_valid=lambda db, username, fingerprint: True,
    )
    import fastapi_modulo.modulos_sipet.web.servicios as servicios_pkg
    import fastapi_modulo.modulos_sipet.web.servicios.template_service as template_service

    monkeypatch.setattr(servicios_pkg, "auth_service", fake_auth_service)
    monkeypatch.setattr(
        template_service,
        "render_no_access_module_page",
        lambda request, title, description, message="": HTMLResponse(message, status_code=403),
    )
    monkeypatch.setattr(
        backend_middleware,
        "validate_csrf_request",
        lambda request: asyncio.sleep(0, result=True),
    )
    async def call_next(_request):
        return HTMLResponse("ok")

    response = asyncio.run(
        backend_middleware.enforce_backend_login(
            _request("/rrhh/privado"),
            call_next,
        )
    )
    assert response.status_code == 403


def test_bind_request_tenant_context_sets_request_state() -> None:
    from fastapi_modulo.core import tenant_context

    request = _request("/api/secure", headers=[(b"host", b"cliente1.midominio.com")])
    binding = tenant_context.bind_request_tenant_context(request)
    try:
        assert request.state.tenant_id == "cliente1_midominio_com"
        assert request.state.tenant_key == "cliente1_midominio_com"
        assert request.state.access_mode == "tenant"
        assert request.state.db_key
        assert request.state.db_url
    finally:
        tenant_context.reset_request_tenant_context(binding)


def test_enforce_backend_login_rejects_session_for_other_tenant(monkeypatch) -> None:
    _install_frontend_public_path_stub()
    monkeypatch.setattr(
        backend_middleware.tenant_context,
        "bind_request_tenant_context",
        lambda request: types.SimpleNamespace(context=types.SimpleNamespace(tenant_id="tenant_a"), host_token="token", tenant_token="tenant"),
    )
    monkeypatch.setattr(backend_middleware.tenant_context, "reset_request_tenant_context", lambda binding: None)
    monkeypatch.setattr(
        backend_middleware,
        "read_session_cookie",
        lambda token: {"username": "admin", "role": "administrador", "tenant_id": "tenant_b", "host": "otra.midominio.com"},
    )
    monkeypatch.setattr(backend_middleware, "is_session_bound_to_request", lambda request, session_data: False)

    async def call_next(_request):
        return HTMLResponse("ok")

    response = asyncio.run(backend_middleware.enforce_backend_login(_request("/api/secure"), call_next))
    assert response.status_code == 401
