from __future__ import annotations

from datetime import date, timedelta
import logging
from threading import Lock
from time import monotonic

from sqlalchemy import text
from sqlalchemy.orm import Session

from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.analytics.models import VendorAnalytics
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.coupons.models import StoreCoupon
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.employees.models import StoreEmployee
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.products.models import Product

_log = logging.getLogger("multitienda.analytics")
_STORE_STATS_TTL_SECONDS = 60
_STORE_STATS_CACHE: dict[int, tuple[float, dict]] = {}
_STORE_STATS_CACHE_LOCK = Lock()


def _get_cached_store_stats(vendor_id: int) -> dict | None:
    with _STORE_STATS_CACHE_LOCK:
        cached = _STORE_STATS_CACHE.get(vendor_id)
        if not cached:
            return None
        expires_at, payload = cached
        if expires_at <= monotonic():
            _STORE_STATS_CACHE.pop(vendor_id, None)
            return None
        return dict(payload)


def _set_cached_store_stats(vendor_id: int, payload: dict) -> dict:
    cached_payload = dict(payload)
    with _STORE_STATS_CACHE_LOCK:
        _STORE_STATS_CACHE[vendor_id] = (
            monotonic() + _STORE_STATS_TTL_SECONDS,
            cached_payload,
        )
    return dict(cached_payload)


def get_store_stats(db: Session, vendor_id: int) -> dict:
    cached = _get_cached_store_stats(vendor_id)
    if cached is not None:
        return cached

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

    payload = {
        "products": products,
        "employees": employees,
        "coupons": coupons,
        "orders": orders,
        "chart_labels": chart_labels,
        "chart_values": chart_values,
    }
    return _set_cached_store_stats(vendor_id, payload)
