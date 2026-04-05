from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.routes import require_role
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.videos import schemas, service
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import get_db
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.dependencies import get_vendor_store as _get_vendor_store

router = APIRouter(prefix="/videos", tags=["videos"])


@router.get("/store/{vendor_id}", response_model=List[schemas.StoreVideoRead])
def list_videos(vendor_id: int, db: Session = Depends(get_db)):
    _get_vendor_store(vendor_id, db)
    return service.list_by_vendor(db, vendor_id, active_only=True)


@router.post("/store/{vendor_id}", response_model=schemas.StoreVideoRead, status_code=201)
def create_video(
    vendor_id: int,
    data: schemas.StoreVideoCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role("vendor")),
):
    _get_vendor_store(vendor_id, db)
    video = service.create_for_vendor(db, vendor_id, **data.dict())
    db.commit()
    return video


@router.put("/{video_id}", response_model=schemas.StoreVideoRead)
def update_video(
    video_id: int,
    data: schemas.StoreVideoUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role("vendor")),
):
    video = service.get_by_id(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video no encontrado")
    video = service.update_video(db, video, **data.dict(exclude_unset=True))
    db.commit()
    return video


@router.delete("/{video_id}", status_code=204)
def delete_video(
    video_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("vendor")),
):
    video = service.get_by_id(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video no encontrado")
    service.delete_video(db, video)
    db.commit()
