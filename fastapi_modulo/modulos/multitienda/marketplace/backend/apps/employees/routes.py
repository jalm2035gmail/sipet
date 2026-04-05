from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.routes import require_any_role
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.employees import models, schemas
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import get_db
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.dependencies import assert_store_access, get_vendor_store as _get_vendor_store

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("/store/{vendor_id}", response_model=List[schemas.StoreEmployeeRead])
def list_employees(
    vendor_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin", "store_employee")),
):
    _get_vendor_store(vendor_id, db)
    assert_store_access(user, vendor_id, db)
    return db.query(models.StoreEmployee).filter_by(vendor_id=vendor_id).all()


@router.post("/store/{vendor_id}", response_model=schemas.StoreEmployeeRead, status_code=201)
def create_employee(
    vendor_id: int,
    data: schemas.StoreEmployeeCreate,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin")),
):
    _get_vendor_store(vendor_id, db)
    assert_store_access(user, vendor_id, db)
    existing = db.query(models.StoreEmployee).filter_by(vendor_id=vendor_id, user_id=data.user_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="El usuario ya es empleado de esta tienda")
    employee = models.StoreEmployee(
        vendor_id=vendor_id,
        user_id=data.user_id,
        role=data.role,
        position=data.position,
        is_active=data.is_active,
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@router.put("/{employee_id}", response_model=schemas.StoreEmployeeRead)
def update_employee(
    employee_id: int,
    data: schemas.StoreEmployeeUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin")),
):
    employee = db.query(models.StoreEmployee).filter_by(id=employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    assert_store_access(user, employee.vendor_id, db)
    for field, value in data.dict(exclude_unset=True).items():
        setattr(employee, field, value)
    db.commit()
    db.refresh(employee)
    return employee


@router.delete("/{employee_id}", status_code=204)
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin")),
):
    employee = db.query(models.StoreEmployee).filter_by(id=employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    assert_store_access(user, employee.vendor_id, db)
    db.delete(employee)
    db.commit()
