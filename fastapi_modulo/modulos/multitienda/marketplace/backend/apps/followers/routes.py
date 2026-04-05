from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.routes import require_any_role
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.followers import schemas, service
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.vendors.models import VendorStore
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import get_db

router = APIRouter(prefix="/followers", tags=["followers"])


@router.get("/store/{vendor_id}", response_model=List[schemas.StoreFollowerRead])
def list_followers(
    vendor_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin")),
):
    store = db.query(VendorStore).filter_by(id=vendor_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Tienda no encontrada")
    return service.list_by_vendor(db, vendor_id)


@router.post("/store/{vendor_id}/follow", response_model=schemas.StoreFollowerRead, status_code=201)
def follow_store(
    vendor_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("customer", "vendor", "superadmin")),
):
    store = db.query(VendorStore).filter_by(id=vendor_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Tienda no encontrada")
    existing = service.get_by_vendor_user(db, vendor_id, user.id)
    if existing:
        raise HTTPException(status_code=409, detail="Ya sigues esta tienda")
    follower = service.create_for_vendor(db, vendor_id, user_id=user.id)
    db.commit()
    return follower


@router.delete("/store/{vendor_id}/unfollow", status_code=204)
def unfollow_store(
    vendor_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("customer", "vendor", "superadmin")),
):
    follower = service.get_by_vendor_user(db, vendor_id, user.id)
    if not follower:
        raise HTTPException(status_code=404, detail="No sigues esta tienda")
    service.delete_follower(db, follower)
    db.commit()


@router.get("/store/{vendor_id}/count")
def follower_count(vendor_id: int, db: Session = Depends(get_db)):
    count = service.count_by_vendor(db, vendor_id)
    return {"vendor_id": vendor_id, "followers": count}
