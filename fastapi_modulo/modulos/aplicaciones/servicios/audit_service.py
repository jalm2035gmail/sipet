from __future__ import annotations

from typing import Any

from fastapi_modulo.modulos.aplicaciones.repositorios.audit_repository import get_protocol_status_map
from fastapi_modulo.modulos.aplicaciones.repositorios.persistence_repository import (
    create_registry_audit,
    replace_protocol_audit,
)
from fastapi_modulo.modulos.aplicaciones.servicios.protocol_service import ensure_protocol_files
from fastapi_modulo.modulos.aplicaciones.servicios.redis_service import (
    guarded_lock,
    invalidate_catalog_cache,
    store_task_state,
)


def _persist_protocol_map(protocol_map: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    for module_key, payload in protocol_map.items():
        replace_protocol_audit(module_key, payload)
    return protocol_map


def get_protocol_audit_map() -> dict[str, dict[str, Any]]:
    return _persist_protocol_map(get_protocol_status_map())


def sync_protocol_files(
    *,
    mode: str = "repair_missing_only",
    overwrite_manifest: bool = False,
    overwrite_init: bool = False,
    user_id: str | None = None,
    ip: str | None = None,
) -> dict[str, Any]:
    with guarded_lock(
        "app_protocol_sync",
        ttl_seconds=180,
        detail="Ya existe una sincronizacion de protocolo en curso.",
    ):
        result = ensure_protocol_files(
            mode=mode,
            overwrite_manifest=overwrite_manifest,
            overwrite_init=overwrite_init,
        )
        _persist_protocol_map(result.get("after", {}))
        invalidate_catalog_cache()
        create_registry_audit(
            module_key="*",
            action="sync_protocol",
            payload={
                "mode": mode,
                "overwrite_manifest": overwrite_manifest,
                "overwrite_init": overwrite_init,
                "created_init": result.get("created_init", []),
                "created_manifest": result.get("created_manifest", []),
                "updated_init": result.get("updated_init", []),
                "updated_manifest": result.get("updated_manifest", []),
            },
            result="success",
            user_id=user_id,
            ip=ip,
        )
        return result


def update_sync_task_state(task_id: str, payload: dict[str, Any]) -> None:
    if str(task_id or "").strip():
        store_task_state("protocol_sync", str(task_id).strip(), payload)


__all__ = ["get_protocol_audit_map", "sync_protocol_files", "update_sync_task_state"]
