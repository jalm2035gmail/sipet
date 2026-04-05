from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, exists
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.commissions.models import (
    Payout,
    PayoutItem,
    VendorBalance,
    WithdrawalRequest,
)
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.orders.models import Order, OrderItem
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.models import User
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.routes import require_any_role, get_current_user
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.vendors.models import VendorStore as Vendor
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import get_db
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.dependencies import get_current_vendor

router = APIRouter(prefix="/api/commissions", tags=["commissions"])


@router.get("/vendor/balance")
async def get_vendor_balance(
    db: Session = Depends(get_db),
    current_vendor: Vendor = Depends(get_current_vendor),
):
    """Obtener balance actual del vendedor"""
    last_transaction = db.query(VendorBalance).filter(
        VendorBalance.vendor_id == current_vendor.id
    ).order_by(VendorBalance.created_at.desc()).first()
    current_balance = last_transaction.balance_after if last_transaction else Decimal('0.00')
    pending_orders = db.query(OrderItem).filter(
        OrderItem.vendor_id == current_vendor.id,
        OrderItem.order.has(status='completed'),
        ~OrderItem.order.has(payment_status='refunded'),
        ~exists().where(and_(
            PayoutItem.order_item_id == OrderItem.id,
            PayoutItem.payout.has(status='paid')
        ))
    ).all()
    pending_amount = sum(item.vendor_amount for item in pending_orders)
    next_payout = db.query(Payout).filter(
        Payout.vendor_id == current_vendor.id,
        Payout.status == 'pending'
    ).order_by(Payout.payout_period_start).first()
    recent_transactions = db.query(VendorBalance).filter(
        VendorBalance.vendor_id == current_vendor.id
    ).order_by(VendorBalance.created_at.desc()).limit(10).all()
    return {
        "current_balance": float(current_balance),
        "available_balance": float(current_balance),
        "pending_balance": float(pending_amount),
        "next_payout": {
            "amount": float(next_payout.net_amount) if next_payout else 0,
            "date": next_payout.payout_date if next_payout else None,
            "reference": next_payout.reference_number if next_payout else None
        } if next_payout else None,
        "recent_transactions": [
            {
                "id": t.id,
                "type": t.transaction_type,
                "amount": float(t.amount),
                "description": t.description,
                "date": t.created_at,
                "order_number": t.order.order_number if t.order else None
            }
            for t in recent_transactions
        ]
    }

# ... El resto de endpoints se implementan igual, adaptando dependencias y modelos ...
