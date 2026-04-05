from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.routes import require_any_role
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.reservations import schemas, service
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import get_db
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.dependencies import assert_store_access, get_vendor_store as _get_vendor_store

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.get("/store/{vendor_id}", response_model=List[schemas.StoreReservationRead])
def list_reservations(
    vendor_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin", "store_employee")),
):
    _get_vendor_store(vendor_id, db)
    assert_store_access(user, vendor_id, db)
    return service.list_by_vendor(db, vendor_id)


@router.post("/store/{vendor_id}", response_model=schemas.StoreReservationRead, status_code=201)
def create_reservation(
    vendor_id: int,
    data: schemas.StoreReservationCreate,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("customer", "vendor", "superadmin", "store_employee")),
):
    _get_vendor_store(vendor_id, db)
    reservation = service.create_for_vendor(
        db,
        vendor_id,
        customer_user_id=user.id,
        product_id=data.product_id,
        reservation_date=data.reservation_date,
        time_slot=data.time_slot,
        duration_minutes=data.duration_minutes,
        notes=data.notes or "",
    )
    db.commit()
    return reservation


@router.put("/{reservation_id}", response_model=schemas.StoreReservationRead)
def update_reservation(
    reservation_id: int,
    data: schemas.StoreReservationUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin", "store_employee")),
):
    reservation = service.get_by_id(db, reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservación no encontrada")
    assert_store_access(user, reservation.vendor_id, db)
    reservation = service.update_reservation(db, reservation, **data.dict(exclude_unset=True))
    db.commit()
    return reservation


@router.delete("/{reservation_id}", status_code=204)
def delete_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin")),
):
    reservation = service.get_by_id(db, reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservación no encontrada")
    assert_store_access(user, reservation.vendor_id, db)
    service.delete_reservation(db, reservation)
    db.commit()


@router.get("/my", response_model=List[schemas.StoreReservationRead])
def my_reservations(
    db: Session = Depends(get_db),
    user=Depends(require_any_role("customer", "vendor", "superadmin", "store_employee")),
):
    return service.list_by_customer(db, user.id)
