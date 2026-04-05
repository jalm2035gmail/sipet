from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.reservations.models import StoreReservation
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.reservations.schemas import ReservationStatus


def list_by_vendor(db: Session, vendor_id: int) -> list[StoreReservation]:
    return (
        db.query(StoreReservation)
        .filter_by(vendor_id=vendor_id)
        .order_by(StoreReservation.reservation_date.desc())
        .all()
    )


def list_by_customer(db: Session, user_id: int) -> list[StoreReservation]:
    return db.query(StoreReservation).filter_by(customer_user_id=user_id).all()


def get_by_id(db: Session, reservation_id: int) -> StoreReservation | None:
    return db.query(StoreReservation).filter_by(id=reservation_id).first()


def get_by_vendor(db: Session, vendor_id: int, reservation_id: int) -> StoreReservation | None:
    return db.query(StoreReservation).filter_by(id=reservation_id, vendor_id=vendor_id).first()


def create_for_vendor(
    db: Session,
    vendor_id: int,
    *,
    customer_user_id: int,
    product_id=None,
    reservation_date=None,
    time_slot=None,
    duration_minutes: int = 60,
    notes: str = "",
) -> StoreReservation:
    reservation = StoreReservation(
        vendor_id=vendor_id,
        customer_user_id=customer_user_id,
        product_id=product_id,
        reservation_date=reservation_date,
        time_slot=time_slot,
        duration_minutes=duration_minutes,
        notes=notes,
    )
    db.add(reservation)
    db.flush()
    db.refresh(reservation)
    return reservation


def update_reservation(db: Session, reservation: StoreReservation, **updates) -> StoreReservation:
    for field, value in updates.items():
        setattr(reservation, field, value)
    status = updates.get("status")
    if status == ReservationStatus.confirmed:
        reservation.confirmed_at = datetime.utcnow()
    elif status == ReservationStatus.cancelled:
        reservation.cancelled_at = datetime.utcnow()
    db.flush()
    db.refresh(reservation)
    return reservation


def delete_reservation(db: Session, reservation: StoreReservation) -> None:
    db.delete(reservation)
    db.flush()
