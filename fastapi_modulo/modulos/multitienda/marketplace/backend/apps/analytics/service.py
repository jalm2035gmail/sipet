from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.analytics.models import VendorAnalytics
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.coupons.models import StoreCoupon
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.employees.models import StoreEmployee
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.products.models import Product


def get_store_stats(db: Session, vendor_id: int) -> dict:
    def safe_orders_count() -> int:
        try:
            row = db.execute(
                text("SELECT COUNT(*) AS cnt FROM orders WHERE vendor_id = :vid"),
                {"vid": vendor_id},
            ).mappings().first()
            return int((row or {}).get("cnt", 0))
        except Exception:
            return 0

    products = db.query(Product).filter_by(vendor_id=vendor_id).count()
    employees = db.query(StoreEmployee).filter_by(vendor_id=vendor_id).count()
    coupons = db.query(StoreCoupon).filter_by(vendor_id=vendor_id, is_active=True).count()
    orders = safe_orders_count()

    today = date.today()
    chart_labels: list[str] = []
    chart_values: list[int] = []
    for i in range(6, -1, -1):
        current_date = today - timedelta(days=i)
        chart_labels.append(current_date.strftime("%d/%m"))
        row = (
            db.query(VendorAnalytics)
            .filter_by(vendor_id=vendor_id, date=current_date)
            .first()
        )
        chart_values.append(int(row.store_views or 0) if row else 0)

    return {
        "products": products,
        "employees": employees,
        "coupons": coupons,
        "orders": orders,
        "chart_labels": chart_labels,
        "chart_values": chart_values,
    }
