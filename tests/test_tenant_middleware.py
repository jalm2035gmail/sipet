import asyncio
import types

from fastapi.responses import JSONResponse
from starlette.requests import Request

from fastapi_modulo.core.tenant_middleware import apply_tenant_context_middleware


def _request(path: str, headers: list[tuple[bytes, bytes]] | None = None):
    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    scope = {
        "type": "http",
        "method": "GET",
        "scheme": "https",
        "path": path,
        "headers": list(headers or []),
        "app": types.SimpleNamespace(docs_url=None),
    }
    return Request(scope, receive=receive)


def test_tenant_middleware_sets_request_state() -> None:
    request = _request("/crm", headers=[(b"host", b"cliente1.midominio.com")])

    async def call_next(req: Request):
        payload = {
            "tenant_id": req.state.tenant_id,
            "tenant_key": req.state.tenant_key,
            "db_key": req.state.db_key,
            "access_mode": req.state.access_mode,
        }
        return JSONResponse(payload)

    response = asyncio.run(apply_tenant_context_middleware(request, call_next))
    assert response.status_code == 200
    assert b"cliente1_midominio_com" in response.body


def test_tenant_middleware_preserves_nodb_mode() -> None:
    request = _request("/health", headers=[(b"host", b"cliente1.midominio.com")])

    async def call_next(req: Request):
        return JSONResponse({"access_mode": req.state.access_mode})

    response = asyncio.run(apply_tenant_context_middleware(request, call_next))
    assert response.status_code == 200
    assert b"nodb" in response.body
