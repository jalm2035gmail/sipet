from __future__ import annotations

import os
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Optional

from fastapi import Request

from fastapi_modulo.core import db as core_db
from fastapi_modulo.core.tenant_resolver import DEFAULT_TENANT_RESOLVER, classify_access_mode, normalize_host
from fastapi_modulo.core.tenant_settings import normalize_tenant_slug

_TENANT_CONTEXT: ContextVar["TenantContext | None"] = ContextVar("sipet_tenant_context", default=None)


@dataclass(frozen=True)
class TenantContext:
    host: str
    tenant_key: str
    tenant_id: str
    db_key: str
    db_url: str
    access_mode: str


@dataclass(frozen=True)
class TenantContextBinding:
    context: TenantContext
    host_token: object
    tenant_token: object


def normalize_host_identifier(value: Optional[str]) -> str:
    return normalize_host(value)


def normalize_tenant_key(value: Optional[str]) -> str:
    return normalize_tenant_slug(value or "")


def classify_request_access(path: Optional[str]) -> str:
    return classify_access_mode(path)


def build_db_key(host: str, db_url: str, tenant_key: str) -> str:
    sqlite_path = core_db.get_current_dataMAIN_info(host).get("path", "") if db_url.startswith("sqlite:///") else ""
    if sqlite_path:
        basename = os.path.basename(sqlite_path).rsplit(".", 1)[0].strip()
        if basename:
            return normalize_tenant_key(basename)
    if host:
        return normalize_tenant_key(host.replace(".", "-"))
    return normalize_tenant_key(tenant_key)


def resolve_tenant_context(
    host: Optional[str],
    path: Optional[str] = None,
    tenant_hint: Optional[str] = None,
    access_mode: Optional[str] = None,
) -> TenantContext:
    resolved = DEFAULT_TENANT_RESOLVER.resolve(host, path=path, tenant_hint=tenant_hint, access_mode=access_mode)
    return TenantContext(
        host=resolved.host,
        tenant_key=resolved.tenant_key,
        tenant_id=resolved.tenant_id,
        db_key=resolved.db_key,
        db_url=resolved.db_url,
        access_mode=resolved.access_mode,
    )


def set_tenant_context(context: TenantContext):
    return _TENANT_CONTEXT.set(context)


def reset_tenant_context(token) -> None:
    _TENANT_CONTEXT.reset(token)


def get_tenant_context() -> Optional[TenantContext]:
    return _TENANT_CONTEXT.get()


def bind_request_tenant_context(request: Request) -> TenantContextBinding:
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.hostname
    context = resolve_tenant_context(host, request.url.path)
    request.state.tenant_context = context
    request.state.tenant_id = context.tenant_id
    request.state.tenant_key = context.tenant_key
    request.state.db_key = context.db_key
    request.state.db_url = context.db_url
    request.state.access_mode = context.access_mode
    host_token = core_db.set_request_host(context.host)
    tenant_token = set_tenant_context(context)
    return TenantContextBinding(context=context, host_token=host_token, tenant_token=tenant_token)


def reset_request_tenant_context(binding: TenantContextBinding) -> None:
    core_db.reset_request_host(binding.host_token)
    reset_tenant_context(binding.tenant_token)
