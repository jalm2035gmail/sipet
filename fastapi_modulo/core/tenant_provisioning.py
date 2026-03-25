from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from sqlalchemy.orm import Session

from fastapi_modulo.core.tenant_settings import ARCHITECTURE_SETTINGS, build_database_name, normalize_tenant_slug
from fastapi_modulo.core.db import (
    TenantDomain,
    TenantInstalledApp,
    TenantProvisionLog,
    TenantRegistry,
    ensure_tenant_admin_schema,
    get_admin_engine,
    get_admin_session_factory,
)

DEFAULT_CORE_APPS = ("web", "modulo_base")


@dataclass(frozen=True)
class TenantProvisionPayload:
    tenant_key: str
    primary_host: str
    db_name: str
    db_url: str
    plan: str = "base"
    status: str = "active"


@dataclass(frozen=True)
class TenantProvisionResult:
    tenant_key: str
    primary_host: str
    db_name: str
    db_url: str
    created: bool
    installed_apps: tuple[str, ...]


def _normalize_host(value: str) -> str:
    raw = str(value or "").strip().lower()
    raw = raw.split("://", 1)[-1]
    raw = raw.split("/", 1)[0]
    raw = raw.split(":", 1)[0]
    return raw.strip()


def build_tenant_payload(primary_host: str, tenant_key: str = "", plan: str = "base") -> TenantProvisionPayload:
    normalized_host = _normalize_host(primary_host)
    resolved_tenant_key = normalize_tenant_slug(tenant_key or normalized_host)
    environment = ARCHITECTURE_SETTINGS.environment
    db_name = build_database_name(resolved_tenant_key, environment)
    if ARCHITECTURE_SETTINGS.active_database_engine.value == "postgresql":
        db_url = ""
    else:
        db_url = f"sqlite:///./{db_name}.db"
    return TenantProvisionPayload(
        tenant_key=resolved_tenant_key,
        primary_host=normalized_host,
        db_name=db_name,
        db_url=db_url,
        plan=plan or "base",
        status="active",
    )


def _get_existing_tenant(session: Session, tenant_key: str, primary_host: str) -> TenantRegistry | None:
    return (
        session.query(TenantRegistry)
        .filter(
            (TenantRegistry.tenant_key == tenant_key) | (TenantRegistry.primary_host == primary_host)
        )
        .order_by(TenantRegistry.id.asc())
        .first()
    )


def _ensure_domain(session: Session, tenant_key: str, host: str) -> None:
    existing = session.query(TenantDomain).filter(TenantDomain.host == host).first()
    if existing is not None:
        existing.tenant_key = tenant_key
        existing.domain_type = existing.domain_type or "primary"
        existing.is_active = 1
        existing.updated_at = datetime.utcnow()
        return
    session.add(
        TenantDomain(
            tenant_key=tenant_key,
            host=host,
            domain_type="primary",
            certificate_status="pending",
            is_active=1,
        )
    )


def _ensure_installed_apps(session: Session, tenant_key: str, app_keys: Iterable[str]) -> tuple[str, ...]:
    installed: list[str] = []
    for app_key in app_keys:
        normalized_app_key = normalize_tenant_slug(app_key)
        existing = (
            session.query(TenantInstalledApp)
            .filter(
                TenantInstalledApp.tenant_key == tenant_key,
                TenantInstalledApp.app_key == normalized_app_key,
            )
            .first()
        )
        if existing is None:
            session.add(
                TenantInstalledApp(
                    tenant_key=tenant_key,
                    app_key=normalized_app_key,
                    app_version="0.0.0",
                    install_status="installed",
                    is_enabled=1,
                )
            )
        else:
            existing.install_status = "installed"
            existing.is_enabled = 1
            existing.updated_at = datetime.utcnow()
        installed.append(normalized_app_key)
    return tuple(installed)


def _log_provision(session: Session, tenant_key: str, status: str, detail: str) -> None:
    session.add(
        TenantProvisionLog(
            tenant_key=tenant_key,
            action="create",
            status=status,
            detail=detail,
        )
    )


def create_tenant(
    session: Session,
    primary_host: str,
    tenant_key: str = "",
    plan: str = "base",
    core_apps: Iterable[str] = DEFAULT_CORE_APPS,
) -> TenantProvisionResult:
    ensure_tenant_admin_schema(session.get_bind())
    payload = build_tenant_payload(primary_host=primary_host, tenant_key=tenant_key, plan=plan)

    existing = _get_existing_tenant(session, payload.tenant_key, payload.primary_host)
    created = existing is None
    if existing is None:
        existing = TenantRegistry(
            tenant_key=payload.tenant_key,
            primary_host=payload.primary_host,
            db_name=payload.db_name,
            db_url=payload.db_url,
            plan=payload.plan,
            status=payload.status,
            is_active=1,
        )
        session.add(existing)
    else:
        existing.primary_host = payload.primary_host
        existing.db_name = payload.db_name
        existing.db_url = payload.db_url
        existing.plan = payload.plan
        existing.status = payload.status
        existing.is_active = 1
        existing.updated_at = datetime.utcnow()

    _ensure_domain(session, payload.tenant_key, payload.primary_host)
    installed_apps = _ensure_installed_apps(session, payload.tenant_key, core_apps)
    _log_provision(
        session,
        payload.tenant_key,
        "completed",
        f"Tenant preparado para host={payload.primary_host}, db_name={payload.db_name}",
    )
    session.commit()

    return TenantProvisionResult(
        tenant_key=payload.tenant_key,
        primary_host=payload.primary_host,
        db_name=payload.db_name,
        db_url=payload.db_url,
        created=created,
        installed_apps=installed_apps,
    )


def create_tenant_with_default_session(
    primary_host: str,
    tenant_key: str = "",
    plan: str = "base",
    core_apps: Iterable[str] = DEFAULT_CORE_APPS,
) -> TenantProvisionResult:
    ensure_tenant_admin_schema(get_admin_engine())
    session = get_admin_session_factory()()
    try:
        return create_tenant(
            session=session,
            primary_host=primary_host,
            tenant_key=tenant_key,
            plan=plan,
            core_apps=core_apps,
        )
    finally:
        session.close()
