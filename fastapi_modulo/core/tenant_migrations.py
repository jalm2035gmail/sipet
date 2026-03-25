from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Iterable, Sequence

from sqlalchemy.orm import Session

from fastapi_modulo.core.db import (
    TenantMigrationRun,
    TenantRegistry,
    create_engine_for_url,
    ensure_ia_config_schema,
    ensure_tenant_admin_schema,
    get_admin_engine,
    get_admin_session_factory,
)


MigrationHook = Callable[[object], None]
TENANT_MIGRATION_HOOKS: Sequence[tuple[str, MigrationHook]] = (
    ("ensure_ia_config_schema", ensure_ia_config_schema),
)


@dataclass(frozen=True)
class TenantMigrationResult:
    tenant_key: str
    target_scope: str
    migration_key: str
    status: str
    detail: str


def _log_migration_run(
    session: Session,
    *,
    tenant_key: str,
    target_scope: str,
    migration_key: str,
    status: str,
    detail: str,
) -> TenantMigrationRun:
    row = TenantMigrationRun(
        tenant_key=tenant_key,
        target_scope=target_scope,
        migration_key=migration_key,
        status=status,
        detail=detail,
        started_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
    )
    session.add(row)
    session.commit()
    return row


def run_admin_migrations(session: Session | None = None) -> TenantMigrationResult:
    ensure_tenant_admin_schema(get_admin_engine())
    own_session = session is None
    db = session or get_admin_session_factory()()
    try:
        _log_migration_run(
            db,
            tenant_key="system",
            target_scope="admin",
            migration_key="ensure_tenant_admin_schema",
            status="completed",
            detail="Esquema administrativo central verificado.",
        )
        return TenantMigrationResult(
            tenant_key="system",
            target_scope="admin",
            migration_key="ensure_tenant_admin_schema",
            status="completed",
            detail="Esquema administrativo central verificado.",
        )
    finally:
        if own_session:
            db.close()


def list_migration_targets(session: Session, tenant_key: str = "") -> list[TenantRegistry]:
    query = session.query(TenantRegistry).filter(TenantRegistry.is_active == 1)
    if str(tenant_key or "").strip():
        query = query.filter(TenantRegistry.tenant_key == str(tenant_key).strip())
    return query.order_by(TenantRegistry.id.asc()).all()


def run_tenant_migration(session: Session, tenant: TenantRegistry) -> list[TenantMigrationResult]:
    results: list[TenantMigrationResult] = []
    if not str(tenant.db_url or "").strip():
        results.append(
            TenantMigrationResult(
                tenant_key=tenant.tenant_key,
                target_scope="tenant",
                migration_key="core",
                status="skipped",
                detail="Tenant sin db_url definida; no se ejecutaron migraciones.",
            )
        )
        _log_migration_run(
            session,
            tenant_key=tenant.tenant_key,
            target_scope="tenant",
            migration_key="core",
            status="skipped",
            detail="Tenant sin db_url definida; no se ejecutaron migraciones.",
        )
        return results

    tenant_engine = create_engine_for_url(tenant.db_url)
    try:
        for migration_key, hook in TENANT_MIGRATION_HOOKS:
            hook(tenant_engine)
            detail = f"Migracion {migration_key} aplicada sobre {tenant.db_name or tenant.db_url}."
            _log_migration_run(
                session,
                tenant_key=tenant.tenant_key,
                target_scope="tenant",
                migration_key=migration_key,
                status="completed",
                detail=detail,
            )
            results.append(
                TenantMigrationResult(
                    tenant_key=tenant.tenant_key,
                    target_scope="tenant",
                    migration_key=migration_key,
                    status="completed",
                    detail=detail,
                )
            )
    finally:
        tenant_engine.dispose()
    return results


def run_migrations_for_tenants(tenant_key: str = "") -> list[TenantMigrationResult]:
    ensure_tenant_admin_schema(get_admin_engine())
    session = get_admin_session_factory()()
    try:
        results: list[TenantMigrationResult] = [run_admin_migrations(session)]
        for tenant in list_migration_targets(session, tenant_key=tenant_key):
            results.extend(run_tenant_migration(session, tenant))
        return results
    finally:
        session.close()
