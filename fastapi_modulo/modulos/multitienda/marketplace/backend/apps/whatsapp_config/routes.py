from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.routes import require_role
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.whatsapp_config import models, schemas
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import get_db
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.dependencies import get_vendor_store as _get_vendor_store

router = APIRouter(prefix="/whatsapp-config", tags=["whatsapp_config"])


@router.get("/store/{vendor_id}", response_model=schemas.StoreWhatsappConfigRead)
def get_whatsapp_config(
    vendor_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("vendor")),
):
    _get_vendor_store(vendor_id, db)
    cfg = db.query(models.StoreWhatsappConfig).filter_by(vendor_id=vendor_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="Sin configuración de WhatsApp")
    return cfg


@router.post("/store/{vendor_id}", response_model=schemas.StoreWhatsappConfigRead, status_code=201)
def create_whatsapp_config(
    vendor_id: int,
    data: schemas.StoreWhatsappConfigCreate,
    db: Session = Depends(get_db),
    user=Depends(require_role("vendor")),
):
    _get_vendor_store(vendor_id, db)
    if db.query(models.StoreWhatsappConfig).filter_by(vendor_id=vendor_id).first():
        raise HTTPException(status_code=409, detail="Ya existe una configuración de WhatsApp para esta tienda")
    cfg = models.StoreWhatsappConfig(vendor_id=vendor_id, **data.dict())
    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    return cfg


@router.put("/store/{vendor_id}", response_model=schemas.StoreWhatsappConfigRead)
def update_whatsapp_config(
    vendor_id: int,
    data: schemas.StoreWhatsappConfigUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_role("vendor")),
):
    cfg = db.query(models.StoreWhatsappConfig).filter_by(vendor_id=vendor_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="Sin configuración de WhatsApp")
    for field, value in data.dict(exclude_unset=True).items():
        setattr(cfg, field, value)
    db.commit()
    db.refresh(cfg)
    return cfg


@router.delete("/store/{vendor_id}", status_code=204)
def delete_whatsapp_config(
    vendor_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("vendor")),
):
    cfg = db.query(models.StoreWhatsappConfig).filter_by(vendor_id=vendor_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="Sin configuración de WhatsApp")
    db.delete(cfg)
    db.commit()
