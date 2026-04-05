from __future__ import annotations

from sqlalchemy.orm import Session

from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.videos.models import StoreVideo


def list_by_vendor(
    db: Session,
    vendor_id: int,
    *,
    active_only: bool = False,
) -> list[StoreVideo]:
    query = db.query(StoreVideo).filter_by(vendor_id=vendor_id)
    if active_only:
        query = query.filter_by(is_active=True)
    return query.order_by(StoreVideo.order.asc(), StoreVideo.created_at.desc()).all()


def get_by_id(db: Session, video_id: int) -> StoreVideo | None:
    return db.query(StoreVideo).filter_by(id=video_id).first()


def get_by_vendor(db: Session, vendor_id: int, video_id: int) -> StoreVideo | None:
    return db.query(StoreVideo).filter_by(id=video_id, vendor_id=vendor_id).first()


def create_for_vendor(db: Session, vendor_id: int, **payload) -> StoreVideo:
    video = StoreVideo(vendor_id=vendor_id, **payload)
    db.add(video)
    db.flush()
    db.refresh(video)
    return video


def update_video(db: Session, video: StoreVideo, **updates) -> StoreVideo:
    for field, value in updates.items():
        setattr(video, field, value)
    db.flush()
    db.refresh(video)
    return video


def delete_video(db: Session, video: StoreVideo) -> None:
    db.delete(video)
    db.flush()
