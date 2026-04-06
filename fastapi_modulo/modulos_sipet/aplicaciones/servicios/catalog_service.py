from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from fastapi_modulo.modulos_sipet.aplicaciones.repositorios.app_repository import list_catalog_modules
from fastapi_modulo.modulos_sipet.aplicaciones.repositorios.package_repository import (
    PROJECT_ROOT,
    get_module_architecture_report,
    get_module_image_path,
    get_module_upload_root,
)
from fastapi_modulo.modulos_sipet.aplicaciones.repositorios.persistence_repository import (
    create_registry_audit,
    get_latest_registry_audit,
    get_latest_package_upload,
    list_registry_state,
)
from fastapi_modulo.modulos_sipet.aplicaciones.servicios.audit_service import get_protocol_audit_map
from fastapi_modulo.modulos_sipet.aplicaciones.servicios.image_branding_service import get_module_catalog_image_url
from fastapi_modulo.modulos_sipet.aplicaciones.servicios.redis_service import cache_catalog, get_cached_payload, set_cached_payload

CONFIG_ONLY_MODULE_KEYS = {
    "bsc",
    "instalacion_core",
    "modulo_base",
    "ajustes_core",
    "ajustes_ia_core",
    "ia_core",
    "predictivo_core",
    "personalizacion_core",
    "roles_core",
    "membresia_core",
    "plantillas_core",
    "diagnostico_core",
}
ARCHITECTURE_AUDIT_ACTION = "architecture_report"
ARCHITECTURE_CACHE_TTL_SECONDS = 300


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _is_installed_module(item: dict[str, Any], target_root: str | None) -> bool:
    if target_root:
        return True
    return bool(item.get("always_enabled"))


def _supports_package_management(item: dict[str, Any], target_root: str | None) -> bool:
    return bool(target_root) and bool(item.get("manageable", True))


def _is_core_module_payload(item: dict[str, Any]) -> bool:
    manifest_file = str(item.get("manifest_file") or "").strip()
    module_dir = str(item.get("module_dir") or "").strip()
    return "fastapi_modulo/modulos_sipet/" in manifest_file or "fastapi_modulo/modulos_sipet/" in module_dir


def _is_internal_runtime_helper(item: dict[str, Any]) -> bool:
    return (
        not bool(item.get("manageable", True))
        and not bool(item.get("sidebar_visible", False))
        and not str(item.get("route") or "").strip()
    )


def _package_management_note(item: dict[str, Any], *, target_root: str | None, is_core_module: bool) -> str:
    if is_core_module:
        return "Módulo núcleo de SIPET. Se actualiza con el deploy del core y no admite importación por ZIP."
    if not bool(item.get("manageable", True)):
        return "Módulo administrado por el sistema. No admite importación por ZIP."
    if not target_root:
        return "Este módulo no tiene un destino importable por paquetes ZIP."
    return ""


def _architecture_cache_key(module_key: str, target_root: str | None) -> str:
    return f"{str(module_key or '').strip()}:{str(target_root or '').strip()}"


def _normalize_architecture_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "architecture_ok": bool(payload.get("architecture_ok", True)),
        "architecture_errors": list(payload.get("architecture_errors", [])),
        "architecture_warnings": list(payload.get("architecture_warnings", [])),
        "validated_at": str(payload.get("validated_at") or ""),
    }


def _load_persisted_architecture(module_key: str, target_root: str | None) -> dict[str, Any] | None:
    audit_row = get_latest_registry_audit(module_key, ARCHITECTURE_AUDIT_ACTION)
    if audit_row is None:
        return None
    try:
        raw_payload = json.loads(str(audit_row.payload_json or "{}"))
    except Exception:
        return None
    if not isinstance(raw_payload, dict):
        return None
    if str(raw_payload.get("target_root") or "").strip() != str(target_root or "").strip():
        return None
    return _normalize_architecture_payload(raw_payload)


def _persist_architecture_snapshot(module_key: str, target_root: str | None, payload: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_architecture_payload(payload)
    if not normalized["validated_at"]:
        normalized["validated_at"] = _utc_now().isoformat()
    create_registry_audit(
        module_key=module_key,
        action=ARCHITECTURE_AUDIT_ACTION,
        payload={
            **normalized,
            "target_root": str(target_root or "").strip(),
        },
        result="success",
        user_id=None,
        ip=None,
    )
    set_cached_payload(
        "module_architecture",
        _architecture_cache_key(module_key, target_root),
        normalized,
        ARCHITECTURE_CACHE_TTL_SECONDS,
    )
    return normalized


def get_cached_architecture_report(
    module_key: str,
    target_root: str | None,
    *,
    refresh: bool = False,
) -> dict[str, Any]:
    cache_key = _architecture_cache_key(module_key, target_root)
    if not refresh:
        cached = get_cached_payload("module_architecture", cache_key)
        if isinstance(cached, dict):
            return _normalize_architecture_payload(cached)
        persisted = _load_persisted_architecture(module_key, target_root)
        if persisted is not None:
            set_cached_payload("module_architecture", cache_key, persisted, ARCHITECTURE_CACHE_TTL_SECONDS)
            return persisted
    computed = _normalize_architecture_payload(get_module_architecture_report(module_key, target_root))
    if not computed["validated_at"]:
        computed["validated_at"] = _utc_now().isoformat()
    return _persist_architecture_snapshot(module_key, target_root, computed)


def decorate_modules_payload(
    items: list[dict[str, Any]] | None = None,
    tenant_key: str | None = None,
    *,
    refresh: bool = False,
    include_legacy: bool = False,
) -> list[dict[str, Any]]:
    source_payload = (
        list_catalog_modules(tenant_key=tenant_key, refresh=refresh, include_legacy=include_legacy)
        if items is None
        else items
    )
    protocol_map = get_protocol_audit_map()
    persisted_state = list_registry_state(tenant_key)
    payload: list[dict[str, Any]] = []
    seen_fingerprints: set[tuple[str, str]] = set()
    for item in source_payload:
        key = str(item.get("key") or "").strip()
        if key in CONFIG_ONLY_MODULE_KEYS:
            continue
        if _is_internal_runtime_helper(item):
            continue
        application_flag = item.get("application")
        if application_flag is False:
            continue
        route = str(item.get("route") or "").strip()
        label = str(item.get("label") or "").strip().lower()
        fingerprint = (route, label)
        if (route or label) and fingerprint in seen_fingerprints:
            continue
        target_root = get_module_upload_root(key)
        is_core_module = _is_core_module_payload(item)
        if is_core_module:
            target_root = None
        if not _is_installed_module(item, target_root):
            continue
        state_row = persisted_state.get(key)
        if state_row is not None:
            if item.get("always_enabled"):
                item["enabled"] = True
            else:
                item["enabled"] = bool(state_row.enabled)
            if state_row.installed_version:
                item["installed_version"] = state_row.installed_version
        module_icon = str(item.get("icon") or "").strip()
        module_image_path = get_module_image_path(key)
        package_upload_enabled = _supports_package_management(item, target_root)
        item["package_upload_enabled"] = package_upload_enabled
        item["package_target_label"] = os.path.relpath(target_root, PROJECT_ROOT) if package_upload_enabled and target_root else ""
        item["is_core_module"] = is_core_module
        item["package_management_note"] = _package_management_note(
            item,
            target_root=target_root,
            is_core_module=is_core_module,
        )
        item["image_url"] = get_module_catalog_image_url(key) if module_image_path else None
        item["icon"] = module_icon
        upload_row = get_latest_package_upload(key)
        if upload_row is not None:
            item["uploaded_at"] = upload_row.uploaded_at.isoformat() if upload_row.uploaded_at else ""
            item["uploaded_filename"] = upload_row.original_filename
        status = protocol_map.get(key) or {}
        item["protocol_ok"] = bool(status.get("ok"))
        item["protocol_has_init"] = bool(status.get("has_init"))
        item["protocol_has_manifest"] = bool(status.get("has_manifest"))
        item["protocol_missing"] = list(status.get("missing", []))
        item["module_dir"] = str(status.get("module_dir", ""))
        item["has_readme"] = bool(status.get("has_readme"))
        item["has_controladores_dir"] = bool(status.get("has_controladores_dir"))
        item["has_tests_dir"] = bool(status.get("has_tests_dir"))
        item["routers_importable"] = bool(status.get("routers_importable"))
        item["issues"] = list(status.get("issues", []))
        item.update(get_cached_architecture_report(key, target_root, refresh=refresh))
        payload.append(item)
        if route or label:
            seen_fingerprints.add(fingerprint)
    if items is None and not tenant_key:
        cache_catalog(payload)
    return payload


__all__ = [
    "decorate_modules_payload",
    "get_cached_architecture_report",
    "get_module_image_path",
    "get_module_upload_root",
]
