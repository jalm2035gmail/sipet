import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.routes import require_any_role
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.referrals import models, schemas
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import get_db
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.dependencies import assert_store_access, get_vendor_store as _get_vendor_store

router = APIRouter(prefix="/referrals", tags=["referrals"])


@router.get("/store/{vendor_id}", response_model=List[schemas.StoreReferralRead])
def list_referrals(
    vendor_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin")),
):
    _get_vendor_store(vendor_id, db)
    assert_store_access(user, vendor_id, db)
    return db.query(models.StoreReferral).filter_by(vendor_id=vendor_id).all()


@router.post("/store/{vendor_id}/generate", response_model=schemas.StoreReferralRead, status_code=201)
def generate_referral(
    vendor_id: int,
    data: schemas.StoreReferralCreate,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("customer", "vendor", "superadmin")),
):
    _get_vendor_store(vendor_id, db)
    code = data.referral_code or secrets.token_urlsafe(8).upper()
    if db.query(models.StoreReferral).filter_by(referral_code=code).first():
        raise HTTPException(status_code=409, detail="El código de referido ya existe")
    referral = models.StoreReferral(
        vendor_id=vendor_id,
        referrer_user_id=user.id,
        referral_code=code,
        reward_type=data.reward_type,
        reward_value=data.reward_value,
    )
    db.add(referral)
    db.commit()
    db.refresh(referral)
    return referral


@router.post("/claim/{referral_code}")
def claim_referral(
    referral_code: str,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("customer", "vendor", "superadmin")),
):
    referral = db.query(models.StoreReferral).filter_by(referral_code=referral_code).first()
    if not referral:
        raise HTTPException(status_code=404, detail="Código de referido no encontrado")
    if referral.status != models.ReferralStatus.pending:
        raise HTTPException(status_code=400, detail="Este código ya fue utilizado")
    if referral.referrer_user_id == user.id:
        raise HTTPException(status_code=400, detail="No puedes usar tu propio código de referido")
    referral.referred_user_id = user.id
    referral.status = models.ReferralStatus.completed
    db.commit()
    return {"success": True, "message": "Referido registrado correctamente"}


@router.get("/my", response_model=List[schemas.StoreReferralRead])
def my_referrals(
    db: Session = Depends(get_db),
    user=Depends(require_any_role("customer", "vendor", "superadmin")),
):
    return db.query(models.StoreReferral).filter_by(referrer_user_id=user.id).all()
