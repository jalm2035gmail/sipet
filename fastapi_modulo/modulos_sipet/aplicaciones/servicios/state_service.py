from __future__ import annotations

from fastapi_modulo.modulos_sipet.aplicaciones.repositorios.app_repository import set_catalog_module_enabled
from fastapi_modulo.modulos_sipet.aplicaciones.repositorios.persistence_repository import (
    create_registry_audit,
    upsert_registry_state,
)
from fastapi_modulo.modulos_sipet.aplicaciones.servicios.catalog_service import decorate_modules_payload
from fastapi_modulo.modulos_sipet.aplicaciones.servicios.redis_service import invalidate_catalog_cache


def update_module_state(
    module_key: str,
    enabled: bool,
    *,
    user_id: str | None = None,
    tenant_id: str | None = None,
    tenant_key: str | None = None,
    ip: str | None = None,
) -> dict:
    resolved_tenant_key = str(tenant_key or tenant_id or "").strip() or None
    updated = set_catalog_module_enabled(module_key, enabled, tenant_key=resolved_tenant_key)
    installed_version = str(updated.get("version") or updated.get("installed_version") or "").strip() or None
    upsert_registry_state(
        module_key=module_key,
        enabled=enabled,
        tenant_id=resolved_tenant_key,
        installed_version=installed_version,
        uploaded_at=None,
        updated_by=user_id,
    )
    create_registry_audit(
        module_key=module_key,
        action="toggle_state",
        payload={"enabled": bool(enabled), "tenant_id": resolved_tenant_key or ""},
        result="success",
        user_id=user_id,
        ip=ip,
    )
    invalidate_catalog_cache()
    return decorate_modules_payload([updated], tenant_key=resolved_tenant_key)[0]


__all__ = ["update_module_state"]
