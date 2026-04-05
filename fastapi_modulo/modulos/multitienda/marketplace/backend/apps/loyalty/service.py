from __future__ import annotations

from sqlalchemy.orm import Session

from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.loyalty.models import (
    LoyaltyAccount,
    LoyaltyPlan,
    LoyaltyTransaction,
)


def get_plan(db: Session, vendor_id: int) -> LoyaltyPlan | None:
    return db.query(LoyaltyPlan).filter_by(vendor_id=vendor_id).first()


def upsert_plan(
    db: Session,
    vendor_id: int,
    *,
    name: str,
    points_per_peso: float,
    min_redeem_points: int,
    redeem_rate: float,
    is_active: bool,
    description: str,
) -> LoyaltyPlan:
    plan = get_plan(db, vendor_id)
    if plan is None:
        plan = LoyaltyPlan(vendor_id=vendor_id)
        db.add(plan)
    plan.name = name
    plan.points_per_peso = points_per_peso
    plan.min_redeem_points = min_redeem_points
    plan.redeem_rate = redeem_rate
    plan.is_active = is_active
    plan.description = description
    db.flush()
    db.refresh(plan)
    return plan


def list_customers(db: Session, vendor_id: int) -> list[LoyaltyAccount]:
    return (
        db.query(LoyaltyAccount)
        .filter_by(vendor_id=vendor_id)
        .order_by(LoyaltyAccount.current_points.desc())
        .all()
    )


def get_account_by_email(db: Session, vendor_id: int, email: str) -> LoyaltyAccount | None:
    return db.query(LoyaltyAccount).filter_by(vendor_id=vendor_id, customer_email=email).first()


def adjust_points(
    db: Session,
    vendor_id: int,
    *,
    email: str,
    points: int,
    tx_type: str = "adjusted",
    notes: str = "",
    reference: str = "",
    name: str = "",
) -> LoyaltyAccount:
    account = get_account_by_email(db, vendor_id, email)
    if account is None:
        init = max(0, points)
        account = LoyaltyAccount(
            vendor_id=vendor_id,
            customer_email=email,
            customer_name=name or "",
            current_points=init,
            lifetime_points=init,
        )
        db.add(account)
        db.flush()
    else:
        account.current_points = max(0, int(account.current_points or 0) + points)
        account.lifetime_points = int(account.lifetime_points or 0) + max(0, points)
        if name and not account.customer_name:
            account.customer_name = name
        db.flush()

    tx = LoyaltyTransaction(
        account_id=account.id,
        points=points,
        transaction_type=tx_type,
        reference=reference,
        notes=notes,
    )
    db.add(tx)
    db.flush()
    db.refresh(account)
    return account


def get_history(db: Session, vendor_id: int, email: str) -> list[LoyaltyTransaction]:
    account = get_account_by_email(db, vendor_id, email)
    if account is None:
        return []
    return (
        db.query(LoyaltyTransaction)
        .filter_by(account_id=account.id)
        .order_by(LoyaltyTransaction.id.desc())
        .limit(100)
        .all()
    )
