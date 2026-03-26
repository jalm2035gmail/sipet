from typing import Any

from fastapi_modulo.core import db as core_db
from fastapi_modulo.core.db import TenantInstalledApp, ensure_tenant_admin_schema
from fastapi_modulo.core.module_registry import MODULES_BY_KEY, is_supported_module, list_modules_payload, set_module_enabled

GLOBAL_ROUTER_TENANT_MODULES = {
    "multitienda",
    "intelicoop",
}


def _admin_session():
    ensure_tenant_admin_schema(core_db.get_admin_engine())
    return core_db.get_admin_session_factory()()


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
    if not is_supported_module(module):
        raise ValueError("Este módulo legacy está deshabilitado hasta ser migrado a modulos_sipet.")
    if not module.manageable:
        raise ValueError("Este módulo no se puede desactivar.")
    if module.always_enabled and not enabled:
        raise ValueError("Este módulo no se puede desactivar.")
    normalized_tenant_key = str(tenant_key or "").strip()
    if not normalized_tenant_key:
        raise ValueError("Tenant inválido para cambio de estado.")
    restart_required = False

    if enabled and module.key in GLOBAL_ROUTER_TENANT_MODULES:
        set_module_enabled(module.key, True)
        restart_required = True

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

    result = next(
        (
            item
            for item in list_modules_payload(tenant_key=normalized_tenant_key, include_legacy=True)
            if item["key"] == module.key
        ),
        None,
    )
    if result is None:
        raise ValueError(f"No se pudo reconstruir el catalogo para el modulo '{module.key}'.")
    result["restart_required"] = restart_required
    return result


def set_catalog_module_enabled(module_key: str, enabled: bool, tenant_key: str | None = None) -> dict[str, Any]:
    normalized_tenant_key = str(tenant_key or "").strip()
    if normalized_tenant_key:
        return _set_tenant_module_enabled(module_key, enabled, normalized_tenant_key)
    return set_module_enabled(module_key, enabled)


def delete_catalog_module_dependencies(module_key: str, tenant_key: str | None = None) -> None:
    normalized_module_key = str(module_key or "").strip()
    if not normalized_module_key:
        return
    normalized_tenant_key = str(tenant_key or "").strip()
    with _admin_session() as db:
        query = db.query(TenantInstalledApp).filter(TenantInstalledApp.app_key == normalized_module_key)
        if normalized_tenant_key:
            query = query.filter(TenantInstalledApp.tenant_key == normalized_tenant_key)
        query.delete(synchronize_session=False)
        db.commit()


__all__ = ["delete_catalog_module_dependencies", "list_catalog_modules", "set_catalog_module_enabled"]
