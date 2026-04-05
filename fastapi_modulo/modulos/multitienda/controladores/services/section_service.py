from __future__ import annotations

from urllib.parse import urlencode

from fastapi_modulo.modulos_sipet.web.servicios.access_service import normalize_role_name


def get_optional_section_integration(section_id: str, optional_section_integrations: dict) -> dict:
    return dict(optional_section_integrations.get(str(section_id or "").strip(), {}))


def resolve_enabled_module_route(module_key: str, is_module_enabled, list_modules_payload) -> str:
    normalized_key = str(module_key or "").strip()
    if not normalized_key or not is_module_enabled(normalized_key):
        return ""
    for item in list_modules_payload():
        if str(item.get("key") or "").strip() == normalized_key:
            return str(item.get("route") or "").strip()
    return ""


def optional_section_available(section_id: str, optional_section_integrations: dict, is_module_enabled, list_modules_payload) -> bool:
    integration = get_optional_section_integration(section_id, optional_section_integrations)
    module_key = str(integration.get("module_key") or "").strip()
    if not module_key:
        return True
    return bool(resolve_enabled_module_route(module_key, is_module_enabled, list_modules_payload))


def resolve_integrated_section_target(
    section_id: str,
    optional_section_integrations: dict,
    is_module_enabled,
    list_modules_payload,
    scope: dict | None = None,
) -> str:
    integration = get_optional_section_integration(section_id, optional_section_integrations)
    module_key = str(integration.get("module_key") or "").strip()
    explicit_target = str(integration.get("target_route") or "").strip()
    target_route = explicit_target or resolve_enabled_module_route(module_key, is_module_enabled, list_modules_payload)
    if not target_route:
        return ""
    scope_query_param = str(integration.get("scope_query_param") or "").strip()
    scope_value = str((scope or {}).get("store_slug") or "").strip()
    if scope_query_param and scope_value:
        separator = "&" if "?" in target_route else "?"
        return f"{target_route}{separator}{urlencode({scope_query_param: scope_value})}"
    return target_route


def resolve_integrated_module_context(
    section_id: str,
    optional_section_integrations: dict,
    is_module_enabled,
    list_modules_payload,
    scope: dict | None = None,
) -> dict[str, str | bool]:
    integration = get_optional_section_integration(section_id, optional_section_integrations)
    module_key = str(integration.get("module_key") or "").strip()
    target_route = resolve_integrated_section_target(
        section_id,
        optional_section_integrations,
        is_module_enabled,
        list_modules_payload,
        scope,
    )
    route = resolve_enabled_module_route(module_key, is_module_enabled, list_modules_payload)
    return {
        "enabled": bool(route),
        "module_key": module_key,
        "route": route,
        "target_route": target_route or route,
        "api_base": f"/api/{module_key}" if module_key else "",
    }


def is_store_assigned_admin(role_name: str | None) -> bool:
    return normalize_role_name(role_name) == "administrador_tienda"


def can_access_store_config(role_name: str | None) -> bool:
    normalized = normalize_role_name(role_name)
    return normalized in {
        "administrador_tienda",
        "superadministrador",
        "superadmin",
        "administrador_multiempresa",
        "administrador",
    }


_SECTION_RULES = {
    "gestion": lambda perms, is_superadmin, is_platform_admin, normalized_role: is_platform_admin,
    "repartidores": lambda perms, is_superadmin, is_platform_admin, normalized_role: is_platform_admin,
    "configuracion": lambda perms, is_superadmin, is_platform_admin, normalized_role: can_access_store_config(normalized_role),
    "videos": lambda perms, is_superadmin, is_platform_admin, normalized_role: is_superadmin or perms.get("can_upload_videos"),
    "referidos": lambda perms, is_superadmin, is_platform_admin, normalized_role: is_superadmin or perms.get("referrals"),
    "fidelizacion": lambda perms, is_superadmin, is_platform_admin, normalized_role: is_superadmin or perms.get("fidelizacion"),
    "notificaciones_pwa": lambda perms, is_superadmin, is_platform_admin, normalized_role: is_superadmin or perms.get("pwa_notifications"),
    "reservaciones": lambda perms, is_superadmin, is_platform_admin, normalized_role: is_superadmin or perms.get("appointments"),
    "cupones": lambda perms, is_superadmin, is_platform_admin, normalized_role: is_superadmin or perms.get("coupons"),
    "whatsapp": lambda perms, is_superadmin, is_platform_admin, normalized_role: is_superadmin or perms.get("whatsapp"),
    "seguidores": lambda perms, is_superadmin, is_platform_admin, normalized_role: is_superadmin or int(perms.get("max_portal_users") or 0) > 0,
    "ia": lambda perms, is_superadmin, is_platform_admin, normalized_role: is_superadmin or perms.get("can_use_ai"),
    "institucion_financiera": lambda perms, is_superadmin, is_platform_admin, normalized_role: is_superadmin or perms.get("can_use_financial"),
    "apartados": lambda perms, is_superadmin, is_platform_admin, normalized_role: is_superadmin or perms.get("can_use_layaway"),
    "subastas": lambda perms, is_superadmin, is_platform_admin, normalized_role: is_superadmin or perms.get("can_use_auctions"),
}


def visible_module_sections(
    role_name: str | None,
    module_sections: list[dict[str, str]],
    optional_section_integrations: dict,
    is_module_enabled,
    list_modules_payload,
    store_permissions: dict | None = None,
) -> list[dict[str, str]]:
    normalized_role = normalize_role_name(role_name)
    is_superadmin = normalized_role in {"superadministrador", "superadmin"}
    is_platform_admin = is_superadmin or normalized_role in {"administrador_multiempresa", "administrador"}
    perms = store_permissions or {}
    return [
        section
        for section in module_sections
        if optional_section_available(
            section["id"],
            optional_section_integrations,
            is_module_enabled,
            list_modules_payload,
        )
        and _SECTION_RULES.get(
            section["id"],
            lambda perms, is_superadmin, is_platform_admin, normalized_role: True,
        )(perms, is_superadmin, is_platform_admin, normalized_role)
    ]


def can_access_module_section(
    role_name: str | None,
    section_id: str,
    module_sections: list[dict[str, str]],
    optional_section_integrations: dict,
    is_module_enabled,
    list_modules_payload,
    store_permissions: dict | None = None,
) -> bool:
    return any(
        section["id"] == section_id
        for section in visible_module_sections(
            role_name,
            module_sections,
            optional_section_integrations,
            is_module_enabled,
            list_modules_payload,
            store_permissions,
        )
    )
