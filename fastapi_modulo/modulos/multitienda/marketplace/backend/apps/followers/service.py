from __future__ import annotations

from sqlalchemy.orm import Session

from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.followers.models import StoreFollower


def list_by_vendor(db: Session, vendor_id: int) -> list[StoreFollower]:
    return (
        db.query(StoreFollower)
        .filter_by(vendor_id=vendor_id)
        .order_by(StoreFollower.created_at.desc())
        .all()
    )


def get_by_id(db: Session, follower_id: int) -> StoreFollower | None:
    return db.query(StoreFollower).filter_by(id=follower_id).first()


def get_by_vendor(db: Session, vendor_id: int, follower_id: int) -> StoreFollower | None:
    return db.query(StoreFollower).filter_by(id=follower_id, vendor_id=vendor_id).first()


def get_by_vendor_user(db: Session, vendor_id: int, user_id: int) -> StoreFollower | None:
    return db.query(StoreFollower).filter_by(vendor_id=vendor_id, user_id=user_id).first()


def create_for_vendor(db: Session, vendor_id: int, *, user_id: int) -> StoreFollower:
    follower = StoreFollower(vendor_id=vendor_id, user_id=user_id)
    db.add(follower)
    db.flush()
    db.refresh(follower)
    return follower


def delete_follower(db: Session, follower: StoreFollower) -> None:
    db.delete(follower)
    db.flush()


def count_by_vendor(db: Session, vendor_id: int) -> int:
    return db.query(StoreFollower).filter_by(vendor_id=vendor_id).count()
