from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.routes import require_any_role
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.suppliers import models, schemas
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import get_db
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.dependencies import assert_store_access, get_vendor_store as _get_vendor_store

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.get("/store/{vendor_id}", response_model=List[schemas.StoreSupplierRead])
def list_suppliers(
    vendor_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin")),
):
    _get_vendor_store(vendor_id, db)
    assert_store_access(user, vendor_id, db)
    return db.query(models.StoreSupplier).filter_by(vendor_id=vendor_id).all()


@router.post("/store/{vendor_id}", response_model=schemas.StoreSupplierRead, status_code=201)
def create_supplier(
    vendor_id: int,
    data: schemas.StoreSupplierCreate,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin")),
):
    _get_vendor_store(vendor_id, db)
    assert_store_access(user, vendor_id, db)
    supplier = models.StoreSupplier(vendor_id=vendor_id, **data.dict())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.get("/{supplier_id}", response_model=schemas.StoreSupplierRead)
def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin")),
):
    supplier = db.query(models.StoreSupplier).filter_by(id=supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    assert_store_access(user, supplier.vendor_id, db)
    return supplier


@router.put("/{supplier_id}", response_model=schemas.StoreSupplierRead)
def update_supplier(
    supplier_id: int,
    data: schemas.StoreSupplierUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin")),
):
    supplier = db.query(models.StoreSupplier).filter_by(id=supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    assert_store_access(user, supplier.vendor_id, db)
    for field, value in data.dict(exclude_unset=True).items():
        setattr(supplier, field, value)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.delete("/{supplier_id}", status_code=204)
def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin")),
):
    supplier = db.query(models.StoreSupplier).filter_by(id=supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    assert_store_access(user, supplier.vendor_id, db)
    db.delete(supplier)
    db.commit()
