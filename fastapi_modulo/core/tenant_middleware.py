from __future__ import annotations

from fastapi import Request

from fastapi_modulo.core import tenant_context


async def apply_tenant_context_middleware(request: Request, call_next):
    if getattr(request.state, "tenant_context", None) is not None:
        return await call_next(request)

    binding = tenant_context.bind_request_tenant_context(request)
    try:
        return await call_next(request)
    finally:
        tenant_context.reset_request_tenant_context(binding)
