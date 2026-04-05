from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.reservations.models import StoreReservation
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.reservations.schemas import ReservationStatus
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.service_utils import (
    create_for_vendor as create_vendor_record,
    delete_entity,
    get_by_id as get_record_by_id,
    get_by_vendor as get_vendor_record,
    list_by_vendor as list_vendor_records,
    update_entity,
)


def list_by_vendor(db: Session, vendor_id: int) -> list[StoreReservation]:
    return list_vendor_records(
        db,
        StoreReservation,
        vendor_id,
        order_by=(StoreReservation.reservation_date.desc(),),
    )


def list_by_customer(db: Session, user_id: int) -> list[StoreReservation]:
    return db.query(StoreReservation).filter_by(customer_user_id=user_id).all()


def get_by_id(db: Session, reservation_id: int) -> StoreReservation | None:
    return get_record_by_id(db, StoreReservation, reservation_id)


def get_by_vendor(db: Session, vendor_id: int, reservation_id: int) -> StoreReservation | None:
    return get_vendor_record(db, StoreReservation, vendor_id, reservation_id)


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
    reservation = create_vendor_record(
        db,
        StoreReservation,
        vendor_id,
        customer_user_id=customer_user_id,
        product_id=product_id,
        reservation_date=reservation_date,
        time_slot=time_slot,
        duration_minutes=duration_minutes,
        notes=notes,
    )
    return reservation


def update_reservation(db: Session, reservation: StoreReservation, **updates) -> StoreReservation:
    update_entity(db, reservation, **updates)
    status = updates.get("status")
    if status == ReservationStatus.confirmed:
        reservation.confirmed_at = datetime.utcnow()
    elif status == ReservationStatus.cancelled:
        reservation.cancelled_at = datetime.utcnow()
    db.flush()
    db.refresh(reservation)
    return reservation


def delete_reservation(db: Session, reservation: StoreReservation) -> None:
    delete_entity(db, reservation)
