from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.coupons.models import StoreCoupon
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.service_utils import (
    create_for_vendor as create_vendor_record,
    delete_entity,
    get_by_id as get_record_by_id,
    get_by_vendor as get_vendor_record,
    list_by_vendor as list_vendor_records,
    update_entity,
)


def list_by_vendor(db: Session, vendor_id: int) -> list[StoreCoupon]:
    return list_vendor_records(
        db,
        StoreCoupon,
        vendor_id,
        order_by=(StoreCoupon.created_at.desc(),),
    )


def get_by_id(db: Session, coupon_id: int) -> StoreCoupon | None:
    return get_record_by_id(db, StoreCoupon, coupon_id)


def get_by_vendor(db: Session, vendor_id: int, coupon_id: int) -> StoreCoupon | None:
    return get_vendor_record(db, StoreCoupon, vendor_id, coupon_id)


def get_by_vendor_code(db: Session, vendor_id: int, code: str) -> StoreCoupon | None:
    return db.query(StoreCoupon).filter_by(vendor_id=vendor_id, code=code).first()


def create_for_vendor(db: Session, vendor_id: int, **payload) -> StoreCoupon:
    return create_vendor_record(db, StoreCoupon, vendor_id, **payload)


def update_coupon(db: Session, coupon: StoreCoupon, **updates) -> StoreCoupon:
    return update_entity(db, coupon, **updates)


def delete_coupon(db: Session, coupon: StoreCoupon) -> None:
    delete_entity(db, coupon)


def validate_coupon_for_vendor(
    db: Session,
    vendor_id: int,
    code: str,
    *,
    cart_total: float = 0.0,
) -> dict:
    now = datetime.utcnow()
    coupon = (
        db.query(StoreCoupon)
        .filter_by(vendor_id=vendor_id, code=code.strip().upper(), is_active=True)
        .first()
    )
    if not coupon:
        return {"valid": False, "error": "Cupón inválido o inactivo."}
    if coupon.valid_from and coupon.valid_from > now:
        return {"valid": False, "error": "El cupón aún no es válido."}
    if coupon.valid_until and coupon.valid_until < now:
        return {"valid": False, "error": "El cupón ha expirado."}
    if coupon.max_uses is not None and int(coupon.uses_count or 0) >= int(coupon.max_uses):
        return {"valid": False, "error": "El cupón ha alcanzado su límite de usos."}

    min_order = float(coupon.min_order_amount or 0)
    if cart_total < min_order:
        return {"valid": False, "error": f"Compra mínima requerida: ${min_order:.2f}."}

    dtype = getattr(coupon.discount_type, "value", coupon.discount_type) or "percent"
    dval = float(coupon.discount_value or 0)
    if dtype in ("percent", "porcentaje", "percentage"):
        discount = round(cart_total * dval / 100, 2)
    elif dtype in ("fixed", "monto"):
        discount = round(min(dval, cart_total), 2)
    else:
        discount = 0.0

    return {
        "valid": True,
        "coupon_id": coupon.id,
        "code": coupon.code,
        "discount_type": dtype,
        "discount_value": dval,
        "discount_amount": discount,
        "free_shipping": dtype in ("free_shipping", "envio"),
    }


def redeem_for_vendor(db: Session, vendor_id: int, coupon_id: int) -> bool:
    coupon = get_by_vendor(db, vendor_id, coupon_id)
    if not coupon:
        return False
    coupon.uses_count = int(coupon.uses_count or 0) + 1
    db.flush()
    return True
