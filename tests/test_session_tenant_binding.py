from fastapi import Response
from starlette.requests import Request

from fastapi_modulo.modulos_sipet.web.servicios.session_service import (
    apply_auth_cookies,
    build_session_cookie,
    is_session_bound_to_request,
    read_session_cookie,
)


def _request(host: str = "cliente1.midominio.com", tenant_id: str = "cliente1_midominio_com"):
    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    scope = {
        "type": "http",
        "method": "GET",
        "scheme": "https",
        "path": "/backend",
        "headers": [(b"host", host.encode("latin1"))],
        "state": {"tenant_id": tenant_id},
    }
    request = Request(scope, receive=receive)
    request.state.tenant_id = tenant_id
    return request


def test_build_and_read_session_cookie_with_host() -> None:
    token = build_session_cookie("demo", "administrador", "cliente1_midominio_com", "cliente1.midominio.com")
    payload = read_session_cookie(token)
    assert payload is not None
    assert payload["tenant_id"] == "cliente1_midominio_com"
    assert payload["host"] == "cliente1.midominio.com"


def test_is_session_bound_to_request() -> None:
    request = _request()
    session_data = {
        "username": "demo",
        "role": "administrador",
        "tenant_id": "cliente1_midominio_com",
        "host": "cliente1.midominio.com",
    }
    assert is_session_bound_to_request(request, session_data) is True
    session_data["host"] = "cliente2.midominio.com"
    assert is_session_bound_to_request(request, session_data) is False


def test_apply_auth_cookies_uses_request_tenant_context() -> None:
    request = _request()
    response = Response()
    apply_auth_cookies(response, request, "demo", "administrador")
    cookies = response.headers.getlist("set-cookie")
    assert any("tenant_id=cliente1_midominio_com" in value for value in cookies)
