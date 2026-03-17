from __future__ import annotations

from typing import Any

from fastapi_modulo.modulos_sipet.web.servicios.access_service import normalize_role_name

MODULE_ICON_MAP = {
    "crm": "fa-solid fa-users-rectangle",
    "auditoria": "fa-solid fa-clipboard-check",
    "activo_fijo": "fa-solid fa-building-circle-check",
    "control_interno": "fa-solid fa-list-check",
    "control_seguimiento": "fa-solid fa-shield-check",
    "capacitacion": "fa-solid fa-book-open",
    "brujula": "fa-solid fa-compass",
    "pld": "fa-solid fa-shield-halved",
    "intelicoop": "fa-solid fa-microchip",
    "mkt": "fa-solid fa-envelope-open-text",
    "encuestas": "fa-solid fa-square-poll-vertical",
    "system_admin": "fa-solid fa-cubes",
}
ROLE_ICON_MAP = {
    "superadministrador": "fa-solid fa-user-shield",
    "administrador": "fa-solid fa-user-gear",
    "administrador_multiempresa": "fa-solid fa-building-user",
    "autoridades": "fa-solid fa-landmark",
    "usuario": "fa-solid fa-user",
}
ACTION_ICON_MAP = {
    "create": "fa-solid fa-plus",
    "update": "fa-solid fa-pen",
    "delete": "fa-solid fa-trash",
    "view": "fa-regular fa-eye",
    "export": "fa-solid fa-file-export",
    "download": "fa-solid fa-download",
    "security": "fa-solid fa-shield-halved",
    "warning": "fa-solid fa-triangle-exclamation",
    "success": "fa-solid fa-circle-check",
    "settings": "fa-solid fa-gear",
}
DEFAULT_MODULE_ICON = "fa-regular fa-circle"


def resolve_module_icon(module_key: str, fallback_icon: str = "") -> str:
    key = str(module_key or "").strip().lower()
    return MODULE_ICON_MAP.get(key) or str(fallback_icon or "").strip() or DEFAULT_MODULE_ICON


def resolve_role_icon(role_name: str) -> str:
    return ROLE_ICON_MAP.get(normalize_role_name(role_name), ROLE_ICON_MAP["usuario"])


def resolve_action_icon(action_name: str) -> str:
    return ACTION_ICON_MAP.get(str(action_name or "").strip().lower(), DEFAULT_MODULE_ICON)


def build_icon_catalog_context() -> dict[str, Any]:
    return {
        "module_icon_map": MODULE_ICON_MAP.copy(),
        "role_icon_map": ROLE_ICON_MAP.copy(),
        "action_icon_map": ACTION_ICON_MAP.copy(),
        "default_module_icon": DEFAULT_MODULE_ICON,
    }
