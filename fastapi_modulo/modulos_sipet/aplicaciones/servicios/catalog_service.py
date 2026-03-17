from __future__ import annotations

import os
from typing import Any

from fastapi_modulo.modulos_sipet.aplicaciones.repositorios.app_repository import list_catalog_modules
from fastapi_modulo.modulos_sipet.aplicaciones.repositorios.package_repository import (
    PROJECT_ROOT,
    get_module_image_path,
    get_module_upload_root,
)
from fastapi_modulo.modulos_sipet.aplicaciones.repositorios.persistence_repository import (
    get_latest_package_upload,
    list_registry_state,
)
from fastapi_modulo.modulos_sipet.aplicaciones.servicios.audit_service import get_protocol_audit_map
from fastapi_modulo.modulos_sipet.aplicaciones.servicios.image_branding_service import get_module_catalog_image_url
from fastapi_modulo.modulos_sipet.aplicaciones.servicios.redis_service import cache_catalog, get_cached_catalog


def decorate_modules_payload(items: list[dict[str, Any]] | None = None, tenant_key: str | None = None) -> list[dict[str, Any]]:
    if items is None:
        cached = get_cached_catalog()
        if cached is not None:
            return cached
    payload = list_catalog_modules(tenant_key=tenant_key) if items is None else items
    protocol_map = get_protocol_audit_map()
    persisted_state = list_registry_state(tenant_key)
    for item in payload:
        key = str(item.get("key") or "").strip()
        state_row = persisted_state.get(key)
        if state_row is not None:
            item["enabled"] = bool(state_row.enabled)
            if state_row.installed_version:
                item["installed_version"] = state_row.installed_version
        target_root = get_module_upload_root(key)
        item["package_upload_enabled"] = bool(target_root)
        item["package_target_label"] = os.path.relpath(target_root, PROJECT_ROOT) if target_root else ""
        item["image_url"] = get_module_catalog_image_url(key)
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
    if items is None and not tenant_key:
        cache_catalog(payload)
    return payload


__all__ = ["decorate_modules_payload", "get_module_image_path", "get_module_upload_root"]
