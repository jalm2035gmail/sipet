from typing import Any

from fastapi_modulo.core import db as core_db
from fastapi_modulo.core.db import TenantInstalledApp, ensure_tenant_admin_schema
from fastapi_modulo.core.module_registry import MODULES_BY_KEY, list_modules_payload, set_module_enabled


def _admin_session():
    ensure_tenant_admin_schema(core_db.get_current_engine())
    return core_db.get_session_factory_for_host("")()


def list_catalog_modules(
    tenant_key: str | None = None,
    *,
    refresh: bool = False,
    include_legacy: bool = False,
) -> list[dict[str, Any]]:
    return list_modules_payload(tenant_key=tenant_key, refresh=refresh, include_legacy=include_legacy)


def _set_tenant_module_enabled(module_key: str, enabled: bool, tenant_key: str) -> dict[str, Any]:
    module = MODULES_BY_KEY.get(str(module_key or "").strip())
    if not module:
        raise KeyError("Módulo no encontrado.")
    if module.always_enabled or not module.manageable:
        raise ValueError("Este módulo no se puede desactivar.")
    normalized_tenant_key = str(tenant_key or "").strip()
    if not normalized_tenant_key:
        raise ValueError("Tenant inválido para cambio de estado.")

    with _admin_session() as db:
        row = (
            db.query(TenantInstalledApp)
            .filter(
                TenantInstalledApp.tenant_key == normalized_tenant_key,
                TenantInstalledApp.app_key == module.key,
            )
            .first()
        )
        if row is None:
            row = TenantInstalledApp(
                tenant_key=normalized_tenant_key,
                app_key=module.key,
                app_version="0.0.0",
            )
            db.add(row)
        row.is_enabled = 1 if enabled else 0
        row.install_status = "installed" if enabled else "disabled"
        db.commit()

    result = next(item for item in list_modules_payload(tenant_key=normalized_tenant_key) if item["key"] == module.key)
    result["restart_required"] = False
    return result


def set_catalog_module_enabled(module_key: str, enabled: bool, tenant_key: str | None = None) -> dict[str, Any]:
    normalized_tenant_key = str(tenant_key or "").strip()
    if normalized_tenant_key:
        return _set_tenant_module_enabled(module_key, enabled, normalized_tenant_key)
    return set_module_enabled(module_key, enabled)


__all__ = ["list_catalog_modules", "set_catalog_module_enabled"]
