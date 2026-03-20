from __future__ import annotations

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from backend.apps.users.routes import get_current_user as _get_current_user
from backend.apps.users.routes import require_role
from backend.apps.vendors.models import VendorStore
from backend.core.db import get_db as _get_db
from backend.core.db import get_db_session


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


__all__ = [
    "get_admin_user",
    "get_current_user",
    "get_current_vendor",
    "get_db",
    "get_db_session",
    "get_support_user",
]
