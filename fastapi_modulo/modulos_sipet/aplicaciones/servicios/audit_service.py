from __future__ import annotations

import json
from typing import Any

from fastapi_modulo.modulos_sipet.aplicaciones.repositorios.audit_repository import get_protocol_status_map
from fastapi_modulo.modulos_sipet.aplicaciones.repositorios.persistence_repository import (
    create_registry_audit,
    get_latest_registry_audit,
    replace_protocol_audit,
)
from fastapi_modulo.modulos_sipet.aplicaciones.servicios.protocol_service import ensure_protocol_files
from fastapi_modulo.modulos_sipet.aplicaciones.servicios.redis_service import (
    guarded_lock,
    get_cached_payload,
    invalidate_catalog_cache,
    set_cached_payload,
    store_task_state,
)

PROTOCOL_STATUS_AUDIT_ACTION = "protocol_status_map"
PROTOCOL_STATUS_CACHE_KEY = "current"
PROTOCOL_STATUS_CACHE_TTL_SECONDS = 300


def scan_protocol_status_map() -> dict[str, dict[str, Any]]:
    return get_protocol_status_map()


def persist_protocol_status_map(protocol_map: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    for module_key, payload in protocol_map.items():
        replace_protocol_audit(module_key, payload)
    create_registry_audit(
        module_key="*",
        action=PROTOCOL_STATUS_AUDIT_ACTION,
        payload={"modules": protocol_map},
        result="success",
        user_id=None,
        ip=None,
    )
    set_cached_payload(
        "protocol_status_map",
        PROTOCOL_STATUS_CACHE_KEY,
        protocol_map,
        PROTOCOL_STATUS_CACHE_TTL_SECONDS,
    )
    return protocol_map


def get_cached_protocol_status_map() -> dict[str, dict[str, Any]]:
    cached = get_cached_payload("protocol_status_map", PROTOCOL_STATUS_CACHE_KEY)
    if isinstance(cached, dict):
        return cached

    audit_row = get_latest_registry_audit("*", PROTOCOL_STATUS_AUDIT_ACTION)
    if audit_row is not None:
        try:
            payload = json.loads(str(audit_row.payload_json or "{}"))
        except Exception:
            payload = {}
        modules = payload.get("modules")
        if isinstance(modules, dict):
            set_cached_payload(
                "protocol_status_map",
                PROTOCOL_STATUS_CACHE_KEY,
                modules,
                PROTOCOL_STATUS_CACHE_TTL_SECONDS,
            )
            return modules
    return {}


def get_protocol_audit_map(*, refresh: bool = False) -> dict[str, dict[str, Any]]:
    if not refresh:
        cached = get_cached_protocol_status_map()
        if cached:
            return cached
    return persist_protocol_status_map(scan_protocol_status_map())


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
        persist_protocol_status_map(result.get("after", {}))
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


__all__ = [
    "get_cached_protocol_status_map",
    "get_protocol_audit_map",
    "persist_protocol_status_map",
    "scan_protocol_status_map",
    "sync_protocol_files",
    "update_sync_task_state",
]
