from __future__ import annotations

from fastapi_modulo.modulos.aplicaciones.repositorios.app_repository import set_catalog_module_enabled
from fastapi_modulo.modulos.aplicaciones.repositorios.persistence_repository import (
    create_registry_audit,
    upsert_registry_state,
)
from fastapi_modulo.modulos.aplicaciones.servicios.catalog_service import decorate_modules_payload
from fastapi_modulo.modulos.aplicaciones.servicios.redis_service import invalidate_catalog_cache


def update_module_state(
    module_key: str,
    enabled: bool,
    *,
    user_id: str | None = None,
    tenant_id: str | None = None,
    ip: str | None = None,
) -> dict:
    updated = set_catalog_module_enabled(module_key, enabled)
    installed_version = str(updated.get("version") or updated.get("installed_version") or "").strip() or None
    upsert_registry_state(
        module_key=module_key,
        enabled=enabled,
        tenant_id=tenant_id,
        installed_version=installed_version,
        uploaded_at=None,
        updated_by=user_id,
    )
    create_registry_audit(
        module_key=module_key,
        action="toggle_state",
        payload={"enabled": bool(enabled), "tenant_id": tenant_id},
        result="success",
        user_id=user_id,
        ip=ip,
    )
    invalidate_catalog_cache()
    return decorate_modules_payload([updated])[0]


__all__ = ["update_module_state"]
