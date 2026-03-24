from __future__ import annotations

import os
import re
from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.orders.routes import (
    router as orders_router,
)
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.payments.routes import (
    router as payments_router,
)
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.products.routes import (
    router as products_router,
)
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.models import User
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.routes import (
    router as users_router,
)
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.vendors.models import (
    VendorStatus,
    VendorStore,
)
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.vendors.routes import (
    router as vendors_router,
)
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import SessionLocal

# Registrar modelos relacionados para resolver relationships SQLAlchemy.
import fastapi_modulo.modulos.multitienda.marketplace.backend.apps.analytics.models  # noqa: F401
import fastapi_modulo.modulos.multitienda.marketplace.backend.apps.commissions.models  # noqa: F401


BACKEND_ROOT_PATH = os.getenv("BACKEND_ROOT_PATH", "")
BACKEND_ROUTE_PREFIX = os.getenv("BACKEND_ROUTE_PREFIX", "").rstrip("/")
if BACKEND_ROUTE_PREFIX and not BACKEND_ROUTE_PREFIX.startswith("/"):
    BACKEND_ROUTE_PREFIX = f"/{BACKEND_ROUTE_PREFIX}"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = PROJECT_ROOT / "static"

marketplace_router = APIRouter()


def _slugify_store_name(value: str) -> str:
    raw = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")
    return raw or "tienda"


@marketplace_router.post(f"{BACKEND_ROUTE_PREFIX}/admin/store-settings")
async def save_store_settings(request: Request):
    payload = await request.json()
    store_name = str(payload.get("store_name") or "").strip()
    admin_id_raw = str(payload.get("admin_user_id") or "").strip()
    if not store_name:
        raise HTTPException(status_code=422, detail="Store name is required")
    if not admin_id_raw:
        raise HTTPException(status_code=422, detail="Admin user is required")
    try:
        admin_user_id = int(admin_id_raw)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Admin user is invalid") from exc

    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.id == admin_user_id).first()
        if not admin_user:
            raise HTTPException(status_code=404, detail="Admin user not found")

        store = db.query(VendorStore).filter(VendorStore.vendor_id == admin_user_id).first()
        theme = dict(store.store_theme or {}) if store and isinstance(store.store_theme, dict) else {}
        theme.update(
            {
                "store_type": str(payload.get("store_type") or "").strip(),
                "membership": str(payload.get("membership") or "").strip(),
                "inventory_enabled": bool(payload.get("inventory_enabled", False)),
                "validity": str(payload.get("validity") or "").strip(),
                "referrals": str(payload.get("referrals") or "").strip(),
                "appointments": str(payload.get("appointments") or "").strip(),
                "coupons": str(payload.get("coupons") or "").strip(),
                "whatsapp": str(payload.get("whatsapp") or "").strip(),
                "max_internal_users": max(0, int(payload.get("max_internal_users") or 0)),
                "max_portal_users": max(0, int(payload.get("max_portal_users") or 0)),
            }
        )

        if store is None:
            base_slug = _slugify_store_name(store_name)
            slug = base_slug
            suffix = 2
            while db.query(VendorStore).filter(VendorStore.store_slug == slug).first():
                slug = f"{base_slug}-{suffix}"
                suffix += 1
            store = VendorStore(
                vendor_id=admin_user_id,
                store_name=store_name,
                store_slug=slug,
                store_theme=theme,
                is_featured=bool(payload.get("is_featured", False)),
                status=VendorStatus.approved if bool(payload.get("is_active", True)) else VendorStatus.pending,
                is_active=bool(payload.get("is_active", True)),
            )
            db.add(store)
        else:
            store.store_name = store_name
            store.store_theme = theme
            store.is_featured = bool(payload.get("is_featured", False))
            store.is_active = bool(payload.get("is_active", True))
            store.status = VendorStatus.approved if store.is_active else VendorStatus.pending

        db.commit()
        db.refresh(store)
        return JSONResponse(
            {
                "id": store.id,
                "store_name": store.store_name,
                "vendor_id": store.vendor_id,
                "max_internal_users": theme.get("max_internal_users", 0),
                "max_portal_users": theme.get("max_portal_users", 0),
            },
            status_code=201,
        )
    finally:
        db.close()


@marketplace_router.get(f"{BACKEND_ROUTE_PREFIX}/health")
def health():
    return {"status": "ok", "prefix": BACKEND_ROUTE_PREFIX or "/"}


def build_marketplace_backend_app() -> FastAPI:
    app = FastAPI(title="MultiTiendApp API", root_path=BACKEND_ROOT_PATH)

    if STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    app.include_router(marketplace_router)
    app.include_router(users_router, prefix=f"{BACKEND_ROUTE_PREFIX}/users", tags=["users"])
    app.include_router(vendors_router, prefix=f"{BACKEND_ROUTE_PREFIX}/vendors", tags=["vendors"])
    app.include_router(products_router, prefix=f"{BACKEND_ROUTE_PREFIX}/products", tags=["products"])
    app.include_router(orders_router, prefix=f"{BACKEND_ROUTE_PREFIX}/orders", tags=["orders"])
    app.include_router(payments_router, prefix=f"{BACKEND_ROUTE_PREFIX}/payments", tags=["payments"])

    try:
        from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.reviews.api import (
            router as reviews_api_router,
        )

        app.include_router(reviews_api_router, prefix=BACKEND_ROUTE_PREFIX)
    except Exception as exc:
        print(f"[startup] reviews router disabled: {exc}")

    return app


__all__ = ["BACKEND_ROUTE_PREFIX", "build_marketplace_backend_app", "marketplace_router"]
