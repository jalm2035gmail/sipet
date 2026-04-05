from __future__ import annotations

import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.products.models import ProductImage
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.vendors.models import VendorStore
from fastapi_modulo.modulos.multitienda.servicios.data_utils import (
    coerce_value as _coerce,
    orm_list as _orm_list,
)


def _rows(db: Session, sql: str, params=None) -> list:
    result = db.execute(text(sql), params or {})
    keys = result.keys()
    return [{k: _coerce(v) for k, v in dict(zip(keys, row)).items()} for row in result.fetchall()]


def _decode_theme(raw_value) -> dict:
    current = raw_value
    for _ in range(3):
        if isinstance(current, dict):
            return current
        if not isinstance(current, str):
            return {}
        try:
            current = json.loads(current)
        except Exception:
            return {}
    return {}


def list_public_catalog(db: Session, store_id: int | None = None, *, featured_only: bool = False) -> list:
    vendor_query = db.query(VendorStore).filter_by(is_active=True)
    if store_id is not None:
        vendor_query = vendor_query.filter(VendorStore.id == store_id)
    elif featured_only:
        vendor_query = vendor_query.filter(VendorStore.is_featured.is_(True))

    vendor_rows = _orm_list(vendor_query.order_by(VendorStore.id.desc()))
    themed_products = []
    themed_seen: set[tuple] = set()
    for vendor in vendor_rows:
        theme = _decode_theme(vendor.get("store_theme"))
        catalog_products = theme.get("catalog_products")
        if not isinstance(catalog_products, list):
            continue
        for item in catalog_products:
            if not isinstance(item, dict):
                continue
            is_public = bool(item.get("publicado")) or bool(item.get("ecomPublicado"))
            if not is_public:
                continue
            nombre = str(item.get("nombre") or "").strip()
            if not nombre:
                continue
            themed_dedup_key = (vendor["id"], nombre.lower())
            if themed_dedup_key in themed_seen:
                continue
            themed_seen.add(themed_dedup_key)
            raw_img = str(item.get("imagen") or "").strip()
            if raw_img.startswith(("http://localhost", "http://127.", "http://0.0.0.0")):
                raw_img = ""
            themed_products.append({
                "id": item.get("db_product_id") or item.get("_id") or item.get("id"),
                "vendor_id": vendor["id"],
                "nombre": nombre,
                "precio": float(item.get("precio") or 0),
                "imagen": raw_img,
                "galleryImages": [img for img in (item.get("galleryImages") or []) if isinstance(img, str) and img],
                "categoria": item.get("categoria") or "",
                "slug": item.get("slug") or "",
                "store_slug": str(vendor.get("store_slug") or "").strip().lower(),
                "descCorta": item.get("descCorta") or "",
                "descLarga": item.get("descLarga") or item.get("descripcion") or "",
                "mostrarDetalles": item.get("mostrarDetalles") is not False,
                "detallesHtml": item.get("detallesHtml") or "",
                "mostrarEspecificaciones": item.get("mostrarEspecificaciones") is not False,
                "especificacionesHtml": item.get("especificacionesHtml") or "",
                "mostrarCondiciones": item.get("mostrarCondiciones") is not False,
                "condicionesHtml": item.get("condicionesHtml") or "",
                "tienda": vendor.get("store_name") or "",
                "publicado": True,
                "nuevo": bool(item.get("nuevo")),
            })

    ids_sin_imagen = [
        int(item["id"]) for item in themed_products
        if not item["imagen"] and isinstance(item["id"], int)
    ]
    if ids_sin_imagen:
        img_rows = _orm_list(
            db.query(ProductImage)
            .filter(
                ProductImage.is_primary.is_(True),
                ProductImage.product_id.in_(ids_sin_imagen),
            )
        )
        img_map = {int(row["product_id"]): str(row["image"] or "") for row in img_rows}
        for item in themed_products:
            if not item["imagen"] and isinstance(item["id"], int) and item["id"] in img_map:
                item["imagen"] = img_map[item["id"]]

    db_params: dict = {}
    try:
        sql = (
            "SELECT p.id, p.vendor_id, p.name, p.description, p.price, "
            "p.stock_quantity, p.slug, p.is_active, p.status, p.created_at, "
            "c.name AS category_name, "
            "pi.image AS primary_image, "
            "v.store_name AS store_name, "
            "v.store_slug AS store_slug "
            "FROM products p "
            "LEFT JOIN categories c ON c.id = ("
            "  SELECT id FROM categories WHERE id IN ("
            "    SELECT category_id FROM product_category WHERE product_id = p.id LIMIT 1"
            "  ) LIMIT 1"
            ") "
            "LEFT JOIN product_images pi ON pi.product_id = p.id AND pi.is_primary = 1 "
            "LEFT JOIN vendors v ON v.id = p.vendor_id "
            "WHERE p.status = 'published' AND p.is_active = 1"
        )
        if store_id is not None:
            sql += " AND p.vendor_id = :vid"
            db_params["vid"] = store_id
        elif featured_only:
            sql += " AND v.is_featured = 1"
        sql += " ORDER BY p.id DESC"
        rows = _rows(db, sql, db_params)
        use_category = True
    except Exception:
        sql = (
            "SELECT p.id, p.vendor_id, p.name, p.description, p.price, "
            "p.stock_quantity, p.slug, p.is_active, p.status, "
            "pi.image AS primary_image, "
            "v.store_name AS store_name, "
            "v.store_slug AS store_slug "
            "FROM products p "
            "LEFT JOIN product_images pi ON pi.product_id = p.id AND pi.is_primary = 1 "
            "LEFT JOIN vendors v ON v.id = p.vendor_id "
            "WHERE p.status = 'published' AND p.is_active = 1"
        )
        if store_id is not None:
            sql += " AND p.vendor_id = :vid"
            db_params["vid"] = store_id
        elif featured_only:
            sql += " AND v.is_featured = 1"
        sql += " ORDER BY p.id DESC"
        rows = _rows(db, sql, db_params)
        use_category = False

    result = []
    for row in rows:
        result.append({
            "id": row["id"],
            "vendor_id": row["vendor_id"],
            "nombre": row["name"] or "",
            "precio": float(row["price"] or 0),
            "imagen": row["primary_image"] or "",
            "galleryImages": [],
            "categoria": (row.get("category_name") or "") if use_category else "",
            "slug": row["slug"] or "",
            "store_slug": str(row.get("store_slug") or "").strip().lower(),
            "descCorta": row["description"] or "",
            "descLarga": row["description"] or "",
            "mostrarDetalles": False,
            "detallesHtml": "",
            "mostrarEspecificaciones": False,
            "especificacionesHtml": "",
            "mostrarCondiciones": False,
            "condicionesHtml": "",
            "tienda": row["store_name"] or "",
            "publicado": True,
            "nuevo": False,
        })

    merged = []
    seen_slug: set = set()
    seen_nombre: set = set()
    for item in themed_products + result:
        item_vendor = str(item.get("vendor_id") or "").strip()
        item_nombre = str(item.get("nombre") or "").strip().lower()
        item_slug = str(item.get("slug") or "").strip().lower()
        slug_key = (item_vendor, item_slug) if item_slug else None
        nombre_key = (item_vendor, item_nombre) if item_nombre else None
        if (slug_key and slug_key in seen_slug) or (nombre_key and nombre_key in seen_nombre):
            continue
        if slug_key:
            seen_slug.add(slug_key)
        if nombre_key:
            seen_nombre.add(nombre_key)
        merged.append(item)
    return merged
