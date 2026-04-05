from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.routes import require_any_role
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.layaways import models, schemas, service
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import get_db
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.dependencies import assert_store_access, get_vendor_store as _get_vendor_store

router = APIRouter(prefix="/layaways", tags=["layaways"])


@router.get("/store/{vendor_id}", response_model=List[schemas.StoreLayawayRead])
def list_layaways(
    vendor_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin", "store_employee")),
):
    _get_vendor_store(vendor_id, db)
    assert_store_access(user, vendor_id, db)
    return service.list_by_vendor(db, vendor_id)


@router.post("/store/{vendor_id}", response_model=schemas.StoreLayawayRead, status_code=201)
def create_layaway(
    vendor_id: int,
    data: schemas.StoreLayawayCreate,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("customer", "vendor", "superadmin", "store_employee")),
):
    _get_vendor_store(vendor_id, db)
    if data.downpayment > data.total_amount:
        raise HTTPException(status_code=400, detail="El enganche no puede ser mayor al total")
    layaway = service.create_basic(db, vendor_id, {
        "customer_user_id": user.id,
        "product_id": data.product_id,
        "total_amount": data.total_amount,
        "downpayment": data.downpayment,
        "due_date": data.due_date,
        "notes": data.notes,
    })
    db.commit()
    return layaway


@router.put("/{layaway_id}", response_model=schemas.StoreLayawayRead)
def update_layaway(
    layaway_id: int,
    data: schemas.StoreLayawayUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin", "store_employee")),
):
    layaway = db.query(models.StoreLayaway).filter_by(id=layaway_id).first()
    if not layaway:
        raise HTTPException(status_code=404, detail="Apartado no encontrado")
    assert_store_access(user, layaway.vendor_id, db)
    updates = service.update_basic(db, layaway.vendor_id, layaway_id, data.dict(exclude_unset=True))
    if not updates:
        raise HTTPException(status_code=404, detail="Apartado no encontrado")
    db.commit()
    return updates


@router.get("/my", response_model=List[schemas.StoreLayawayRead])
def my_layaways(
    db: Session = Depends(get_db),
    user=Depends(require_any_role("customer", "vendor", "superadmin", "store_employee")),
):
    return db.query(models.StoreLayaway).filter_by(customer_user_id=user.id).all()
