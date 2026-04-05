from __future__ import annotations

from sqlalchemy.orm import Session

from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.followers.models import StoreFollower
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.service_utils import (
    create_for_vendor as create_vendor_record,
    delete_entity,
    get_by_id as get_record_by_id,
    get_by_vendor as get_vendor_record,
    list_by_vendor as list_vendor_records,
)


def list_by_vendor(db: Session, vendor_id: int) -> list[StoreFollower]:
    return list_vendor_records(
        db,
        StoreFollower,
        vendor_id,
        order_by=(StoreFollower.created_at.desc(),),
    )


def get_by_id(db: Session, follower_id: int) -> StoreFollower | None:
    return get_record_by_id(db, StoreFollower, follower_id)


def get_by_vendor(db: Session, vendor_id: int, follower_id: int) -> StoreFollower | None:
    return get_vendor_record(db, StoreFollower, vendor_id, follower_id)


def get_by_vendor_user(db: Session, vendor_id: int, user_id: int) -> StoreFollower | None:
    return db.query(StoreFollower).filter_by(vendor_id=vendor_id, user_id=user_id).first()


def create_for_vendor(db: Session, vendor_id: int, *, user_id: int) -> StoreFollower:
    return create_vendor_record(db, StoreFollower, vendor_id, user_id=user_id)


def delete_follower(db: Session, follower: StoreFollower) -> None:
    delete_entity(db, follower)


def count_by_vendor(db: Session, vendor_id: int) -> int:
    return db.query(StoreFollower).filter_by(vendor_id=vendor_id).count()
