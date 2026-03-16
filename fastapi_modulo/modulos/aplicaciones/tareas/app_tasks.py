from __future__ import annotations

from datetime import datetime, timezone

from fastapi_modulo.modulos.aplicaciones.servicios.audit_service import sync_protocol_files
from fastapi_modulo.modulos.aplicaciones.servicios.package_service import (
    apply_module_package_job,
    rollback_module_package_job,
)
from fastapi_modulo.modulos.aplicaciones.servicios.redis_service import store_task_state
from fastapi_modulo.modulos.aplicaciones.tareas.celery_app import celery_app


def _update_task(task_name: str, task_id: str, *, status: str, result: dict | None = None, error: str = "") -> None:
    if not str(task_id or "").strip():
        return
    store_task_state(
        task_name,
        str(task_id).strip(),
        {
            "task_id": str(task_id).strip(),
            "task_name": task_name,
            "status": status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "result": result or {},
            "error": error,
        },
    )


@celery_app.task(name="applications.protocol_sync")
def sync_app_protocol_task(
    task_id: str = "",
    mode: str = "repair_missing_only",
    overwrite_manifest: bool = False,
    overwrite_init: bool = False,
    user_id: str = "",
    ip: str = "",
) -> dict:
    _update_task("protocol_sync", task_id, status="running")
    try:
        result = sync_protocol_files(
            mode=mode,
            overwrite_manifest=overwrite_manifest,
            overwrite_init=overwrite_init,
            user_id=user_id or None,
            ip=ip or None,
        )
        _update_task("protocol_sync", task_id, status="success", result=result)
        return result
    except Exception as exc:
        _update_task("protocol_sync", task_id, status="error", error=str(exc))
        raise


@celery_app.task(name="applications.package_apply")
def apply_module_package_task(
    task_id: str = "",
    module_key: str = "",
    zip_path: str = "",
    original_filename: str = "",
    checksum: str = "",
    file_size: int = 0,
    user_id: str = "",
    tenant_id: str = "",
    ip: str = "",
) -> dict:
    _update_task("package_apply", task_id, status="running")
    try:
        result = apply_module_package_job(
            module_key=module_key,
            zip_path=zip_path,
            original_filename=original_filename,
            checksum=checksum,
            file_size=int(file_size or 0),
            user_id=user_id or None,
            tenant_id=tenant_id or None,
            ip=ip or None,
        )
        _update_task("package_apply", task_id, status="success", result=result)
        return result
    except Exception as exc:
        _update_task("package_apply", task_id, status="error", error=str(exc))
        raise


@celery_app.task(name="applications.package_rollback")
def rollback_module_package_task(
    task_id: str = "",
    module_key: str = "",
    user_id: str = "",
    tenant_id: str = "",
    ip: str = "",
) -> dict:
    _update_task("package_rollback", task_id, status="running")
    try:
        result = rollback_module_package_job(
            module_key=module_key,
            user_id=user_id or None,
            tenant_id=tenant_id or None,
            ip=ip or None,
        )
        _update_task("package_rollback", task_id, status="success", result=result)
        return result
    except Exception as exc:
        _update_task("package_rollback", task_id, status="error", error=str(exc))
        raise


__all__ = ["apply_module_package_task", "rollback_module_package_task", "sync_app_protocol_task"]
