from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc
from sqlalchemy.exc import OperationalError, ProgrammingError

from fastapi_modulo.core import db as core_db
from fastapi_modulo.modulos_sipet.aplicaciones.modelos.db_models import (
    AppPackageUpload,
    AppProtocolAudit,
    AppRegistryAudit,
    AppRegistryState,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _admin_session():
    return core_db.get_admin_session_factory()()


def list_registry_state(tenant_id: str | None = None) -> dict[str, AppRegistryState]:
    try:
        with _admin_session() as db:
            query = db.query(AppRegistryState)
            if tenant_id is not None:
                query = query.filter(AppRegistryState.tenant_id == tenant_id)
            rows = query.all()
            return {str(row.module_key): row for row in rows}
    except (OperationalError, ProgrammingError):
        return {}


def upsert_registry_state(
    *,
    module_key: str,
    enabled: bool,
    tenant_id: str | None,
    installed_version: str | None,
    uploaded_at: datetime | None,
    updated_by: str | None,
) -> AppRegistryState:
    try:
        with _admin_session() as db:
            row = (
                db.query(AppRegistryState)
                .filter(
                    AppRegistryState.module_key == module_key,
                    AppRegistryState.tenant_id == tenant_id,
                )
                .first()
            )
            if row is None:
                row = AppRegistryState(
                    module_key=module_key,
                    tenant_id=tenant_id,
                )
                db.add(row)
            row.enabled = bool(enabled)
            row.installed_version = installed_version
            row.uploaded_at = uploaded_at
            row.updated_by = updated_by
            row.updated_at = _utc_now()
            db.commit()
            db.refresh(row)
            return row
    except (OperationalError, ProgrammingError):
        return AppRegistryState(
            module_key=module_key,
            tenant_id=tenant_id,
            enabled=enabled,
            installed_version=installed_version,
            uploaded_at=uploaded_at,
            updated_by=updated_by,
            updated_at=_utc_now(),
        )


def create_registry_audit(
    *,
    module_key: str,
    action: str,
    payload: dict[str, Any],
    result: str,
    user_id: str | None,
    ip: str | None,
) -> AppRegistryAudit:
    row = AppRegistryAudit(
        module_key=module_key,
        action=action,
        payload_json=json.dumps(payload, ensure_ascii=True, default=str),
        result=result,
        user_id=user_id,
        ip=ip,
    )
    try:
        with _admin_session() as db:
            db.add(row)
            db.commit()
            db.refresh(row)
            return row
    except (OperationalError, ProgrammingError):
        return row


def replace_protocol_audit(module_key: str, payload: dict[str, Any]) -> AppProtocolAudit:
    row = AppProtocolAudit(module_key=module_key)
    row.has_init = bool(payload.get("has_init"))
    row.has_manifest = bool(payload.get("has_manifest"))
    row.missing_json = json.dumps(list(payload.get("missing", [])), ensure_ascii=True)
    row.ok = bool(payload.get("ok"))
    row.scanned_at = _utc_now()
    try:
        with _admin_session() as db:
            persisted = (
                db.query(AppProtocolAudit)
                .filter(AppProtocolAudit.module_key == module_key)
                .order_by(desc(AppProtocolAudit.scanned_at), desc(AppProtocolAudit.id))
                .first()
            )
            if persisted is None:
                persisted = row
                db.add(persisted)
            else:
                persisted.has_init = row.has_init
                persisted.has_manifest = row.has_manifest
                persisted.missing_json = row.missing_json
                persisted.ok = row.ok
                persisted.scanned_at = row.scanned_at
            db.commit()
            db.refresh(persisted)
            return persisted
    except (OperationalError, ProgrammingError):
        return row


def create_package_upload(
    *,
    module_key: str,
    original_filename: str,
    stored_filename: str,
    checksum: str,
    file_size: int,
    uploaded_by: str | None,
    applied: bool,
) -> AppPackageUpload:
    row = AppPackageUpload(
        module_key=module_key,
        original_filename=original_filename,
        stored_filename=stored_filename,
        checksum=checksum,
        file_size=file_size,
        uploaded_by=uploaded_by,
        applied=applied,
    )
    try:
        with _admin_session() as db:
            db.add(row)
            db.commit()
            db.refresh(row)
            return row
    except (OperationalError, ProgrammingError):
        return row


def get_latest_package_upload(module_key: str) -> AppPackageUpload | None:
    try:
        with _admin_session() as db:
            return (
                db.query(AppPackageUpload)
                .filter(AppPackageUpload.module_key == module_key)
                .order_by(desc(AppPackageUpload.uploaded_at), desc(AppPackageUpload.id))
                .first()
            )
    except (OperationalError, ProgrammingError):
        return None


def get_latest_registry_audit(module_key: str, action: str) -> AppRegistryAudit | None:
    try:
        with _admin_session() as db:
            return (
                db.query(AppRegistryAudit)
                .filter(
                    AppRegistryAudit.module_key == module_key,
                    AppRegistryAudit.action == action,
                )
                .order_by(desc(AppRegistryAudit.created_at), desc(AppRegistryAudit.id))
                .first()
            )
    except (OperationalError, ProgrammingError):
        return None


def clear_module_persistence(module_key: str, tenant_id: str | None = None) -> None:
    try:
        with _admin_session() as db:
            state_query = db.query(AppRegistryState).filter(AppRegistryState.module_key == module_key)
            if tenant_id is not None:
                state_query = state_query.filter(AppRegistryState.tenant_id == tenant_id)
            state_query.delete(synchronize_session=False)
            db.query(AppPackageUpload).filter(AppPackageUpload.module_key == module_key).delete(synchronize_session=False)
            db.query(AppRegistryAudit).filter(AppRegistryAudit.module_key == module_key).delete(synchronize_session=False)
            db.query(AppProtocolAudit).filter(AppProtocolAudit.module_key == module_key).delete(synchronize_session=False)
            db.commit()
    except (OperationalError, ProgrammingError):
        return


__all__ = [
    "create_package_upload",
    "create_registry_audit",
    "clear_module_persistence",
    "get_latest_package_upload",
    "get_latest_registry_audit",
    "list_registry_state",
    "replace_protocol_audit",
    "upsert_registry_state",
]
