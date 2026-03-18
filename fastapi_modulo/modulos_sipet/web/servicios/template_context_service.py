from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from fastapi import Request

from fastapi_modulo.modulos_sipet.web.servicios.access_service import (
    get_user_strategy_submenu_access_levels,
    get_user_screen_access_levels,
    is_admin_or_superadmin,
    is_superadmin,
)
from fastapi_modulo.modulos_sipet.web.servicios.branding_image_service import resolve_branding_filename
from fastapi_modulo.modulos_sipet.web.servicios.icon_catalog_service import build_icon_catalog_context
from fastapi_modulo.modulos_sipet.web.servicios.identity_integration_service import merge_remote_branding
from fastapi_modulo.modulos_sipet.web.servicios.module_catalog_service import get_backend_catalog_context
from fastapi_modulo.modulos_sipet.web.servicios.session_service import CSRF_COOKIE_NAME, normalize_tenant_id
from fastapi_modulo.modulos_sipet.web.servicios.ui_shell_service import get_colores_context
from fastapi_modulo.modulos_sipet.web.servicios.visual_editor_service import backend_visual_editor_config

IDENTIDAD_LOGIN_CONFIG_PATH = (os.environ.get("IDENTIDAD_LOGIN_CONFIG_PATH") or "fastapi_modulo/modulos_sipet/web/identidad_login.json").strip()
IDENTIDAD_LOGIN_IMAGE_DIR = "fastapi_modulo/templates/imagenes"
DEFAULT_LOGIN_IDENTITY = {
    "favicon_filename": "icon.png",
    "logo_filename": "icon.png",
    "desktop_bg_filename": "fondo.jpg",
    "mobile_bg_filename": "movil.jpg",
    "company_short_name": "AVAN",
    "login_message": "Incrementando el nivel de eficiencia",
    "menu_position": "arriba",
}
APP_ENV = (os.environ.get("APP_ENV") or os.environ.get("ENVIRONMENT") or "development").strip().lower()

def _load_login_identity() -> Dict[str, str]:
    data = DEFAULT_LOGIN_IDENTITY.copy()
    if os.path.exists(IDENTIDAD_LOGIN_CONFIG_PATH):
        try:
            with open(IDENTIDAD_LOGIN_CONFIG_PATH, "r", encoding="utf-8") as fh:
                loaded = json.load(fh)
            if isinstance(loaded, dict):
                data.update({k: v for k, v in loaded.items() if isinstance(v, str)})
        except (OSError, json.JSONDecodeError):
            pass
    return data


def _build_login_asset_url(filename: Optional[str], default_filename: str) -> str:
    selected = filename or default_filename
    selected_path = os.path.join(IDENTIDAD_LOGIN_IMAGE_DIR, selected)
    if not os.path.exists(selected_path):
        selected = default_filename
        selected_path = os.path.join(IDENTIDAD_LOGIN_IMAGE_DIR, selected)
    version = int(os.path.getmtime(selected_path)) if os.path.exists(selected_path) else 0
    return f"/templates/imagenes/{selected}?v={version}"


def _build_branding_variant_url(filename: Optional[str], default_filename: str, variant: str = "") -> str:
    selected = resolve_branding_filename(IDENTIDAD_LOGIN_IMAGE_DIR, filename, default_filename, variant)
    return _build_login_asset_url(selected, default_filename)


def get_login_identity_context(request: Optional[Request] = None) -> Dict[str, str]:
    data = _load_login_identity()
    local_context = {
        "login_favicon_url": _build_branding_variant_url(
            data.get("logo_filename") or data.get("favicon_filename"),
            DEFAULT_LOGIN_IDENTITY["favicon_filename"],
            "favicon",
        ),
        "login_logo_url": _build_branding_variant_url(data.get("logo_filename"), DEFAULT_LOGIN_IDENTITY["logo_filename"], "login"),
        "login_logo_sidebar_url": _build_branding_variant_url(
            data.get("logo_filename"),
            DEFAULT_LOGIN_IDENTITY["logo_filename"],
            "sidebar",
        ),
        "login_logo_dark_url": _build_branding_variant_url(data.get("logo_filename"), DEFAULT_LOGIN_IDENTITY["logo_filename"], "dark"),
        "login_logo_light_url": _build_branding_variant_url(data.get("logo_filename"), DEFAULT_LOGIN_IDENTITY["logo_filename"], "light"),
        "login_bg_desktop_url": _build_login_asset_url(data.get("desktop_bg_filename"), DEFAULT_LOGIN_IDENTITY["desktop_bg_filename"]),
        "login_bg_mobile_url": _build_login_asset_url(data.get("mobile_bg_filename"), DEFAULT_LOGIN_IDENTITY["mobile_bg_filename"]),
        "login_company_short_name": data.get("company_short_name") or DEFAULT_LOGIN_IDENTITY["company_short_name"],
        "login_message": data.get("login_message") or DEFAULT_LOGIN_IDENTITY["login_message"],
        "menu_position": data.get("menu_position") or DEFAULT_LOGIN_IDENTITY["menu_position"],
    }
    host = ""
    tenant_id = ""
    if request is not None:
        host = (request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.hostname or "").split(",")[0].strip()
        tenant_id = normalize_tenant_id(
            getattr(request.state, "tenant_id", None)
            or request.cookies.get("tenant_id")
            or os.environ.get("DEFAULT_TENANT_ID", "default")
        )
    return merge_remote_branding(local_context, host=host, tenant_id=tenant_id)


def resolve_sidebar_logo_url(login_identity: Optional[Dict[str, str]] = None) -> str:
    identity_data = _load_login_identity()
    identity_logo_filename = str(identity_data.get("logo_filename") or "").strip()
    login_identity = login_identity or get_login_identity_context()
    identity_logo_url = str(login_identity.get("login_logo_sidebar_url") or login_identity.get("login_logo_url") or "").strip()
    if identity_logo_filename and identity_logo_filename != DEFAULT_LOGIN_IDENTITY["logo_filename"]:
        return identity_logo_url or "/templates/icon/icon.png"
    from fastapi_modulo.modulos_sipet.personalizacion.controladores.personalizar import resolve_logo_empresa_url

    default_logo_url = resolve_logo_empresa_url()
    if default_logo_url:
        return default_logo_url
    return identity_logo_url or "/templates/icon/icon.png"


def _is_dark_color(value: str) -> bool:
    color = (value or "").strip().lower()
    if color.startswith("#"):
        hex_color = color[1:]
        if len(hex_color) == 3:
            hex_color = "".join(ch * 2 for ch in hex_color)
        if len(hex_color) == 6:
            try:
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
                return luminance < 0.5
            except ValueError:
                return True
    return True


def build_not_found_context(request: Request, title: str = "Pagina no existe") -> Dict[str, str]:
    login_identity = get_login_identity_context(request)
    colores = get_colores_context()
    sidebar_top_color = (colores.get("sidebar-top") or "#1f2a3d").strip()
    is_dark_bg = _is_dark_color(sidebar_top_color)
    return {
        "request": request,
        "title": title,
        "app_favicon_url": login_identity.get("login_favicon_url"),
        "company_logo_url": login_identity.get("login_logo_url"),
        "sidebar_top_color": sidebar_top_color,
        "not_found_text_color": "#ffffff" if is_dark_bg else "#2b2b2b",
        "not_found_highlight_color": "#ffffff" if is_dark_bg else "#1f1f1f",
    }


def build_login_context(
    request: Request,
    *,
    title: str = "Login",
    login_error: str = "",
    **extra: object,
) -> dict:
    return {
        "request": request,
        "title": title,
        "login_error": login_error,
        **get_login_identity_context(request),
        **extra,
    }


def build_backend_context(
    request: Request,
    *,
    title: str,
    subtitle: Optional[str] = None,
    description: Optional[str] = None,
    content: str = "",
    view_buttons_html: str = "",
    hide_floating_actions: bool = True,
    show_page_header: bool = True,
    page_title: Optional[str] = None,
    page_description: Optional[str] = None,
    section_title: Optional[str] = None,
    section_label: Optional[str] = None,
    floating_buttons: Optional[List[Dict]] = None,
    floating_actions_html: str = "",
    floating_actions_screen: str = "personalization",
    **extra: object,
) -> dict:
    login_identity = get_login_identity_context(request)
    resolved_title = (page_title or title or "Sin titulo").strip()
    resolved_description = (page_description or description or subtitle or "Descripcion pendiente").strip()
    return {
        "request": request,
        "title": title,
        "subtitle": subtitle,
        "page_title": resolved_title,
        "page_description": resolved_description,
        "section_title": (section_title or "Contenido").strip(),
        "section_label": (section_label or "Seccion").strip(),
        "content": content,
        "view_buttons_html": view_buttons_html,
        "floating_buttons": floating_buttons,
        "floating_actions_html": floating_actions_html,
        "floating_actions_screen": floating_actions_screen,
        "hide_floating_actions": hide_floating_actions,
        "show_page_header": show_page_header,
        "colores": get_colores_context(),
        "can_manage_personalization": is_superadmin(request),
        "app_favicon_url": login_identity.get("login_favicon_url"),
        "login_logo_url": login_identity.get("login_logo_url"),
        "sidebar_logo_url": resolve_sidebar_logo_url(login_identity),
        "csrf_token": request.cookies.get(CSRF_COOKIE_NAME, ""),
        "user_strategy_submenu_access_levels": get_user_strategy_submenu_access_levels(request),
        "user_screen_access_levels": get_user_screen_access_levels(request),
        "current_role": getattr(request.state, "user_role", ""),
        "grapesjs_backend_editor_enabled": backend_visual_editor_config().get("enabled", False),
        "backend_visual_editor": backend_visual_editor_config(),
        "app_env": APP_ENV,
        "is_superadmin_user": is_superadmin(request),
        "is_admin_or_superadmin_user": is_admin_or_superadmin(request),
        **build_icon_catalog_context(),
        **get_backend_catalog_context(request),
        **extra,
    }
