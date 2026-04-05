from __future__ import annotations

from sqlalchemy.orm import Session

from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.videos.models import StoreVideo
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.service_utils import (
    create_for_vendor as create_vendor_record,
    delete_entity,
    get_by_id as get_record_by_id,
    get_by_vendor as get_vendor_record,
    update_entity,
)


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
    return get_record_by_id(db, StoreVideo, video_id)


def get_by_vendor(db: Session, vendor_id: int, video_id: int) -> StoreVideo | None:
    return get_vendor_record(db, StoreVideo, vendor_id, video_id)


def create_for_vendor(db: Session, vendor_id: int, **payload) -> StoreVideo:
    return create_vendor_record(db, StoreVideo, vendor_id, **payload)


def update_video(db: Session, video: StoreVideo, **updates) -> StoreVideo:
    return update_entity(db, video, **updates)


def delete_video(db: Session, video: StoreVideo) -> None:
    delete_entity(db, video)
