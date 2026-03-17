from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from fastapi_modulo.core.database_router import DEFAULT_DATABASE_ROUTER
from fastapi_modulo.core.tenant_settings import ARCHITECTURE_SETTINGS, normalize_tenant_slug
from fastapi_modulo.core.tenant_types import TenantKeyStrategy

NODB_PATHS = {
    "/health",
    "/healthz",
    "/favicon.ico",
    "/docs",
    "/redoc",
    "/openapi.json",
}
NODB_PREFIXES = (
    "/static/",
    "/templates/",
    "/icon/",
    "/imagenes/",
    "/docs/",
    "/redoc/",
)
ADMIN_GLOBAL_PREFIXES = (
    "/admin/tenants",
    "/admin/system",
)


@dataclass(frozen=True)
class ResolvedTenant:
    host: str
    tenant_key: str
    tenant_id: str
    db_key: str
    db_url: str
    access_mode: str


def normalize_host(value: Optional[str]) -> str:
    raw = (value or "").strip().lower()
    if not raw:
        return ""
    if "://" in raw:
        raw = raw.split("://", 1)[1]
    raw = raw.split("/", 1)[0]
    raw = raw.split(",", 1)[0].strip()
    if ":" in raw and raw.count(":") == 1:
        raw = raw.split(":", 1)[0]
    return raw


def classify_access_mode(path: Optional[str]) -> str:
    current_path = str(path or "").strip() or "/"
    if current_path in NODB_PATHS or any(current_path.startswith(prefix) for prefix in NODB_PREFIXES):
        return "nodb"
    if any(current_path.startswith(prefix) for prefix in ADMIN_GLOBAL_PREFIXES):
        return "admin_global"
    return "tenant"


def tenant_key_from_host(host: str, strategy: TenantKeyStrategy | None = None) -> str:
    active_strategy = strategy or ARCHITECTURE_SETTINGS.tenant_key_strategy
    normalized_host = normalize_host(host)
    if not normalized_host:
        return normalize_tenant_slug(os.environ.get("DEFAULT_TENANT_ID", "default"))
    if active_strategy == TenantKeyStrategy.SUBDOMAIN:
        subdomain = normalized_host.split(".", 1)[0]
        return normalize_tenant_slug(subdomain)
    if active_strategy == TenantKeyStrategy.HOST_ENV:
        environment = ARCHITECTURE_SETTINGS.environment
        return normalize_tenant_slug(f"{normalized_host}_{environment}")
    return normalize_tenant_slug(normalized_host)


def build_db_key(host: str, db_url: str, tenant_key: str) -> str:
    if db_url.startswith("sqlite:///"):
        sqlite_path = db_url.replace("sqlite:///", "", 1).split("?", 1)[0]
        if sqlite_path:
            basename = os.path.basename(sqlite_path).rsplit(".", 1)[0].strip()
            if basename:
                return normalize_tenant_slug(basename)
    if host:
        return normalize_tenant_slug(host)
    return normalize_tenant_slug(tenant_key)


class TenantResolver:
    def __init__(self, default_tenant_id: Optional[str] = None):
        self.default_tenant_id = normalize_tenant_slug(default_tenant_id or os.environ.get("DEFAULT_TENANT_ID", "default"))

    def resolve_tenant_from_domain(self, domain: Optional[str]) -> str:
        normalized_domain = normalize_host(domain)
        if not normalized_domain:
            return self.default_tenant_id
        return tenant_key_from_host(normalized_domain)

    def resolve(
        self,
        host: Optional[str],
        path: Optional[str] = None,
        tenant_hint: Optional[str] = None,
        access_mode: Optional[str] = None,
    ) -> ResolvedTenant:
        normalized_host = normalize_host(host)
        resolved_access_mode = access_mode or classify_access_mode(path)
        tenant_key = normalize_tenant_slug(tenant_hint or self.resolve_tenant_from_domain(normalized_host))
        db_url = DEFAULT_DATABASE_ROUTER.get_database_url_for_host(normalized_host)
        db_key = build_db_key(normalized_host, db_url, tenant_key)
        return ResolvedTenant(
            host=normalized_host,
            tenant_key=tenant_key,
            tenant_id=tenant_key,
            db_key=db_key,
            db_url=db_url,
            access_mode=resolved_access_mode,
        )


DEFAULT_TENANT_RESOLVER = TenantResolver()
