from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import desc
from sqlalchemy.exc import OperationalError, ProgrammingError

from fastapi_modulo.db import SessionLocal
from fastapi_modulo.modulos.aplicaciones.modelos.db_models import (
    AppPackageUpload,
    AppProtocolAudit,
    AppRegistryAudit,
    AppRegistryState,
)


def list_registry_state() -> dict[str, AppRegistryState]:
    try:
        with SessionLocal() as db:
            rows = db.query(AppRegistryState).all()
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
        with SessionLocal() as db:
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
            row.updated_at = datetime.utcnow()
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
            updated_at=datetime.utcnow(),
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
        with SessionLocal() as db:
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
    row.scanned_at = datetime.utcnow()
    try:
        with SessionLocal() as db:
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
        with SessionLocal() as db:
            db.add(row)
            db.commit()
            db.refresh(row)
            return row
    except (OperationalError, ProgrammingError):
        return row


def get_latest_package_upload(module_key: str) -> AppPackageUpload | None:
    try:
        with SessionLocal() as db:
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
        with SessionLocal() as db:
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


__all__ = [
    "create_package_upload",
    "create_registry_audit",
    "get_latest_package_upload",
    "get_latest_registry_audit",
    "list_registry_state",
    "replace_protocol_audit",
    "upsert_registry_state",
]
