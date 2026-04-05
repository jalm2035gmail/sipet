from __future__ import annotations

import logging

from sqlalchemy import text

from fastapi_modulo.modulos_sipet.web.servicios.access_service import normalize_role_name, sensitive_lookup_hash
from fastapi_modulo.modulos_sipet.web.servicios.auth_service import find_user_by_login
from fastapi_modulo.modulos.multitienda.controladores.services.roles_service import get_roles_map

_log = logging.getLogger("multitienda.scope")


def coerce_theme_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value or "").strip().lower()
    return normalized in {"1", "true", "verdadero", "si", "sí", "yes", "on", "habilitado", "enabled"}


def current_user_record(request, db, current_username) -> tuple[object, str] | None:
    cached = getattr(request.state, "_multitienda_current_user_record", None)
    if cached is not None:
        return cached
    username = current_username(request)
    if not username:
        return None
    user = find_user_by_login(db, username, login_hash=sensitive_lookup_hash(username))
    roles_by_id = get_roles_map(db)
    if user is not None:
        role_name = roles_by_id.get(user.rol_id) or normalize_role_name(getattr(user, "role", "") or "usuario")
        resolved = (user, role_name)
        setattr(request.state, "_multitienda_current_user_record", resolved)
        return resolved
    return None


def resolve_store_scope(request, db, current_user_record_fn) -> dict[str, object]:
    resolved = current_user_record_fn(request, db)
    if not resolved:
        return {"role": "usuario", "user_id": None, "store_id": None, "store_slug": "", "restricted": False}
    user, role_name = resolved
    restricted = role_name in {"administrador_tienda", "vendedor_tienda"}
    store_id = None
    store_slug = ""
    if restricted:
        store_row = db.execute(
            text(
                """
                SELECT id, store_slug
                FROM vendors
                WHERE vendor_id = :vendor_id
                LIMIT 1
                """
            ),
            {"vendor_id": int(user.id)},
        ).mappings().first()
        if not store_row:
            store_row = db.execute(
                text(
                    """
                    SELECT v.id, v.store_slug
                    FROM store_employees se
                    JOIN vendors v ON v.id = se.vendor_id
                    WHERE se.user_id = :user_id
                    ORDER BY se.id ASC
                    LIMIT 1
                    """
                ),
                {"user_id": int(user.id)},
            ).mappings().first()
        store_id = int(store_row["id"]) if store_row and store_row.get("id") is not None else None
        store_slug = str(store_row.get("store_slug") or "") if store_row else ""
    return {
        "role": role_name,
        "user_id": int(user.id),
        "store_id": store_id,
        "store_slug": store_slug,
        "restricted": restricted,
    }


def resolve_store_permissions(db, scope: dict, decode_store_theme) -> dict:
    try:
        if scope.get("store_id"):
            row = db.execute(
                text("SELECT store_theme FROM vendors WHERE id = :id LIMIT 1"),
                {"id": int(scope["store_id"])},
            ).mappings().first()
        elif scope.get("user_id"):
            row = db.execute(
                text("SELECT store_theme FROM vendors WHERE vendor_id = :uid LIMIT 1"),
                {"uid": int(scope["user_id"])},
            ).mappings().first()
        else:
            return {}
        theme = decode_store_theme(row["store_theme"]) if row else {}
        if not theme:
            return {}
        theme["can_upload_videos"] = coerce_theme_bool(theme.get("can_upload_videos"))
        theme["referrals"] = coerce_theme_bool(theme.get("referrals"))
        theme["fidelizacion"] = coerce_theme_bool(theme.get("fidelizacion"))
        theme["pwa_notifications"] = coerce_theme_bool(theme.get("pwa_notifications"))
        theme["appointments"] = coerce_theme_bool(theme.get("appointments"))
        theme["coupons"] = coerce_theme_bool(theme.get("coupons"))
        theme["whatsapp"] = coerce_theme_bool(theme.get("whatsapp"))
        theme["can_use_ai"] = coerce_theme_bool(theme.get("can_use_ai"))
        theme["can_use_financial"] = coerce_theme_bool(theme.get("can_use_financial"))
        theme["can_use_layaway"] = coerce_theme_bool(theme.get("can_use_layaway"))
        theme["can_use_auctions"] = coerce_theme_bool(theme.get("can_use_auctions"))
        return theme
    except Exception:
        _log.exception("Error al resolver permisos de tienda para scope=%s", scope)
        return {}
