from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.routes import require_any_role
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.coupons import schemas, service
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import get_db
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.dependencies import assert_store_access, get_vendor_store as _get_vendor_store

router = APIRouter(prefix="/coupons", tags=["coupons"])


@router.get("/store/{vendor_id}", response_model=List[schemas.StoreCouponRead])
def list_coupons(
    vendor_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin")),
):
    _get_vendor_store(vendor_id, db)
    assert_store_access(user, vendor_id, db)
    return service.list_by_vendor(db, vendor_id)


@router.post("/store/{vendor_id}", response_model=schemas.StoreCouponRead, status_code=201)
def create_coupon(
    vendor_id: int,
    data: schemas.StoreCouponCreate,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin")),
):
    _get_vendor_store(vendor_id, db)
    assert_store_access(user, vendor_id, db)
    if service.get_by_vendor_code(db, vendor_id, data.code):
        raise HTTPException(status_code=409, detail="Ya existe un cupón con ese código en esta tienda")
    coupon = service.create_for_vendor(db, vendor_id, **data.dict())
    db.commit()
    return coupon


@router.get("/{coupon_id}", response_model=schemas.StoreCouponRead)
def get_coupon(coupon_id: int, db: Session = Depends(get_db)):
    coupon = service.get_by_id(db, coupon_id)
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
    coupon = service.get_by_id(db, coupon_id)
    if not coupon:
        raise HTTPException(status_code=404, detail="Cupón no encontrado")
    assert_store_access(user, coupon.vendor_id, db)
    coupon = service.update_coupon(db, coupon, **data.dict(exclude_unset=True))
    db.commit()
    return coupon


@router.delete("/{coupon_id}", status_code=204)
def delete_coupon(
    coupon_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin")),
):
    coupon = service.get_by_id(db, coupon_id)
    if not coupon:
        raise HTTPException(status_code=404, detail="Cupón no encontrado")
    assert_store_access(user, coupon.vendor_id, db)
    service.delete_coupon(db, coupon)
    db.commit()


@router.post("/validate/")
def validate_coupon(code: str, vendor_id: int, db: Session = Depends(get_db)):
    result = service.validate_coupon_for_vendor(db, vendor_id, code)
    if not result["valid"]:
        detail = result["error"]
        if detail == "Cupón inválido o inactivo.":
            raise HTTPException(status_code=404, detail=detail[:-1])
        raise HTTPException(status_code=400, detail=detail[:-1])
    return {
        "valid": True,
        "discount_type": result["discount_type"],
        "discount_value": result["discount_value"],
    }
