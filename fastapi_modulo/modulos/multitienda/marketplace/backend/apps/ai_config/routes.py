from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.routes import require_role
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.ai_config import models, schemas
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import get_db
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.dependencies import get_vendor_store as _get_vendor_store

router = APIRouter(prefix="/ai-config", tags=["ai_config"])


@router.get("/store/{vendor_id}", response_model=schemas.StoreAiConfigRead)
def get_ai_config(
    vendor_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("vendor")),
):
    _get_vendor_store(vendor_id, db)
    cfg = db.query(models.StoreAiConfig).filter_by(vendor_id=vendor_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="Sin configuración de IA")
    return cfg


@router.post("/store/{vendor_id}", response_model=schemas.StoreAiConfigRead, status_code=201)
def create_ai_config(
    vendor_id: int,
    data: schemas.StoreAiConfigCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role("vendor")),
):
    _get_vendor_store(vendor_id, db)
    if db.query(models.StoreAiConfig).filter_by(vendor_id=vendor_id).first():
        raise HTTPException(status_code=409, detail="Ya existe una configuración de IA para esta tienda")
    cfg = models.StoreAiConfig(vendor_id=vendor_id, **data.dict())
    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    return cfg


@router.put("/store/{vendor_id}", response_model=schemas.StoreAiConfigRead)
def update_ai_config(
    vendor_id: int,
    data: schemas.StoreAiConfigUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role("vendor")),
):
    cfg = db.query(models.StoreAiConfig).filter_by(vendor_id=vendor_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="Sin configuración de IA")
    for field, value in data.dict(exclude_unset=True).items():
        setattr(cfg, field, value)
    db.commit()
    db.refresh(cfg)
    return cfg


@router.delete("/store/{vendor_id}", status_code=204)
def delete_ai_config(
    vendor_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("vendor")),
):
    cfg = db.query(models.StoreAiConfig).filter_by(vendor_id=vendor_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="Sin configuración de IA")
    db.delete(cfg)
    db.commit()
