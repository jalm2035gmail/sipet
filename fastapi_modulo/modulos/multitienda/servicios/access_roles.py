from __future__ import annotations

from fastapi_modulo.core.db import SessionLocal
from fastapi_modulo.modulos_sipet.web.modelos.core_models import Rol
from fastapi_modulo.modulos_sipet.web.servicios.access_service import save_role_permission_profile

MULTITIENDA_ROLE_DEFINITIONS = (
    {
        "role_name": "administrador_tienda",
        "description": "Acceso total a su tienda dentro de Multitienda.",
        "screen_access_levels": {
            "Multitienda": {
                "full_access": True,
                "read_only": False,
                "department_only": False,
                "user_only": False,
                "special_permissions": False,
            },
            "multitienda": {
                "full_access": True,
                "read_only": False,
                "department_only": False,
                "user_only": False,
                "special_permissions": False,
            },
            "multitienda.inicio": {
                "full_access": True,
                "read_only": False,
                "department_only": False,
                "user_only": False,
                "special_permissions": False,
            },
            "multitienda.configuracion": {
                "full_access": True,
                "read_only": False,
                "department_only": False,
                "user_only": False,
                "special_permissions": False,
            },
            "multitienda.productos": {
                "full_access": True,
                "read_only": False,
                "department_only": False,
                "user_only": False,
                "special_permissions": False,
            },
            "multitienda.proveedores": {
                "full_access": True,
                "read_only": False,
                "department_only": False,
                "user_only": False,
                "special_permissions": False,
            },
            "multitienda.empleados": {
                "full_access": True,
                "read_only": False,
                "department_only": False,
                "user_only": False,
                "special_permissions": False,
            },
            "multitienda.crm": {
                "full_access": True,
                "read_only": False,
                "department_only": False,
                "user_only": False,
                "special_permissions": False,
            },
        },
    },
    {
        "role_name": "vendedor_tienda",
        "description": "Acceso a productos y reportes de su tienda.",
        "screen_access_levels": {
            "Multitienda": {
                "full_access": False,
                "read_only": False,
                "department_only": False,
                "user_only": False,
                "special_permissions": True,
            },
            "multitienda": {
                "full_access": False,
                "read_only": False,
                "department_only": False,
                "user_only": False,
                "special_permissions": True,
            },
            "multitienda.inicio": {
                "full_access": False,
                "read_only": False,
                "department_only": False,
                "user_only": False,
                "special_permissions": True,
            },
            "Reportes": {
                "full_access": False,
                "read_only": True,
                "department_only": False,
                "user_only": False,
                "special_permissions": False,
            },
            "multitienda.productos": {
                "full_access": False,
                "read_only": False,
                "department_only": False,
                "user_only": False,
                "special_permissions": True,
            },
            "multitienda.proveedores": {
                "full_access": False,
                "read_only": False,
                "department_only": False,
                "user_only": False,
                "special_permissions": True,
            },
            "multitienda.empleados": {
                "full_access": False,
                "read_only": False,
                "department_only": False,
                "user_only": False,
                "special_permissions": True,
            },
            "multitienda.crm": {
                "full_access": False,
                "read_only": False,
                "department_only": False,
                "user_only": False,
                "special_permissions": True,
            },
        },
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


__all__ = ["MULTITIENDA_ROLE_DEFINITIONS", "ensure_multitienda_access_roles"]
