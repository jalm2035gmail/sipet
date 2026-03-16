from __future__ import annotations

import asyncio

from starlette.requests import Request

from fastapi_modulo.modulos.web.servicios import session_service


def _request_with_scope(headers, cookies=None, body=b"") -> Request:
    cookie_header = ""
    if cookies:
        cookie_header = "; ".join(f"{key}={value}" for key, value in cookies.items())
        headers = list(headers) + [(b"cookie", cookie_header.encode("latin1"))]

    async def receive():
        nonlocal body
        payload = {"type": "http.request", "body": body, "more_body": False}
        body = b""
        return payload

    return Request(
        {
            "type": "http",
            "method": "POST",
            "scheme": "https",
            "path": "/api/test",
            "headers": headers,
        },
        receive=receive,
    )


def test_validate_csrf_request_accepts_header_token() -> None:
    token = session_service.issue_csrf_token()
    request = _request_with_scope(
        [(b"x-csrf-token", token.encode("latin1"))],
        cookies={session_service.CSRF_COOKIE_NAME: token},
    )
    assert asyncio.run(session_service.validate_csrf_request(request)) is True


def test_validate_csrf_request_rejects_mismatch() -> None:
    request = _request_with_scope(
        [(b"x-csrf-token", b"uno")],
        cookies={session_service.CSRF_COOKIE_NAME: "dos"},
    )
    assert asyncio.run(session_service.validate_csrf_request(request)) is False
