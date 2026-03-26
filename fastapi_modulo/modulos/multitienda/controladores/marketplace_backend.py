from __future__ import annotations

import os
import re
from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, Text, func, insert, select, text
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import SessionLocal


BACKEND_ROOT_PATH = os.getenv("BACKEND_ROOT_PATH", "")
BACKEND_ROUTE_PREFIX = os.getenv("BACKEND_ROUTE_PREFIX", "").rstrip("/")
if BACKEND_ROUTE_PREFIX and not BACKEND_ROUTE_PREFIX.startswith("/"):
    BACKEND_ROUTE_PREFIX = f"/{BACKEND_ROUTE_PREFIX}"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = PROJECT_ROOT / "static"

marketplace_router = APIRouter()
_business_type_metadata = MetaData()
store_business_types = Table(
    "store_business_types",
    _business_type_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(160), nullable=False),
    Column("code", String(40), nullable=False, unique=True, index=True),
    Column("description", Text, nullable=False, default=""),
    Column("created_at", DateTime, nullable=False, server_default=func.now()),
)


def _ensure_business_types_schema(bind) -> None:
    _business_type_metadata.create_all(bind=bind, tables=[store_business_types], checkfirst=True)


def _default_business_types() -> list[dict[str, str]]:
    return [
        {"name": "Restaurante", "code": "REST", "description": "Negocios de alimentos y bebidas."},
        {"name": "Moda", "code": "MODA", "description": "Ropa, calzado y accesorios."},
        {"name": "Ferretería", "code": "FERR", "description": "Herramientas y materiales para construcción."},
    ]


def _list_business_types(db) -> list[dict[str, str]]:
    _ensure_business_types_schema(db.bind)
    rows = db.execute(
        select(
            store_business_types.c.id,
            store_business_types.c.name,
            store_business_types.c.code,
            store_business_types.c.description,
        ).order_by(store_business_types.c.name.asc())
    ).mappings().all()
    if rows:
        return [dict(row) for row in rows]
    defaults = _default_business_types()
    db.execute(insert(store_business_types), defaults)
    db.commit()
    seeded = db.execute(
        select(
            store_business_types.c.id,
            store_business_types.c.name,
            store_business_types.c.code,
            store_business_types.c.description,
        ).order_by(store_business_types.c.name.asc())
    ).mappings().all()
    return [dict(row) for row in seeded]


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
        admin_user = db.execute(
            text("SELECT id FROM users WHERE id = :admin_user_id LIMIT 1"),
            {"admin_user_id": admin_user_id},
        ).first()
        if not admin_user:
            raise HTTPException(status_code=404, detail="Admin user not found")

        store = db.execute(
            text(
                """
                SELECT id, vendor_id, store_name, store_slug, store_theme, is_featured, is_active
                FROM vendors
                WHERE vendor_id = :admin_user_id
                LIMIT 1
                """
            ),
            {"admin_user_id": admin_user_id},
        ).mappings().first()
        theme = dict(store["store_theme"] or {}) if store and isinstance(store["store_theme"], dict) else {}
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
            while db.execute(
                text("SELECT 1 FROM vendors WHERE store_slug = :slug LIMIT 1"),
                {"slug": slug},
            ).first():
                slug = f"{base_slug}-{suffix}"
                suffix += 1
            created = db.execute(
                text(
                    """
                    INSERT INTO vendors (
                        vendor_id, store_name, store_slug, store_theme, is_featured, status, is_active
                    ) VALUES (
                        :vendor_id, :store_name, :store_slug, :store_theme, :is_featured, :status, :is_active
                    )
                    RETURNING id, vendor_id, store_name
                    """
                ),
                {
                    "vendor_id": admin_user_id,
                    "store_name": store_name,
                    "store_slug": slug,
                    "store_theme": theme,
                    "is_featured": bool(payload.get("is_featured", False)),
                    "status": "approved" if bool(payload.get("is_active", True)) else "pending",
                    "is_active": bool(payload.get("is_active", True)),
                },
            ).mappings().first()
        else:
            db.execute(
                text(
                    """
                    UPDATE vendors
                    SET store_name = :store_name,
                        store_theme = :store_theme,
                        is_featured = :is_featured,
                        is_active = :is_active,
                        status = :status
                    WHERE id = :id
                    """
                ),
                {
                    "id": store["id"],
                    "store_name": store_name,
                    "store_theme": theme,
                    "is_featured": bool(payload.get("is_featured", False)),
                    "is_active": bool(payload.get("is_active", True)),
                    "status": "approved" if bool(payload.get("is_active", True)) else "pending",
                },
            )
            created = db.execute(
                text("SELECT id, vendor_id, store_name FROM vendors WHERE id = :id"),
                {"id": store["id"]},
            ).mappings().first()

        db.commit()
        return JSONResponse(
            {
                "id": created["id"],
                "store_name": created["store_name"],
                "vendor_id": created["vendor_id"],
                "max_internal_users": theme.get("max_internal_users", 0),
                "max_portal_users": theme.get("max_portal_users", 0),
            },
            status_code=201,
        )
    finally:
        db.close()


@marketplace_router.get(f"{BACKEND_ROUTE_PREFIX}/admin/business-types")
def list_business_types():
    db = SessionLocal()
    try:
        return _list_business_types(db)
    finally:
        db.close()


@marketplace_router.post(f"{BACKEND_ROUTE_PREFIX}/admin/business-types")
async def create_business_type(request: Request):
    payload = await request.json()
    name = str(payload.get("name") or "").strip()
    code = str(payload.get("code") or "").strip().upper()
    description = str(payload.get("description") or "").strip()
    if not name or not code or not description:
        raise HTTPException(status_code=422, detail="Completa Giro de negocio, Código y Descripción.")

    db = SessionLocal()
    try:
        _ensure_business_types_schema(db.bind)
        existing = db.execute(
            select(store_business_types.c.id).where(
                (store_business_types.c.code == code) | (store_business_types.c.name == name)
            )
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Ese giro o código ya existe.")

        db.execute(
            insert(store_business_types).values(
                name=name,
                code=code,
                description=description,
            )
        )
        db.commit()
        created = db.execute(
            select(
                store_business_types.c.id,
                store_business_types.c.name,
                store_business_types.c.code,
                store_business_types.c.description,
            ).where(store_business_types.c.code == code)
        ).mappings().first()
        return JSONResponse(dict(created), status_code=201)
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

    return app


__all__ = ["BACKEND_ROUTE_PREFIX", "build_marketplace_backend_app", "marketplace_router"]
