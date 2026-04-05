from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from fastapi_modulo.modulos.multitienda.marketplace.backend.core.dependencies import assert_store_access
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import get_db
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.routes import require_any_role
from .models import Order, OrderItem, ShippingGroup, Payment

router = APIRouter()


def _serialize_item(i: OrderItem) -> dict:
    return {
        "id":                 i.id,
        "product_id":         i.product_id,
        "variant_id":         i.variant_id,
        "product_name":       i.product_name,
        "product_sku":        i.product_sku,
        "price":              float(i.price),
        "quantity":           i.quantity,
        "total":              float(i.total),
        "item_status":        i.item_status,
        "platform_commission": float(i.platform_commission or 0),
        "vendor_amount":      float(i.vendor_amount or 0),
    }


def _serialize_order(o: Order, include_items: bool = False) -> dict:
    d = {
        "id":                   o.id,
        "order_number":          o.order_number,
        "uuid":                  o.uuid,
        "customer_id":           o.customer_id,
        "guest_email":           o.guest_email,
        "status":                o.status,
        "payment_status":        o.payment_status,
        "subtotal":              float(o.subtotal or 0),
        "tax_amount":            float(o.tax_amount or 0),
        "shipping_total":        float(o.shipping_total or 0),
        "discount_amount":       float(o.discount_amount or 0),
        "total":                 float(o.total or 0),
        "payment_method":        o.payment_method,
        "shipping_method":       o.shipping_method,
        "customer_note":         o.customer_note,
        "billing_address":       o.billing_address,
        "shipping_address":      o.shipping_address,
        "created_at":            o.created_at.isoformat() if o.created_at else None,
        "paid_at":               o.paid_at.isoformat() if o.paid_at else None,
        "completed_at":          o.completed_at.isoformat() if o.completed_at else None,
    }
    if include_items:
        d["items"] = [_serialize_item(i) for i in (o.items or [])]
    return d


def _assert_order_access(user, order: Order) -> None:
    user_type = user.user_type.value if hasattr(user.user_type, "value") else str(user.user_type)
    if user_type == "superadmin":
        return
    item_vendor_ids = {
        int(item.vendor_id)
        for item in (order.items or [])
        if getattr(item, "vendor_id", None) is not None
    }
    if not item_vendor_ids:
        raise HTTPException(status_code=403, detail="No tienes acceso a este pedido")
    if user_type == "vendor":
        allowed_vendor_id = int(user.vendor_profile_id or 0)
        if allowed_vendor_id and allowed_vendor_id in item_vendor_ids:
            return
        raise HTTPException(status_code=403, detail="No tienes acceso a este pedido")
    if user_type == "store_employee":
        allowed_vendor_id = int(user.vendor_profile_id or 0)
        if allowed_vendor_id and allowed_vendor_id in item_vendor_ids:
            return
        raise HTTPException(status_code=403, detail="No tienes acceso a este pedido")
    raise HTTPException(status_code=403, detail="No autorizado")


# ── List orders for a vendor ──────────────────────────────────────────────────

@router.get("/store/{vendor_id}")
def list_store_orders(
    vendor_id: int,
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin", "store_employee")),
):
    assert_store_access(user, vendor_id, db)
    query = (
        db.query(Order)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .filter(OrderItem.vendor_id == vendor_id)
        .options(joinedload(Order.items))
        .distinct()
    )
    if status:
        query = query.filter(Order.status == status)
    orders = query.order_by(Order.id.desc()).all()
    return {"success": True, "data": [_serialize_order(o, include_items=True) for o in orders]}


# ── Get single order ──────────────────────────────────────────────────────────

@router.get("/{order_id}")
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin", "store_employee")),
):
    o = (
        db.query(Order)
        .options(joinedload(Order.items), joinedload(Order.payments))
        .filter(Order.id == order_id)
        .first()
    )
    if not o:
        raise HTTPException(status_code=404, detail="Pedido no encontrado.")
    _assert_order_access(user, o)
    return {"success": True, "data": _serialize_order(o, include_items=True)}


# ── Update order status ───────────────────────────────────────────────────────

@router.patch("/{order_id}/status")
def patch_order_status(
    order_id: int,
    new_status: str = Query(..., description="Nuevo estado del pedido"),
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin", "store_employee")),
):
    o = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.id == order_id)
        .first()
    )
    if not o:
        raise HTTPException(status_code=404, detail="Pedido no encontrado.")
    _assert_order_access(user, o)
    valid = {"pending", "processing", "shipped", "delivered", "cancelled", "refunded"}
    if new_status not in valid:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Válidos: {', '.join(sorted(valid))}")
    o.status = new_status
    db.commit()
    db.refresh(o)
    return {"success": True, "data": _serialize_order(o)}
