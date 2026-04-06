from __future__ import annotations

from fastapi_modulo.core.db import SessionLocal
from fastapi_modulo.modulos_sipet.web.modelos.core_models import Rol, Usuario
from fastapi_modulo.modulos_sipet.web.servicios.access_service import save_role_permission_profile

_FULL_ACCESS = {
    "full_access": True,
    "read_only": False,
    "department_only": False,
    "user_only": False,
    "special_permissions": False,
}

_SPECIAL_ACCESS = {
    "full_access": False,
    "read_only": False,
    "department_only": False,
    "user_only": False,
    "special_permissions": True,
}


def _with_route_aliases(
    base_levels: dict[str, dict[str, bool]],
    route_aliases: dict[str, str],
) -> dict[str, dict[str, bool]]:
    levels = {key: dict(value) for key, value in (base_levels or {}).items()}
    for route, permission_key in route_aliases.items():
        if route not in levels and permission_key in levels:
            levels[route] = dict(levels[permission_key])
    return levels


_MULTITIENDA_ROUTE_ALIASES = {
    "/multitienda": "multitienda",
    "/multitienda/inicio": "multitienda.inicio",
    "/multitienda/configuracion": "multitienda.configuracion",
    "/multitienda/productos": "multitienda.productos",
    "/multitienda/proveedores": "multitienda.proveedores",
    "/multitienda/empleados": "multitienda.empleados",
    "/multitienda/crm": "multitienda.crm",
}

_STORE_ROLE_NAMES = {"administrador_tienda", "vendedor_tienda"}

MULTITIENDA_ROLE_DEFINITIONS = (
    {
        "role_name": "administrador_tienda",
        "description": "Acceso total a su tienda dentro de Multitienda.",
        "screen_access_levels": _with_route_aliases({
            "Multitienda": {
                **_FULL_ACCESS,
            },
            "multitienda": {
                **_FULL_ACCESS,
            },
            "multitienda.inicio": {
                **_FULL_ACCESS,
            },
            "multitienda.configuracion": {
                **_FULL_ACCESS,
            },
            "multitienda.productos": {
                **_FULL_ACCESS,
            },
            "multitienda.proveedores": {
                **_FULL_ACCESS,
            },
            "multitienda.empleados": {
                **_FULL_ACCESS,
            },
            "multitienda.crm": {
                **_FULL_ACCESS,
            },
        }, _MULTITIENDA_ROUTE_ALIASES),
    },
    {
        "role_name": "vendedor_tienda",
        "description": "Acceso a productos y reportes de su tienda.",
        "screen_access_levels": _with_route_aliases({
            "Multitienda": {
                **_SPECIAL_ACCESS,
            },
            "multitienda": {
                **_SPECIAL_ACCESS,
            },
            "multitienda.inicio": {
                **_SPECIAL_ACCESS,
            },
            "Reportes": {
                "full_access": False,
                "read_only": True,
                "department_only": False,
                "user_only": False,
                "special_permissions": False,
            },
            "multitienda.productos": {
                **_SPECIAL_ACCESS,
            },
            "multitienda.proveedores": {
                **_SPECIAL_ACCESS,
            },
            "multitienda.empleados": {
                **_SPECIAL_ACCESS,
            },
            "multitienda.crm": {
                **_SPECIAL_ACCESS,
            },
        }, _MULTITIENDA_ROUTE_ALIASES),
    },
)


def ensure_multitienda_access_roles() -> None:
    db = SessionLocal()
    try:
        for definition in MULTITIENDA_ROLE_DEFINITIONS:
            role_name = str(definition["role_name"]).strip()
            description = str(definition["description"]).strip()
            existing = db.query(Rol).filter(Rol.nombre == role_name).first()
            if existing is None:
                db.add(Rol(nombre=role_name, descripcion=description))
            elif (existing.descripcion or "").strip() != description:
                existing.descripcion = description
                db.add(existing)
        db.commit()
    finally:
        db.close()

    for definition in MULTITIENDA_ROLE_DEFINITIONS:
        save_role_permission_profile(
            role_name=definition["role_name"],
            description=definition["description"],
            screen_access_levels=definition["screen_access_levels"],
        )

    db = SessionLocal()
    try:
        role_ids = {
            int(role.id)
            for role in db.query(Rol).all()
            if str(role.nombre or "").strip() in _STORE_ROLE_NAMES
        }
        dirty = False
        for user in db.query(Usuario).all():
            user_dirty = False
            role_name = str(getattr(user, "role", "") or "").strip()
            if role_name not in _STORE_ROLE_NAMES and int(getattr(user, "rol_id", 0) or 0) not in role_ids:
                continue
            if getattr(user, "app_access", None) is not None:
                user.app_access = None
                user_dirty = True
            if getattr(user, "conversation_access", None) is not None:
                user.conversation_access = None
                user_dirty = True
            if user_dirty:
                dirty = True
                db.add(user)
        if dirty:
            db.commit()
    finally:
        db.close()


__all__ = ["MULTITIENDA_ROLE_DEFINITIONS", "ensure_multitienda_access_roles"]
