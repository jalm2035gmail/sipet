from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.routes import require_role
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.videos import models, schemas
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import get_db
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.dependencies import get_vendor_store as _get_vendor_store

router = APIRouter(prefix="/videos", tags=["videos"])


@router.get("/store/{vendor_id}", response_model=List[schemas.StoreVideoRead])
def list_videos(vendor_id: int, db: Session = Depends(get_db)):
    _get_vendor_store(vendor_id, db)
    return (
        db.query(models.StoreVideo)
        .filter_by(vendor_id=vendor_id, is_active=True)
        .order_by(models.StoreVideo.order.asc())
        .all()
    )


@router.post("/store/{vendor_id}", response_model=schemas.StoreVideoRead, status_code=201)
def create_video(
    vendor_id: int,
    data: schemas.StoreVideoCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role("vendor")),
):
    _get_vendor_store(vendor_id, db)
    video = models.StoreVideo(vendor_id=vendor_id, **data.dict())
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


@router.put("/{video_id}", response_model=schemas.StoreVideoRead)
def update_video(
    video_id: int,
    data: schemas.StoreVideoUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role("vendor")),
):
    video = db.query(models.StoreVideo).filter_by(id=video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video no encontrado")
    for field, value in data.dict(exclude_unset=True).items():
        setattr(video, field, value)
    db.commit()
    db.refresh(video)
    return video


@router.delete("/{video_id}", status_code=204)
def delete_video(
    video_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("vendor")),
):
    video = db.query(models.StoreVideo).filter_by(id=video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video no encontrado")
    db.delete(video)
    db.commit()
