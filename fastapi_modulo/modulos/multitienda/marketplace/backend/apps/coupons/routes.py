from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.routes import require_any_role
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.coupons import models, schemas
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import get_db
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.dependencies import assert_store_access, get_vendor_store as _get_vendor_store
from datetime import datetime

router = APIRouter(prefix="/coupons", tags=["coupons"])


@router.get("/store/{vendor_id}", response_model=List[schemas.StoreCouponRead])
def list_coupons(
    vendor_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin")),
):
    _get_vendor_store(vendor_id, db)
    assert_store_access(user, vendor_id, db)
    return db.query(models.StoreCoupon).filter_by(vendor_id=vendor_id).all()


@router.post("/store/{vendor_id}", response_model=schemas.StoreCouponRead, status_code=201)
def create_coupon(
    vendor_id: int,
    data: schemas.StoreCouponCreate,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin")),
):
    _get_vendor_store(vendor_id, db)
    assert_store_access(user, vendor_id, db)
    if db.query(models.StoreCoupon).filter_by(vendor_id=vendor_id, code=data.code).first():
        raise HTTPException(status_code=409, detail="Ya existe un cupón con ese código en esta tienda")
    coupon = models.StoreCoupon(vendor_id=vendor_id, **data.dict())
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


@router.get("/{coupon_id}", response_model=schemas.StoreCouponRead)
def get_coupon(coupon_id: int, db: Session = Depends(get_db)):
    coupon = db.query(models.StoreCoupon).filter_by(id=coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Cupón no encontrado")
    return coupon


@router.put("/{coupon_id}", response_model=schemas.StoreCouponRead)
def update_coupon(
    coupon_id: int,
    data: schemas.StoreCouponUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin")),
):
    coupon = db.query(models.StoreCoupon).filter_by(id=coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Cupón no encontrado")
    assert_store_access(user, coupon.vendor_id, db)
    for field, value in data.dict(exclude_unset=True).items():
        setattr(coupon, field, value)
    db.commit()
    db.refresh(coupon)
    return coupon


@router.delete("/{coupon_id}", status_code=204)
def delete_coupon(
    coupon_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin")),
):
    coupon = db.query(models.StoreCoupon).filter_by(id=coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Cupón no encontrado")
    assert_store_access(user, coupon.vendor_id, db)
    db.delete(coupon)
    db.commit()


@router.post("/validate/")
def validate_coupon(code: str, vendor_id: int, db: Session = Depends(get_db)):
    now = datetime.utcnow()
    coupon = db.query(models.StoreCoupon).filter_by(vendor_id=vendor_id, code=code, is_active=True).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Cupón inválido o inactivo")
    if coupon.valid_from and now < coupon.valid_from:
        raise HTTPException(status_code=400, detail="El cupón aún no es válido")
    if coupon.valid_until and now > coupon.valid_until:
        raise HTTPException(status_code=400, detail="El cupón ha expirado")
    if coupon.max_uses is not None and coupon.uses_count >= coupon.max_uses:
        raise HTTPException(status_code=400, detail="El cupón ha alcanzado su límite de usos")
    return {"valid": True, "discount_type": coupon.discount_type, "discount_value": float(coupon.discount_value)}
