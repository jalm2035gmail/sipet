from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache
import logging
from time import monotonic

from sqlalchemy import text
from sqlalchemy.orm import Session

from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.analytics.models import VendorAnalytics
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.coupons.models import StoreCoupon
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.employees.models import StoreEmployee
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.products.models import Product
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import SessionLocal

_log = logging.getLogger("multitienda.analytics")
_STORE_STATS_TTL_SECONDS = 60
_STORE_STATS_CACHE_MAXSIZE = 2048


def _build_store_stats(db: Session, vendor_id: int) -> dict:
    def safe_orders_count() -> int:
        try:
            row = db.execute(
                text("SELECT COUNT(*) AS cnt FROM orders WHERE vendor_id = :vid"),
                {"vid": vendor_id},
            ).mappings().first()
            return int((row or {}).get("cnt", 0))
        except Exception:
            _log.exception("No se pudo consultar el conteo de ordenes para vendor_id=%s", vendor_id)
            return 0

    products = db.query(Product).filter_by(vendor_id=vendor_id).count()
    employees = db.query(StoreEmployee).filter_by(vendor_id=vendor_id).count()
    coupons = db.query(StoreCoupon).filter_by(vendor_id=vendor_id, is_active=True).count()
    orders = safe_orders_count()

    today = date.today()
    from_date = today - timedelta(days=6)
    analytics_rows = (
        db.query(VendorAnalytics)
        .filter(
            VendorAnalytics.vendor_id == vendor_id,
            VendorAnalytics.date >= from_date,
            VendorAnalytics.date <= today,
        )
        .all()
    )
    views_by_date = {
        row.date: int(row.store_views or 0)
        for row in analytics_rows
        if getattr(row, "date", None) is not None
    }
    chart_labels: list[str] = []
    chart_values: list[int] = []
    for i in range(6, -1, -1):
        current_date = today - timedelta(days=i)
        chart_labels.append(current_date.strftime("%d/%m"))
        chart_values.append(views_by_date.get(current_date, 0))

    payload = {
        "products": products,
        "employees": employees,
        "coupons": coupons,
        "orders": orders,
        "chart_labels": chart_labels,
        "chart_values": chart_values,
    }
    return payload


@lru_cache(maxsize=_STORE_STATS_CACHE_MAXSIZE)
def _cached_store_stats(vendor_id: int, cache_bucket: int) -> dict:
    del cache_bucket
    db = SessionLocal()
    try:
        return _build_store_stats(db, vendor_id)
    finally:
        db.close()


def get_cached_store_stats(db: Session, vendor_id: int) -> dict:
    del db
    cache_bucket = int(monotonic() // _STORE_STATS_TTL_SECONDS)
    return dict(_cached_store_stats(vendor_id, cache_bucket))
