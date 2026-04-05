from __future__ import annotations

from sqlalchemy.orm import Session

from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.referrals.models import ReferralStatus, StoreReferral


def list_by_vendor(db: Session, vendor_id: int) -> list[StoreReferral]:
    return (
        db.query(StoreReferral)
        .filter_by(vendor_id=vendor_id)
        .order_by(StoreReferral.created_at.desc())
        .all()
    )


def list_by_referrer(db: Session, user_id: int) -> list[StoreReferral]:
    return db.query(StoreReferral).filter_by(referrer_user_id=user_id).all()


def get_by_id(db: Session, referral_id: int) -> StoreReferral | None:
    return db.query(StoreReferral).filter_by(id=referral_id).first()


def get_by_vendor(db: Session, vendor_id: int, referral_id: int) -> StoreReferral | None:
    return db.query(StoreReferral).filter_by(id=referral_id, vendor_id=vendor_id).first()


def get_by_code(db: Session, referral_code: str) -> StoreReferral | None:
    return db.query(StoreReferral).filter_by(referral_code=referral_code).first()


def create_for_vendor(
    db: Session,
    vendor_id: int,
    *,
    referrer_user_id: int,
    referral_code: str,
    reward_type=None,
    reward_value=None,
    status=ReferralStatus.pending,
) -> StoreReferral:
    referral = StoreReferral(
        vendor_id=vendor_id,
        referrer_user_id=referrer_user_id,
        referral_code=referral_code,
        reward_type=reward_type,
        reward_value=reward_value,
        status=status,
    )
    db.add(referral)
    db.flush()
    db.refresh(referral)
    return referral


def update_referral(db: Session, referral: StoreReferral, **updates) -> StoreReferral:
    for field, value in updates.items():
        setattr(referral, field, value)
    db.flush()
    db.refresh(referral)
    return referral


def delete_referral(db: Session, referral: StoreReferral) -> None:
    db.delete(referral)
    db.flush()


def claim_referral(db: Session, referral: StoreReferral, referred_user_id: int) -> StoreReferral:
    referral.referred_user_id = referred_user_id
    referral.status = ReferralStatus.completed
    db.flush()
    db.refresh(referral)
    return referral
