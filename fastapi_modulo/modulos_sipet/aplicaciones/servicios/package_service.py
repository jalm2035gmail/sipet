from __future__ import annotations

import os
import shutil
import tempfile
import json
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, UploadFile

from fastapi_modulo.modulos_sipet.aplicaciones.repositorios.package_repository import (
    apply_module_zip,
    apply_staged_entries,
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
    get_cached_payload,
    get_cached_zip_inspection,
    guarded_lock,
    invalidate_catalog_cache,
    invalidate_zip_inspection,
    set_cached_payload,
)
import logging

_log = logging.getLogger(__name__)
IMPORT_PROCESS_AUDIT_ACTION = "import_process_state"
IMPORT_PROCESS_TTL_SECONDS = 3600


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _monotonic_ms() -> float:
    return time.perf_counter() * 1000.0


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
    modified_files: list[str] = []
    created_files: list[str] = []
    for entry in inspection.get("entries", []):
        relative_path = str(entry.get("relative_path") or "")
        status = str(entry.get("status") or "")
        destination = str(entry.get("destination") or "")
        staged_path = str(entry.get("staged_path") or "")
        existed_before = bool(entry.get("existed_before", os.path.exists(destination)))
        if status == "changed":
            modified_files.append(relative_path)
        elif status == "new":
            created_files.append(relative_path)
        affected_files.append(
            {
                "path": relative_path,
                "status": status,
                "size": int(entry.get("file_size") or 0),
                "existed_before": existed_before,
                "previous_checksum": str(entry.get("destination_checksum") or "")
                or (_file_checksum(destination) if existed_before else ""),
                "incoming_checksum": str(entry.get("staged_checksum") or "")
                or (_file_checksum(staged_path) if staged_path and os.path.exists(staged_path) else ""),
            }
        )
    return {
        "filename": original_filename,
        "checksum": checksum,
        "snapshot_path": snapshot_path,
        "module_key": module_key,
        "requested_by": str(user_id or "").strip(),
        "captured_at": _utc_now().isoformat(),
        "snapshot_mode": "full_fallback",
        "rollback_strategy": "differential_ready_full_fallback",
        "rollback_manifest": {
            "modified_files": modified_files,
            "created_files": created_files,
            "removed_files": [],
            "modified_count": len(modified_files),
            "created_count": len(created_files),
            "removed_count": 0,
        },
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


def _build_prepared_inspection(
    *,
    module_key: str,
    inspection: dict[str, Any],
    checksum: str,
    file_size: int,
    content_type: str,
    original_filename: str,
) -> dict[str, Any]:
    prepared = dict(inspection)
    prepared["module_key"] = module_key
    prepared["checksum"] = checksum
    prepared["file_size"] = int(file_size)
    prepared["content_type"] = content_type
    prepared["original_filename"] = original_filename
    prepared["prepared_at"] = _utc_now().isoformat()
    return prepared


def _inspection_has_changes(inspection: dict[str, Any]) -> bool:
    return int(inspection.get("new_files", 0) or 0) > 0 or int(inspection.get("changed_files", 0) or 0) > 0


def _should_create_snapshot(inspection: dict[str, Any]) -> bool:
    return _inspection_has_changes(inspection)


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


def _log_import_metrics(
    *,
    event: str,
    module_key: str,
    checksum: str = "",
    process_id: str = "",
    timings_ms: dict[str, float] | None = None,
    inspection_payload: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    payload: dict[str, Any] = {
        "event": event,
        "module_key": str(module_key or "").strip(),
        "checksum": str(checksum or "").strip(),
        "process_id": str(process_id or "").strip(),
        "timings_ms": timings_ms or {},
    }
    if inspection_payload is not None:
        payload.update(
            {
                "total_files": int(inspection_payload.get("total_files", 0) or 0),
                "total_uncompressed_size": int(inspection_payload.get("total_uncompressed_size", 0) or 0),
                "new_files": int(inspection_payload.get("new_files", 0) or 0),
                "changed_files": int(inspection_payload.get("changed_files", 0) or 0),
                "unchanged_files": int(inspection_payload.get("unchanged_files", 0) or 0),
                "ignored_files": max(
                    0,
                    int(inspection_payload.get("total_files", 0) or 0)
                    - (
                        int(inspection_payload.get("new_files", 0) or 0)
                        + int(inspection_payload.get("changed_files", 0) or 0)
                        + int(inspection_payload.get("unchanged_files", 0) or 0)
                    ),
                ),
            }
        )
    if extra:
        payload.update(extra)
    _log.info("import_metrics %s", json.dumps(payload, ensure_ascii=True, default=str))


def _snapshot_module_root(module_key: str, target_root: str) -> str:
    snapshot_dir = tempfile.mkdtemp(prefix=f"apps-snapshot-{str(module_key or '').strip()}-")
    archive_base = os.path.join(snapshot_dir, "module_backup")
    archive_path = shutil.make_archive(archive_base, "zip", root_dir=target_root)
    return archive_path


def _safe_unlink(path: str) -> None:
    if not path:
        return
    try:
        if os.path.exists(path):
            os.unlink(path)
    except FileNotFoundError:
        return


def _import_process_id(module_key: str, checksum: str, inspection_payload: dict[str, Any] | None = None) -> str:
    if inspection_payload is not None:
        inspection_id = str(inspection_payload.get("inspection_id") or "").strip()
        if inspection_id:
            return inspection_id
    return f"{str(module_key or '').strip()}:{str(checksum or '').strip().lower()}"


def _build_import_process_state(
    *,
    state: str,
    module_key: str,
    checksum: str,
    inspection_payload: dict[str, Any] | None = None,
    user_id: str | None = None,
    detail: str = "",
    error: str = "",
) -> dict[str, Any]:
    payload = {
        "process_id": _import_process_id(module_key, checksum, inspection_payload),
        "inspection_id": str((inspection_payload or {}).get("inspection_id") or "").strip(),
        "module_key": str(module_key or "").strip(),
        "checksum": str(checksum or "").strip(),
        "state": str(state or "").strip(),
        "detail": str(detail or "").strip(),
        "error": str(error or "").strip(),
        "updated_at": _utc_now().isoformat(),
        "requested_by": str(user_id or "").strip(),
    }
    if inspection_payload is not None:
        payload["target_root"] = str(inspection_payload.get("target_root") or "").strip()
        payload["staging_root"] = str(inspection_payload.get("staging_root") or "").strip()
        payload["new_files"] = int(inspection_payload.get("new_files", 0) or 0)
        payload["changed_files"] = int(inspection_payload.get("changed_files", 0) or 0)
        payload["unchanged_files"] = int(inspection_payload.get("unchanged_files", 0) or 0)
    return payload


def _store_import_process_state(
    *,
    state: str,
    module_key: str,
    checksum: str,
    inspection_payload: dict[str, Any] | None = None,
    user_id: str | None = None,
    detail: str = "",
    error: str = "",
) -> dict[str, Any]:
    payload = _build_import_process_state(
        state=state,
        module_key=module_key,
        checksum=checksum,
        inspection_payload=inspection_payload,
        user_id=user_id,
        detail=detail,
        error=error,
    )
    set_cached_payload("import_process", payload["process_id"], payload, IMPORT_PROCESS_TTL_SECONDS)
    create_registry_audit(
        module_key=module_key,
        action=IMPORT_PROCESS_AUDIT_ACTION,
        payload=payload,
        result="success" if not payload["error"] else "error",
        user_id=user_id,
        ip=None,
    )
    return payload


def get_import_process_state(process_id: str) -> dict[str, Any] | None:
    payload = get_cached_payload("import_process", str(process_id or "").strip())
    return payload if isinstance(payload, dict) else None


def prepare_module_package_import(
    *,
    module_key: str,
    zip_path: str,
    original_filename: str,
    checksum: str,
    file_size: int,
    content_type: str,
) -> dict[str, Any]:
    staging_root = ""
    timings_ms: dict[str, float] = {}
    try:
        _store_import_process_state(
            state="uploaded",
            module_key=module_key,
            checksum=checksum,
            detail="ZIP cargado y pendiente de inspeccion.",
        )
        inspect_started_at = _monotonic_ms()
        inspection = inspect_module_zip(module_key, zip_path)
        timings_ms["inspection"] = round(_monotonic_ms() - inspect_started_at, 3)
        staging_root = str(inspection.get("staging_root") or "")
        prepared = _build_prepared_inspection(
            module_key=module_key,
            inspection=inspection,
            checksum=checksum,
            file_size=file_size,
            content_type=content_type,
            original_filename=original_filename,
        )
        _store_import_process_state(
            state="inspected",
            module_key=module_key,
            checksum=checksum,
            inspection_payload=prepared,
            detail="Inspeccion completada.",
        )
        _store_import_process_state(
            state="validated",
            module_key=module_key,
            checksum=checksum,
            inspection_payload=prepared,
            detail="Validacion completada.",
        )
        _store_import_process_state(
            state="ready_to_apply",
            module_key=module_key,
            checksum=checksum,
            inspection_payload=prepared,
            detail="Importacion lista para aplicar.",
        )
        cache_zip_inspection(module_key, checksum, prepared)
        _log_import_metrics(
            event="prepare_module_package_import",
            module_key=module_key,
            checksum=checksum,
            process_id=_import_process_id(module_key, checksum, prepared),
            timings_ms=timings_ms,
            inspection_payload=prepared,
        )
        return prepared
    except Exception as exc:
        _store_import_process_state(
            state="failed",
            module_key=module_key,
            checksum=checksum,
            detail="Fallo durante la preparacion de la importacion.",
            error=str(exc),
        )
        _log_import_metrics(
            event="prepare_module_package_import_failed",
            module_key=module_key,
            checksum=checksum,
            process_id=_import_process_id(module_key, checksum),
            timings_ms=timings_ms,
            extra={"error": str(exc)},
        )
        cleanup_staging_dir(staging_root)
        raise


def apply_prepared_module_package(
    *,
    module_key: str,
    inspection_payload: dict[str, Any],
    original_filename: str,
    checksum: str,
    file_size: int,
    content_type: str,
    stored_filename: str,
    user_id: str | None = None,
    tenant_id: str | None = None,
    ip: str | None = None,
) -> dict:
    staging_root = str(inspection_payload.get("staging_root") or "")
    timings_ms: dict[str, float] = {}
    try:
        with guarded_lock(
            f"app_upload:{str(module_key or '').strip()}",
            ttl_seconds=300,
            detail="Ya existe una importacion en curso para este modulo.",
        ):
            if not staging_root or not os.path.isdir(staging_root):
                invalidate_zip_inspection(module_key, checksum)
                raise HTTPException(status_code=409, detail="La inspeccion previa del ZIP expiro o ya no esta disponible.")

            payload = _build_package_payload(
                module_key=module_key,
                inspection=inspection_payload,
                checksum=checksum,
                file_size=file_size,
                content_type=content_type,
                dry_run=False,
            )

            if not _inspection_has_changes(inspection_payload):
                _store_import_process_state(
                    state="applied",
                    module_key=module_key,
                    checksum=checksum,
                    inspection_payload=inspection_payload,
                    user_id=user_id,
                    detail="Importacion sin cambios efectivos; no-op aplicado.",
                )
                payload["warnings"] = [*payload["warnings"], "No se aplicaron cambios porque todos los archivos ya coinciden."]
                create_registry_audit(
                    module_key=module_key,
                    action="upload_package_noop",
                    payload={
                        "filename": original_filename,
                        "checksum": checksum,
                        "file_size": file_size,
                        "updated_files": 0,
                        "requested_by": str(user_id or "").strip(),
                    },
                    result="success",
                    user_id=user_id,
                    ip=ip,
                )
                create_package_upload(
                    module_key=module_key,
                    original_filename=original_filename,
                    stored_filename=stored_filename,
                    checksum=checksum,
                    file_size=file_size,
                    uploaded_by=user_id,
                    applied=False,
                )
                return payload

            if not _should_create_snapshot(inspection_payload):
                raise HTTPException(status_code=400, detail="No hay cambios efectivos para crear snapshot.")

            snapshot_started_at = _monotonic_ms()
            snapshot_path = _snapshot_module_root(module_key, inspection_payload["target_root"])
            timings_ms["snapshot"] = round(_monotonic_ms() - snapshot_started_at, 3)
            snapshot_payload = _build_snapshot_audit_payload(
                module_key=module_key,
                original_filename=original_filename,
                checksum=checksum,
                inspection=inspection_payload,
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
            apply_started_at = _monotonic_ms()
            payload["updated_files"] = apply_staged_entries(inspection_payload)
            timings_ms["application"] = round(_monotonic_ms() - apply_started_at, 3)
            invalidate_catalog_cache()
            create_package_upload(
                module_key=module_key,
                original_filename=original_filename,
                stored_filename=stored_filename,
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
            _store_import_process_state(
                state="applied",
                module_key=module_key,
                checksum=checksum,
                inspection_payload=inspection_payload,
                user_id=user_id,
                detail="Importacion aplicada correctamente.",
            )
            _log_import_metrics(
                event="apply_prepared_module_package",
                module_key=module_key,
                checksum=checksum,
                process_id=_import_process_id(module_key, checksum, inspection_payload),
                timings_ms=timings_ms,
                inspection_payload=inspection_payload,
                extra={"updated_files": int(payload["updated_files"])},
            )
            return payload
    except Exception as exc:
        _store_import_process_state(
            state="failed",
            module_key=module_key,
            checksum=checksum,
            inspection_payload=inspection_payload,
            user_id=user_id,
            detail="Fallo durante la aplicacion de la importacion.",
            error=str(exc),
        )
        _log_import_metrics(
            event="apply_prepared_module_package_failed",
            module_key=module_key,
            checksum=checksum,
            process_id=_import_process_id(module_key, checksum, inspection_payload),
            timings_ms=timings_ms,
            inspection_payload=inspection_payload,
            extra={"error": str(exc)},
        )
        raise
    finally:
        cleanup_started_at = _monotonic_ms()
        invalidate_zip_inspection(module_key, checksum)
        cleanup_staging_dir(staging_root)
        timings_ms["cleanup"] = round(_monotonic_ms() - cleanup_started_at, 3)


def apply_module_package_job(
    *,
    module_key: str,
    zip_path: str = "",
    original_filename: str,
    checksum: str,
    file_size: int,
    content_type: str = "application/zip",
    inspection_payload: dict[str, Any] | None = None,
    user_id: str | None = None,
    tenant_id: str | None = None,
    ip: str | None = None,
) -> dict:
    try:
        inspection = inspection_payload
        if inspection is None:
            if not zip_path:
                raise HTTPException(status_code=409, detail="No existe una inspeccion preparada para aplicar.")
            inspection = prepare_module_package_import(
                module_key=module_key,
                zip_path=zip_path,
                original_filename=original_filename,
                checksum=checksum,
                file_size=file_size,
                content_type=content_type,
            )
        return apply_prepared_module_package(
            module_key=module_key,
            inspection_payload=inspection,
            original_filename=original_filename,
            checksum=checksum,
            file_size=file_size,
            content_type=content_type,
            stored_filename=os.path.basename(zip_path or str(inspection.get("original_filename") or original_filename)),
            user_id=user_id,
            tenant_id=tenant_id,
            ip=ip,
        )
    finally:
        _safe_unlink(zip_path)


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
                "snapshot_mode": str(payload.get("snapshot_mode") or "full_fallback"),
                "rollback_strategy": str(payload.get("rollback_strategy") or "full_fallback"),
                "restored_files": restored_files,
                "requested_by": str(user_id or "").strip(),
                "rolled_back_at": now.isoformat(),
                "source_audit_id": int(getattr(audit_row, "id", 0) or 0),
            },
            result="success",
            user_id=user_id,
            ip=ip,
        )
        _store_import_process_state(
            state="rolled_back",
            module_key=module_key,
            checksum=str(payload.get("checksum") or snapshot_path),
            user_id=user_id,
            detail="Rollback ejecutado correctamente.",
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
    upload_temp_path = ""
    timings_ms: dict[str, float] = {}
    try:
        upload_started_at = _monotonic_ms()
        upload_temp_path, metadata = await persist_upload_to_temp(package)
        timings_ms["upload_persist"] = round(_monotonic_ms() - upload_started_at, 3)
        checksum = str(metadata["checksum"])
        file_size = int(metadata["file_size"])
        content_type = str(package.content_type or "").strip()
        original_filename = str(package.filename or "").strip()
        metadata_started_at = _monotonic_ms()
        validate_upload_metadata(
            filename=original_filename,
            content_type=content_type,
            file_size=file_size,
            has_zip_signature=bool(metadata["has_zip_signature"]),
        )
        timings_ms["metadata_validation"] = round(_monotonic_ms() - metadata_started_at, 3)
        if dry_run:
            prepare_started_at = _monotonic_ms()
            inspection = prepare_module_package_import(
                module_key=module_key,
                zip_path=upload_temp_path,
                original_filename=original_filename,
                checksum=checksum,
                file_size=file_size,
                content_type=content_type,
            )
            timings_ms["prepare_total"] = round(_monotonic_ms() - prepare_started_at, 3)
            payload = _build_package_payload(
                module_key=module_key,
                inspection=inspection,
                checksum=checksum,
                file_size=file_size,
                content_type=content_type,
                dry_run=True,
            )
            create_registry_audit(
                module_key=module_key,
                action="inspect_package",
                payload={"filename": original_filename, "checksum": checksum, "file_size": file_size},
                result="success",
                user_id=user_id,
                ip=ip,
            )
            _log_import_metrics(
                event="import_module_package_dry_run",
                module_key=module_key,
                checksum=checksum,
                process_id=_import_process_id(module_key, checksum, inspection),
                timings_ms=timings_ms,
                inspection_payload=inspection,
            )
            return payload

        if not str(expected_checksum or "").strip():
            raise HTTPException(status_code=400, detail="Debes inspeccionar y confirmar el ZIP antes de aplicarlo.")
        if str(expected_checksum).strip().lower() != checksum.lower():
            raise HTTPException(status_code=409, detail="El ZIP confirmado no coincide con el inspeccionado.")
        inspection = get_cached_zip_inspection(module_key, checksum)
        if inspection is None:
            raise HTTPException(status_code=409, detail="La inspeccion previa del ZIP expiro o no existe.")

        apply_started_at = _monotonic_ms()
        payload = apply_prepared_module_package(
            module_key=module_key,
            inspection_payload=inspection,
            original_filename=original_filename,
            checksum=checksum,
            file_size=file_size,
            content_type=content_type,
            stored_filename=os.path.basename(upload_temp_path),
            user_id=user_id,
            tenant_id=tenant_id,
            ip=ip,
        )
        timings_ms["apply_total"] = round(_monotonic_ms() - apply_started_at, 3)
        payload["status"] = "success"
        _log_import_metrics(
            event="import_module_package_apply",
            module_key=module_key,
            checksum=checksum,
            process_id=_import_process_id(module_key, checksum, inspection),
            timings_ms=timings_ms,
            inspection_payload=inspection,
            extra={"updated_files": int(payload.get("updated_files", 0) or 0)},
        )
        return payload
    except Exception as exc:
        _log_import_metrics(
            event="import_module_package_failed",
            module_key=module_key,
            checksum=locals().get("checksum", ""),
            process_id=_import_process_id(module_key, locals().get("checksum", "")),
            timings_ms=timings_ms,
            extra={"error": str(exc)},
        )
        raise
    finally:
        cleanup_started_at = _monotonic_ms()
        await package.close()
        _safe_unlink(upload_temp_path)
        timings_ms["cleanup"] = round(_monotonic_ms() - cleanup_started_at, 3)


__all__ = [
    "apply_module_zip",
    "apply_staged_entries",
    "apply_module_package_job",
    "apply_prepared_module_package",
    "get_import_process_state",
    "get_module_image_path",
    "get_module_upload_root",
    "import_module_package",
    "prepare_module_package_import",
    "rollback_module_package_job",
    "uninstall_module_package_job",
]
