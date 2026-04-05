from __future__ import annotations

from typing import Any, Optional

from fastapi import UploadFile

from fastapi_modulo.modulos_sipet.web.servicios.login_identity_service import (
    DEFAULT_LOGIN_IDENTITY,
    _build_login_asset_url,
    _load_login_identity,
    clear_frontend_page_cache,
    remove_login_image_if_custom,
    save_login_identity,
    store_login_image,
)


def build_identidad_view_context(*, form_values: Optional[dict[str, str]] = None) -> dict[str, Any]:
    identity = _load_login_identity()
    if form_values:
        identity.update({key: str(value or "").strip() for key, value in form_values.items()})
    favicon_url = _build_login_asset_url(identity.get("favicon_filename"), DEFAULT_LOGIN_IDENTITY["favicon_filename"])
    logo_url = _build_login_asset_url(identity.get("logo_filename"), DEFAULT_LOGIN_IDENTITY["logo_filename"])
    login_logo_url = _build_login_asset_url(identity.get("login_logo_filename"), DEFAULT_LOGIN_IDENTITY["login_logo_filename"])
    desktop_bg_url = _build_login_asset_url(identity.get("desktop_bg_filename"), DEFAULT_LOGIN_IDENTITY["desktop_bg_filename"])
    mobile_bg_url = _build_login_asset_url(identity.get("mobile_bg_filename"), DEFAULT_LOGIN_IDENTITY["mobile_bg_filename"])
    loaded_assets = sum(1 for value in [favicon_url, logo_url, login_logo_url, desktop_bg_url, mobile_bg_url] if (value or "").strip())
    consistency = max(60, min(100, int(round((loaded_assets / 5) * 100)))) if loaded_assets else 60
    return {
        "company_short_name": identity.get("company_short_name", DEFAULT_LOGIN_IDENTITY["company_short_name"]),
        "login_message": identity.get("login_message", DEFAULT_LOGIN_IDENTITY["login_message"]),
        "menu_position": (identity.get("menu_position") or DEFAULT_LOGIN_IDENTITY["menu_position"]).strip().lower(),
        "favicon_url": favicon_url,
        "logo_url": logo_url,
        "login_logo_url": login_logo_url,
        "desktop_bg_url": desktop_bg_url,
        "mobile_bg_url": mobile_bg_url,
        "loaded_assets": loaded_assets,
        "consistency": consistency,
        "sidebar_style_variant": identity.get("sidebar_style_variant", "modern"),
    }


async def save_identity_assets(
    *,
    company_short_name: str,
    login_message: str,
    menu_position: str,
    sidebar_style_variant: str,
    favicon: Optional[UploadFile],
    logo_empresa: Optional[UploadFile],
    logo_login: Optional[UploadFile],
    fondo_escritorio: Optional[UploadFile],
    fondo_movil: Optional[UploadFile],
    remove_favicon: bool,
    remove_logo: bool,
    remove_login_logo: bool,
    remove_desktop: bool,
    remove_mobile: bool,
) -> None:
    current = _load_login_identity()
    current["company_short_name"] = company_short_name or DEFAULT_LOGIN_IDENTITY["company_short_name"]
    current["login_message"] = login_message or DEFAULT_LOGIN_IDENTITY["login_message"]
    current["menu_position"] = menu_position
    current["sidebar_style_variant"] = "original" if str(sidebar_style_variant).strip().lower() == "original" else "modern"

    if remove_favicon:
        remove_login_image_if_custom(current.get("favicon_filename"))
        current["favicon_filename"] = DEFAULT_LOGIN_IDENTITY["favicon_filename"]
    if remove_logo:
        remove_login_image_if_custom(current.get("logo_filename"))
        current["logo_filename"] = DEFAULT_LOGIN_IDENTITY["logo_filename"]
    if remove_login_logo:
        remove_login_image_if_custom(current.get("login_logo_filename"))
        current["login_logo_filename"] = current.get("logo_filename") or DEFAULT_LOGIN_IDENTITY["logo_filename"]
    if remove_desktop:
        remove_login_image_if_custom(current.get("desktop_bg_filename"))
        current["desktop_bg_filename"] = DEFAULT_LOGIN_IDENTITY["desktop_bg_filename"]
    if remove_mobile:
        remove_login_image_if_custom(current.get("mobile_bg_filename"))
        current["mobile_bg_filename"] = DEFAULT_LOGIN_IDENTITY["mobile_bg_filename"]

    new_favicon = await store_login_image(favicon, "favicon") if favicon else None
    if new_favicon:
        remove_login_image_if_custom(current.get("favicon_filename"))
        current["favicon_filename"] = new_favicon

    new_logo = await store_login_image(logo_empresa, "logo_empresa") if logo_empresa else None
    if new_logo:
        remove_login_image_if_custom(current.get("logo_filename"))
        current["logo_filename"] = new_logo

    new_login_logo = await store_login_image(logo_login, "logo_login") if logo_login else None
    if new_login_logo:
        remove_login_image_if_custom(current.get("login_logo_filename"))
        current["login_logo_filename"] = new_login_logo

    new_desktop = await store_login_image(fondo_escritorio, "fondo_escritorio") if fondo_escritorio else None
    if new_desktop:
        remove_login_image_if_custom(current.get("desktop_bg_filename"))
        current["desktop_bg_filename"] = new_desktop

    new_mobile = await store_login_image(fondo_movil, "fondo_movil") if fondo_movil else None
    if new_mobile:
        remove_login_image_if_custom(current.get("mobile_bg_filename"))
        current["mobile_bg_filename"] = new_mobile

    save_login_identity(current)
    clear_frontend_page_cache()
