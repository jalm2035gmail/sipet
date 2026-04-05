from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.routes import require_any_role, get_current_user
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.reservations import models, schemas
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
    return db.query(models.StoreReservation).filter_by(vendor_id=vendor_id).all()


@router.post("/store/{vendor_id}", response_model=schemas.StoreReservationRead, status_code=201)
def create_reservation(
    vendor_id: int,
    data: schemas.StoreReservationCreate,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("customer", "vendor", "superadmin", "store_employee")),
):
    _get_vendor_store(vendor_id, db)
    reservation = models.StoreReservation(
        vendor_id=vendor_id,
        customer_user_id=user.id,
        product_id=data.product_id,
        reservation_date=data.reservation_date,
        time_slot=data.time_slot,
        duration_minutes=data.duration_minutes,
        notes=data.notes,
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation


@router.put("/{reservation_id}", response_model=schemas.StoreReservationRead)
def update_reservation(
    reservation_id: int,
    data: schemas.StoreReservationUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin", "store_employee")),
):
    reservation = db.query(models.StoreReservation).filter_by(id=reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservación no encontrada")
    assert_store_access(user, reservation.vendor_id, db)
    for field, value in data.dict(exclude_unset=True).items():
        setattr(reservation, field, value)
    if data.status == schemas.ReservationStatus.confirmed:
        reservation.confirmed_at = datetime.utcnow()
    elif data.status == schemas.ReservationStatus.cancelled:
        reservation.cancelled_at = datetime.utcnow()
    db.commit()
    db.refresh(reservation)
    return reservation


@router.delete("/{reservation_id}", status_code=204)
def delete_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin")),
):
    reservation = db.query(models.StoreReservation).filter_by(id=reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservación no encontrada")
    assert_store_access(user, reservation.vendor_id, db)
    db.delete(reservation)
    db.commit()


@router.get("/my", response_model=List[schemas.StoreReservationRead])
def my_reservations(
    db: Session = Depends(get_db),
    user=Depends(require_any_role("customer", "vendor", "superadmin", "store_employee")),
):
    return db.query(models.StoreReservation).filter_by(customer_user_id=user.id).all()
