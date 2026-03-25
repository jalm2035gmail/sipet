from __future__ import annotations

import os
from typing import Any

from fastapi_modulo.modulos_sipet.aplicaciones.repositorios.app_repository import list_catalog_modules
from fastapi_modulo.modulos_sipet.aplicaciones.repositorios.package_repository import (
    PROJECT_ROOT,
    get_module_architecture_report,
    get_module_image_path,
    get_module_upload_root,
)
from fastapi_modulo.modulos_sipet.aplicaciones.repositorios.persistence_repository import (
    get_latest_package_upload,
    list_registry_state,
)
from fastapi_modulo.modulos_sipet.aplicaciones.servicios.audit_service import get_protocol_audit_map
from fastapi_modulo.modulos_sipet.aplicaciones.servicios.image_branding_service import get_module_catalog_image_url
from fastapi_modulo.modulos_sipet.aplicaciones.servicios.redis_service import cache_catalog

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


def _is_installed_module(item: dict[str, Any], target_root: str | None) -> bool:
    if target_root:
        return True
    return bool(item.get("always_enabled"))


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
        application_flag = item.get("application")
        if application_flag is False:
            continue
        route = str(item.get("route") or "").strip()
        label = str(item.get("label") or "").strip().lower()
        fingerprint = (route, label)
        if (route or label) and fingerprint in seen_fingerprints:
            continue
        target_root = get_module_upload_root(key)
        if not _is_installed_module(item, target_root):
            continue
        state_row = persisted_state.get(key)
        if state_row is not None:
            item["enabled"] = bool(state_row.enabled)
            if state_row.installed_version:
                item["installed_version"] = state_row.installed_version
        module_icon = str(item.get("icon") or "").strip()
        module_image_path = get_module_image_path(key)
        item["package_upload_enabled"] = bool(target_root)
        item["package_target_label"] = os.path.relpath(target_root, PROJECT_ROOT) if target_root else ""
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
        item.update(get_module_architecture_report(key, target_root))
        payload.append(item)
        if route or label:
            seen_fingerprints.add(fingerprint)
    if items is None and not tenant_key:
        cache_catalog(payload)
    return payload


__all__ = ["decorate_modules_payload", "get_module_image_path", "get_module_upload_root"]
