from __future__ import annotations

from sqlalchemy.orm import Session

from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.referrals.models import ReferralStatus, StoreReferral
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.service_utils import (
    create_for_vendor as create_vendor_record,
    delete_entity,
    get_by_id as get_record_by_id,
    get_by_vendor as get_vendor_record,
    list_by_vendor as list_vendor_records,
    update_entity,
)


def list_by_vendor(db: Session, vendor_id: int) -> list[StoreReferral]:
    return list_vendor_records(
        db,
        StoreReferral,
        vendor_id,
        order_by=(StoreReferral.created_at.desc(),),
    )


def list_by_referrer(db: Session, user_id: int) -> list[StoreReferral]:
    return db.query(StoreReferral).filter_by(referrer_user_id=user_id).all()


def get_by_id(db: Session, referral_id: int) -> StoreReferral | None:
    return get_record_by_id(db, StoreReferral, referral_id)


def get_by_vendor(db: Session, vendor_id: int, referral_id: int) -> StoreReferral | None:
    return get_vendor_record(db, StoreReferral, vendor_id, referral_id)


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
    return create_vendor_record(
        db,
        StoreReferral,
        vendor_id,
        referrer_user_id=referrer_user_id,
        referral_code=referral_code,
        reward_type=reward_type,
        reward_value=reward_value,
        status=status,
    )


def update_referral(db: Session, referral: StoreReferral, **updates) -> StoreReferral:
    return update_entity(db, referral, **updates)


def delete_referral(db: Session, referral: StoreReferral) -> None:
    delete_entity(db, referral)


def claim_referral(db: Session, referral: StoreReferral, referred_user_id: int) -> StoreReferral:
    referral.referred_user_id = referred_user_id
    referral.status = ReferralStatus.completed
    db.flush()
    db.refresh(referral)
    return referral
