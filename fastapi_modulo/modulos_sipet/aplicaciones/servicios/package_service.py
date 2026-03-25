from __future__ import annotations

import os
import shutil
import tempfile
import json
from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile

from fastapi_modulo.modulos_sipet.aplicaciones.repositorios.package_repository import (
    apply_module_zip,
    cleanup_staging_dir,
    get_module_architecture_report,
    get_module_image_path,
    get_module_upload_root,
    inspect_module_zip,
    persist_upload_to_temp,
    restore_module_snapshot,
    uninstall_module_files,
    validate_upload_metadata,
)
from fastapi_modulo.modulos_sipet.aplicaciones.repositorios.app_repository import delete_catalog_module_dependencies
from fastapi_modulo.modulos_sipet.aplicaciones.repositorios.persistence_repository import (
    clear_module_persistence,
    create_package_upload,
    create_registry_audit,
    get_latest_registry_audit,
    upsert_registry_state,
)
from fastapi_modulo.modulos_sipet.aplicaciones.servicios.redis_service import (
    cache_zip_inspection,
    get_cached_zip_inspection,
    guarded_lock,
    invalidate_catalog_cache,
    invalidate_zip_inspection,
)
from fastapi_modulo.modulos_sipet.aplicaciones.servicios.task_queue_service import queue_task

import logging

_log = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _file_checksum(path: str) -> str:
    import hashlib

    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _build_snapshot_audit_payload(
    *,
    module_key: str,
    original_filename: str,
    checksum: str,
    inspection: dict,
    snapshot_path: str,
    user_id: str | None,
) -> dict:
    affected_files: list[dict[str, object]] = []
    for entry in inspection.get("entries", []):
        destination = str(entry.get("destination") or "")
        staged_path = str(entry.get("staged_path") or "")
        existed_before = os.path.exists(destination)
        affected_files.append(
            {
                "path": str(entry.get("relative_path") or ""),
                "status": str(entry.get("status") or ""),
                "size": int(entry.get("file_size") or 0),
                "existed_before": existed_before,
                "previous_checksum": _file_checksum(destination) if existed_before else "",
                "incoming_checksum": _file_checksum(staged_path) if staged_path and os.path.exists(staged_path) else "",
            }
        )
    return {
        "filename": original_filename,
        "checksum": checksum,
        "snapshot_path": snapshot_path,
        "module_key": module_key,
        "requested_by": str(user_id or "").strip(),
        "captured_at": _utc_now().isoformat(),
        "affected_files": affected_files,
    }


def _build_package_payload(
    *,
    module_key: str,
    inspection: dict,
    checksum: str,
    file_size: int,
    content_type: str,
    dry_run: bool,
) -> dict:
    return {
        "module_key": module_key,
        "target_root": inspection["target_root"],
        "dry_run": bool(dry_run),
        "status": "success",
        "task_id": "",
        "task_name": "",
        "checksum": checksum,
        "file_size": file_size,
        "content_type": content_type,
        "updated_files": 0,
        "total_files": inspection["total_files"],
        "total_uncompressed_size": inspection["total_uncompressed_size"],
        "new_files": inspection["new_files"],
        "changed_files": inspection["changed_files"],
        "unchanged_files": inspection["unchanged_files"],
        "preview_files": inspection["preview_files"],
        "warnings": inspection["warnings"],
        "architecture_ok": bool(inspection.get("architecture_ok", True)),
        "architecture_errors": list(inspection.get("architecture_errors", [])),
        "architecture_warnings": list(inspection.get("architecture_warnings", [])),
    }


def _notify_webhook(event: str, payload: dict) -> None:
    """Fire-and-forget POST to APPLICATIONS_WEBHOOK_URL. Silently swallows all errors."""
    url = os.environ.get("APPLICATIONS_WEBHOOK_URL", "").strip()
    if not url:
        return
    try:
        import httpx

        body = {
            "event": event,
            "occurred_at": _utc_now().isoformat(),
            **payload,
        }
        with httpx.Client(timeout=5) as client:
            client.post(url, json=body)
    except Exception as exc:
        _log.warning("webhook notification failed (%s): %s", event, exc)


def _snapshot_module_root(module_key: str, target_root: str) -> str:
    snapshot_dir = tempfile.mkdtemp(prefix=f"apps-snapshot-{str(module_key or '').strip()}-")
    archive_base = os.path.join(snapshot_dir, "module_backup")
    archive_path = shutil.make_archive(archive_base, "zip", root_dir=target_root)
    return archive_path


def apply_module_package_job(
    *,
    module_key: str,
    zip_path: str,
    original_filename: str,
    checksum: str,
    file_size: int,
    user_id: str | None = None,
    tenant_id: str | None = None,
    ip: str | None = None,
) -> dict:
    staging_root = ""
    try:
        with guarded_lock(
            f"app_upload:{str(module_key or '').strip()}",
            ttl_seconds=300,
            detail="Ya existe una importacion en curso para este modulo.",
        ):
            inspection = inspect_module_zip(module_key, zip_path)
            staging_root = str(inspection.get("staging_root") or "")
            payload = _build_package_payload(
                module_key=module_key,
                inspection=inspection,
                checksum=checksum,
                file_size=file_size,
                content_type="application/zip",
                dry_run=False,
            )
            snapshot_path = _snapshot_module_root(module_key, inspection["target_root"])
            snapshot_payload = _build_snapshot_audit_payload(
                module_key=module_key,
                original_filename=original_filename,
                checksum=checksum,
                inspection=inspection,
                snapshot_path=snapshot_path,
                user_id=user_id,
            )
            create_registry_audit(
                module_key=module_key,
                action="snapshot_package",
                payload=snapshot_payload,
                result="success",
                user_id=user_id,
                ip=ip,
            )
            payload["updated_files"] = apply_module_zip(zip_path, inspection)
            invalidate_zip_inspection(module_key, checksum)
            invalidate_catalog_cache()
            create_package_upload(
                module_key=module_key,
                original_filename=original_filename,
                stored_filename=os.path.basename(zip_path),
                checksum=checksum,
                file_size=file_size,
                uploaded_by=user_id,
                applied=True,
            )
            upsert_registry_state(
                module_key=module_key,
                enabled=True,
                tenant_id=tenant_id,
                installed_version=None,
                uploaded_at=_utc_now(),
                updated_by=user_id,
            )
            create_registry_audit(
                module_key=module_key,
                action="upload_package",
                payload={
                    **snapshot_payload,
                    "file_size": file_size,
                    "updated_files": payload["updated_files"],
                },
                result="success",
                user_id=user_id,
                ip=ip,
            )
            _notify_webhook(
                "upload_package",
                {
                    "module_key": module_key,
                    "filename": original_filename,
                    "checksum": checksum,
                    "file_size": file_size,
                    "updated_files": payload["updated_files"],
                    "user_id": str(user_id or ""),
                    "ip": str(ip or ""),
                },
            )
            return payload
    finally:
        cleanup_staging_dir(staging_root)
        if zip_path and os.path.exists(zip_path):
            os.unlink(zip_path)


def rollback_module_package_job(
    *,
    module_key: str,
    user_id: str | None = None,
    tenant_id: str | None = None,
    ip: str | None = None,
) -> dict:
    with guarded_lock(
        f"app_upload:{str(module_key or '').strip()}",
        ttl_seconds=300,
        detail="Ya existe una operacion delicada en curso para este modulo.",
    ):
        audit_row = get_latest_registry_audit(module_key, "upload_package")
        if audit_row is None:
            raise HTTPException(status_code=404, detail="No existe un despliegue previo con backup para restaurar.")
        try:
            payload = json.loads(str(audit_row.payload_json or "{}"))
        except Exception as exc:
            raise HTTPException(status_code=400, detail="No se pudo leer la auditoria del backup.") from exc
        snapshot_path = str(payload.get("snapshot_path") or "").strip()
        restored_files = restore_module_snapshot(module_key, snapshot_path)
        invalidate_catalog_cache()
        now = _utc_now()
        upsert_registry_state(
            module_key=module_key,
            enabled=True,
            tenant_id=tenant_id,
            installed_version=None,
            uploaded_at=now,
            updated_by=user_id,
        )
        create_registry_audit(
            module_key=module_key,
            action="rollback_package",
            payload={
                "snapshot_path": snapshot_path,
                "restored_files": restored_files,
                "requested_by": str(user_id or "").strip(),
                "rolled_back_at": now.isoformat(),
                "source_audit_id": int(getattr(audit_row, "id", 0) or 0),
            },
            result="success",
            user_id=user_id,
            ip=ip,
        )
        _notify_webhook(
            "rollback_package",
            {
                "module_key": module_key,
                "snapshot_path": snapshot_path,
                "restored_files": restored_files,
                "user_id": str(user_id or ""),
                "ip": str(ip or ""),
            },
        )
        return {
            "module_key": module_key,
            "status": "success",
            "task_id": "",
            "task_name": "",
            "restored_files": restored_files,
            "snapshot_path": snapshot_path,
        }


def uninstall_module_package_job(
    *,
    module_key: str,
    user_id: str | None = None,
    tenant_id: str | None = None,
    tenant_key: str | None = None,
    ip: str | None = None,
) -> dict:
    with guarded_lock(
        f"app_upload:{str(module_key or '').strip()}",
        ttl_seconds=300,
        detail="Ya existe una operacion delicada en curso para este modulo.",
    ):
        architecture = get_module_architecture_report(module_key)
        payload = uninstall_module_files(module_key)
        resolved_tenant_key = str(tenant_key or tenant_id or "").strip() or None
        delete_catalog_module_dependencies(module_key, tenant_key=resolved_tenant_key)
        clear_module_persistence(module_key, tenant_id=resolved_tenant_key)
        create_registry_audit(
            module_key=module_key,
            action="uninstall_package",
            payload={
                "removed_path": payload.get("removed_path", ""),
                "removed_files": int(payload.get("removed_files", 0)),
                "tenant_id": resolved_tenant_key or "",
                "architecture_before_uninstall": architecture,
            },
            result="success",
            user_id=user_id,
            ip=ip,
        )
        invalidate_catalog_cache()
        _notify_webhook(
            "uninstall_package",
            {
                "module_key": module_key,
                "removed_path": payload.get("removed_path", ""),
                "removed_files": int(payload.get("removed_files", 0)),
                "user_id": str(user_id or ""),
                "ip": str(ip or ""),
            },
        )
        return payload


async def import_module_package(
    module_key: str,
    package: UploadFile,
    *,
    dry_run: bool = False,
    expected_checksum: str = "",
    user_id: str | None = None,
    tenant_id: str | None = None,
    ip: str | None = None,
) -> dict:
    temp_path = ""
    keep_temp_file = False
    try:
        temp_path, metadata = await persist_upload_to_temp(package)
        checksum = str(metadata["checksum"])
        file_size = int(metadata["file_size"])
        validate_upload_metadata(
            filename=str(package.filename or "").strip(),
            content_type=str(package.content_type or "").strip(),
            file_size=file_size,
            has_zip_signature=bool(metadata["has_zip_signature"]),
        )
        inspection = inspect_module_zip(module_key, temp_path)
        payload = _build_package_payload(
            module_key=module_key,
            inspection=inspection,
            checksum=checksum,
            file_size=file_size,
            content_type=str(package.content_type or "").strip(),
            dry_run=dry_run,
        )
        if dry_run:
            cache_zip_inspection(module_key, checksum, payload)
            create_registry_audit(
                module_key=module_key,
                action="inspect_package",
                payload={"filename": str(package.filename or "").strip(), "checksum": checksum, "file_size": file_size},
                result="success",
                user_id=user_id,
                ip=ip,
            )
            return payload

        if not str(expected_checksum or "").strip():
            raise HTTPException(status_code=400, detail="Debes inspeccionar y confirmar el ZIP antes de aplicarlo.")
        if str(expected_checksum).strip().lower() != checksum.lower():
            raise HTTPException(status_code=409, detail="El ZIP confirmado no coincide con el inspeccionado.")
        if get_cached_zip_inspection(module_key, checksum) is None:
            raise HTTPException(status_code=409, detail="La inspeccion previa del ZIP expiro o no existe.")

        queued = queue_task(
            "package_apply",
            {
                "module_key": module_key,
                "zip_path": temp_path,
                "original_filename": str(package.filename or "").strip(),
                "checksum": checksum,
                "file_size": file_size,
                "user_id": user_id or "",
                "tenant_id": tenant_id or "",
                "ip": ip or "",
            },
        )
        if queued["status"] == "inline":
            payload = apply_module_package_job(
                module_key=module_key,
                zip_path=temp_path,
                original_filename=str(package.filename or "").strip(),
                checksum=checksum,
                file_size=file_size,
                user_id=user_id,
                tenant_id=tenant_id,
                ip=ip,
            )
            payload["status"] = "success"
            return payload
        keep_temp_file = True
        payload["status"] = "queued"
        payload["task_id"] = str(queued["task_id"])
        payload["task_name"] = "package_apply"
        return payload
    finally:
        await package.close()
        if temp_path and os.path.exists(temp_path) and not keep_temp_file:
            os.unlink(temp_path)


__all__ = [
    "apply_module_zip",
    "apply_module_package_job",
    "get_module_image_path",
    "get_module_upload_root",
    "import_module_package",
    "rollback_module_package_job",
    "uninstall_module_package_job",
]
