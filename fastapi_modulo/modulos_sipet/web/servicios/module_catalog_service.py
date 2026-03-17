from __future__ import annotations

from functools import lru_cache
from typing import Dict, List

from fastapi import Request

from fastapi_modulo.core.module_registry import get_active_app_access_names, get_active_module_keys, list_modules_payload
from fastapi_modulo.modulos_sipet.web.servicios.access_service import get_user_app_access, is_superadmin
from fastapi_modulo.modulos_sipet.web.servicios.icon_catalog_service import resolve_module_icon


@lru_cache(maxsize=1)
def _cached_modules_payload() -> tuple[dict, ...]:
    return tuple(list_modules_payload())


def invalidate_module_catalog_cache() -> None:
    _cached_modules_payload.cache_clear()


def build_sidebar_modules(request: Request) -> List[Dict[str, str]]:
    user_access = set(get_user_app_access(request))
    sidebar_modules: List[Dict[str, str]] = []
    for item in _cached_modules_payload():
        key = str(item.get("key") or "").strip()
        route = str(item.get("route") or "").strip()
        if not route or not bool(item.get("enabled")):
            continue
        if not bool(item.get("sidebar_visible")) and not (key == "system_admin" and is_superadmin(request)):
            continue
        app_access_name = str(item.get("app_access_name") or "").strip()
        if app_access_name and not is_superadmin(request) and app_access_name not in user_access:
            continue
        sidebar_modules.append(
            {
                "key": key,
                "label": str(item.get("label") or key),
                "route": route,
                "icon": resolve_module_icon(key, str(item.get("icon") or "")),
                "icon_url": str(item.get("icon_url") or ""),
                "route_match": "exact" if key == "brujula" else "",
                "sequence": str(item.get("sequence") or ""),
            }
        )
    return sidebar_modules


def get_backend_catalog_context(request: Request) -> dict:
    modules_payload = list(_cached_modules_payload())
    return {
        "user_app_access": get_user_app_access(request),
        "active_module_keys": get_active_module_keys(),
        "modules_payload": modules_payload,
        "modules_payload_map": {item["key"]: item for item in modules_payload},
        "sidebar_modules": build_sidebar_modules(request),
        "active_system_modules": get_active_app_access_names(),
    }
