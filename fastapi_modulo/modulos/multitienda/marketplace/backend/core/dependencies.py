from __future__ import annotations

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.routes import (
    get_current_user as _get_current_user,
)
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.routes import require_role, require_any_role
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.vendors.models import VendorStore
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import get_db as _get_db
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import get_db_session


def get_db():
    return Depends(_get_db)


def get_current_user():
    return Depends(_get_current_user)


def get_admin_user():
    return Depends(require_role("superadmin"))


def get_support_user():
    return Depends(require_role("superadmin"))


def get_current_vendor(
    user=Depends(require_role("vendor")),
    db: Session = Depends(_get_db),
):
    store = db.query(VendorStore).filter_by(vendor_id=user.id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Vendor store not found")
    return store


def get_vendor_or_admin(
    user=Depends(require_any_role("vendor", "superadmin")),
    db: Session = Depends(_get_db),
):
    """Returns the VendorStore for vendors; returns None for superadmin (access all)."""
    user_type = user.user_type.value if hasattr(user.user_type, "value") else str(user.user_type)
    if user_type == "superadmin":
        return None
    store = db.query(VendorStore).filter_by(vendor_id=user.id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Vendor store not found")
    return store


def assert_store_access(user, vendor_id: int, db: Session) -> None:
    """
    Enforce store isolation: the authenticated user must own or work for the store.

    - superadmin: always allowed
    - vendor: must own the store (VendorStore.id == vendor_id AND VendorStore.vendor_id == user.id)
    - store_employee: must be an active employee of the store
    - customer / financial_analyst: denied (use role-specific deps instead)
    """
    user_type = user.user_type.value if hasattr(user.user_type, "value") else str(user.user_type)
    if user_type == "superadmin":
        return
    if user_type == "vendor":
        store = db.query(VendorStore).filter(
            VendorStore.id == vendor_id,
            VendorStore.vendor_id == user.id,
        ).first()
        if not store:
            raise HTTPException(status_code=403, detail="No tienes acceso a esta tienda")
        return
    if user_type == "store_employee":
        from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.employees.models import StoreEmployee
        emp = db.query(StoreEmployee).filter(
            StoreEmployee.vendor_id == vendor_id,
            StoreEmployee.user_id == user.id,
            StoreEmployee.is_active.is_(True),
        ).first()
        if not emp:
            raise HTTPException(status_code=403, detail="No eres empleado de esta tienda")
        return
    raise HTTPException(status_code=403, detail="No autorizado")


def get_vendor_id_for_user(user, db: Session) -> int:
    """
    Resolves the VendorStore.id for a vendor or store_employee user.
    Raises 403/404 if not applicable.
    """
    user_type = user.user_type.value if hasattr(user.user_type, "value") else str(user.user_type)
    if user_type == "vendor":
        store = db.query(VendorStore).filter_by(vendor_id=user.id).first()
        if not store:
            raise HTTPException(status_code=404, detail="Tienda no encontrada")
        return store.id
    if user_type == "store_employee":
        from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.employees.models import StoreEmployee
        emp = db.query(StoreEmployee).filter(
            StoreEmployee.user_id == user.id,
            StoreEmployee.is_active.is_(True),
        ).first()
        if not emp:
            raise HTTPException(status_code=403, detail="No estás asignado a ninguna tienda")
        return emp.vendor_id
    raise HTTPException(status_code=403, detail="No autorizado")


def get_vendor_store(vendor_id: int, db: Session) -> VendorStore:
    """Obtiene un VendorStore por id o lanza 404."""
    store = db.query(VendorStore).filter_by(id=vendor_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Tienda no encontrada")
    return store


import secrets as _secrets

_SESSION_COOKIE = "mt_session"
_SESSION_KEY_HEADER = "X-Session-Key"


def get_session_key(request, response) -> str:
    """Obtiene la session_key del header, cookie, o genera una nueva."""
    from fastapi import Request, Response
    key = (
        request.headers.get(_SESSION_KEY_HEADER)
        or request.cookies.get(_SESSION_COOKIE)
    )
    if not key:
        key = _secrets.token_urlsafe(32)
        response.set_cookie(
            _SESSION_COOKIE, key,
            max_age=60 * 60 * 24 * 365,
            httponly=True,
            samesite="lax",
        )
    return key


__all__ = [
    "assert_store_access",
    "get_admin_user",
    "get_current_user",
    "get_current_vendor",
    "get_db",
    "get_db_session",
    "get_session_key",
    "get_support_user",
    "get_vendor_id_for_user",
    "get_vendor_or_admin",
    "get_vendor_store",
    "require_any_role",
    "require_role",
]
