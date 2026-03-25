from __future__ import annotations

from typing import Any

from fastapi import Request

from fastapi_modulo.core import db as core_db
from fastapi_modulo.core.db import TenantInstalledApp, TenantMigrationRun, TenantRegistry
from fastapi_modulo.core.module_registry import get_active_module_keys


def _admin_session():
    return core_db.get_admin_session_factory()()


def _redact_db_url(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if raw.startswith("sqlite:///"):
        return "sqlite:///[redacted]"
    if "@" in raw and "://" in raw:
        scheme, rest = raw.split("://", 1)
        credentials, host_part = rest.rsplit("@", 1)
        if ":" in credentials:
            username = credentials.split(":", 1)[0]
            return f"{scheme}://{username}:***@{host_part}"
        return f"{scheme}://***@{host_part}"
    return raw


def _redact_database_info(payload: dict[str, Any]) -> dict[str, Any]:
    sanitized = dict(payload)
    sanitized["url"] = _redact_db_url(str(sanitized.get("url") or ""))
    if sanitized.get("path"):
        sanitized["path"] = "[redacted]"
    return sanitized


def _tenant_registry_payload(tenant_key: str) -> dict[str, Any]:
    session = _admin_session()
    try:
        row = session.query(TenantRegistry).filter(TenantRegistry.tenant_key == tenant_key).first()
        if row is None:
            return {}
        return {
            "tenant_key": row.tenant_key,
            "primary_host": row.primary_host,
            "db_name": row.db_name,
            "db_url": _redact_db_url(row.db_url),
            "plan": row.plan,
            "status": row.status,
            "is_active": bool(row.is_active),
        }
    finally:
        session.close()


def _installed_apps_payload(tenant_key: str) -> list[str]:
    session = _admin_session()
    try:
        rows = (
            session.query(TenantInstalledApp.app_key)
            .filter(
                TenantInstalledApp.tenant_key == tenant_key,
                TenantInstalledApp.is_enabled == 1,
                TenantInstalledApp.install_status == "installed",
            )
            .order_by(TenantInstalledApp.app_key.asc())
            .all()
        )
        return [str(row[0]) for row in rows if str(row[0] or "").strip()]
    finally:
        session.close()


def _recent_migrations_payload(tenant_key: str) -> list[dict[str, str]]:
    session = _admin_session()
    try:
        rows = (
            session.query(TenantMigrationRun)
            .filter(TenantMigrationRun.tenant_key.in_([tenant_key, "system"]))
            .order_by(TenantMigrationRun.id.desc())
            .limit(10)
            .all()
        )
        return [
            {
                "tenant_key": str(row.tenant_key or ""),
                "target_scope": str(row.target_scope or ""),
                "migration_key": str(row.migration_key or ""),
                "status": str(row.status or ""),
                "detail": str(row.detail or ""),
            }
            for row in rows
        ]
    finally:
        session.close()


def build_tenant_diagnostics(request: Request) -> dict[str, Any]:
    tenant_key = str(getattr(request.state, "tenant_key", "") or getattr(request.state, "tenant_id", "") or "").strip()
    db_info = _redact_database_info(core_db.get_current_database_info(
        request.headers.get("x-forwarded-host")
        or request.headers.get("host")
        or request.url.hostname
    ))
    installed_apps = _installed_apps_payload(tenant_key) if tenant_key else []
    return {
        "tenant": {
            "tenant_key": tenant_key,
            "tenant_id": str(getattr(request.state, "tenant_id", "") or ""),
            "host": str(getattr(request.state, "tenant_context", None).host if getattr(request.state, "tenant_context", None) else ""),
            "access_mode": str(getattr(request.state, "access_mode", "") or ""),
        },
        "database": db_info,
        "registry": _tenant_registry_payload(tenant_key) if tenant_key else {},
        "modules": {
            "installed_apps": installed_apps,
            "active_module_keys": get_active_module_keys(tenant_key=tenant_key),
        },
        "migrations": _recent_migrations_payload(tenant_key) if tenant_key else [],
    }
