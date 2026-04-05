from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, timedelta
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.analytics.models import (
    CustomerBehavior,
    PerformanceGoal,
    VendorAnalytics,
)
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.models import User
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.routes import require_any_role, get_current_user
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.vendors.models import VendorStore as Vendor
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import get_db
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.dependencies import assert_store_access, get_vendor_id_for_user
from typing import Optional

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _resolve_vendor_id(vendor_id: Optional[int], user, db: Session) -> int:
    """Superadmin must pass vendor_id; others resolve from their own account."""
    user_type = user.user_type.value if hasattr(user.user_type, "value") else str(user.user_type)
    if user_type == "superadmin":
        if vendor_id is None:
            raise HTTPException(status_code=400, detail="vendor_id requerido para superadmin")
        return vendor_id
    resolved = get_vendor_id_for_user(user, db)
    if vendor_id is not None and vendor_id != resolved:
        raise HTTPException(status_code=403, detail="No tienes acceso a esta tienda")
    return resolved


@router.get("/vendor/daily")
def get_vendor_daily_analytics(
    vendor_id: Optional[int] = None,
    days: int = 30,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin", "store_employee")),
):
    """Obtener métricas diarias del vendedor (últimos N días)"""
    vid = _resolve_vendor_id(vendor_id, user, db)
    assert_store_access(user, vid, db)
    today = date.today()
    start_date = today - timedelta(days=days - 1)
    analytics = db.query(VendorAnalytics).filter(
        VendorAnalytics.vendor_id == vid,
        VendorAnalytics.date >= start_date
    ).order_by(VendorAnalytics.date).all()
    return [
        {
            "date": a.date,
            "total_orders": a.total_orders,
            "total_revenue": float(a.total_revenue or 0),
            "total_commission": float(a.total_commission or 0),
            "net_earnings": float(a.net_earnings or 0),
            "products_sold": a.products_sold,
            "unique_customers": a.unique_customers,
            "average_order_value": float(a.average_order_value or 0),
            "store_views": a.store_views,
            "product_views": a.product_views,
            "conversion_rate": float(a.conversion_rate or 0),
            "low_stock_alerts": a.low_stock_alerts,
            "out_of_stock_products": a.out_of_stock_products,
            "average_rating": float(a.average_rating or 0),
            "total_reviews": a.total_reviews,
            "category_breakdown": a.category_breakdown,
            "top_products": a.top_products
        }
        for a in analytics
    ]

@router.get("/vendor/customer-behavior")
def get_vendor_customer_behavior(
    vendor_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin", "store_employee")),
):
    """Obtener métricas de comportamiento de clientes para un vendedor"""
    vid = _resolve_vendor_id(vendor_id, user, db)
    assert_store_access(user, vid, db)
    behaviors = db.query(CustomerBehavior).filter(
        CustomerBehavior.vendor_id == vid
    ).all()
    return [
        {
            "customer_id": b.customer_id,
            "total_orders": b.total_orders,
            "total_spent": float(b.total_spent or 0),
            "first_order_date": b.first_order_date,
            "last_order_date": b.last_order_date,
            "average_days_between_orders": float(b.average_days_between_orders or 0),
            "favorite_categories": b.favorite_categories,
            "purchased_products": b.purchased_products,
            "predicted_lifetime_value": float(b.predicted_lifetime_value or 0),
            "churn_probability": float(b.churn_probability or 0)
        }
        for b in behaviors
    ]

@router.get("/vendor/goals")
def get_vendor_performance_goals(
    vendor_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin", "store_employee")),
):
    """Obtener metas de desempeño del vendedor"""
    vid = _resolve_vendor_id(vendor_id, user, db)
    assert_store_access(user, vid, db)
    goals = db.query(PerformanceGoal).filter(
        PerformanceGoal.vendor_id == vid
    ).order_by(PerformanceGoal.created_at.desc()).all()
    return [
        {
            "id": g.id,
            "goal_type": g.goal_type,
            "period_type": g.period_type,
            "target_value": float(g.target_value or 0),
            "current_value": float(g.current_value or 0),
            "start_date": g.start_date,
            "end_date": g.end_date,
            "is_completed": g.is_completed,
            "completion_date": g.completion_date,
            "progress": float(g.current_value or 0) / float(g.target_value or 1) * 100
        }
        for g in goals
    ]



