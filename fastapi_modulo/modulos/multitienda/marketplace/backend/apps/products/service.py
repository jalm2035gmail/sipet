from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.products.models import Product
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.products.models import ProductImage
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.vendors.models import VendorStore
from fastapi_modulo.modulos.multitienda.servicios.store_tables_shared import orm_list, rows
from fastapi_modulo.modulos.multitienda.servicios.theme_utils import decode_theme

_log = logging.getLogger("multitienda.products")


def _filtered_vendor_rows(db: Session, store_id: int | None, featured_only: bool) -> list[dict]:
    vendor_query = db.query(VendorStore).filter_by(is_active=True)
    if store_id is not None:
        vendor_query = vendor_query.filter(VendorStore.id == store_id)
    elif featured_only:
        vendor_query = vendor_query.filter(VendorStore.is_featured.is_(True))
    return orm_list(vendor_query.order_by(VendorStore.id.desc()))


def _load_db_public_catalog(db: Session, store_id: int | None, featured_only: bool) -> list[dict]:
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
            "LEFT JOIN ("
            "  SELECT product_id, MIN(category_id) AS category_id "
            "  FROM product_category "
            "  GROUP BY product_id"
            ") pc ON pc.product_id = p.id "
            "LEFT JOIN categories c ON c.id = pc.category_id "
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
        sql_rows = rows(db, sql, db_params)
        use_category = True
    except Exception:
        _log.exception("Fallo la consulta enriquecida del catalogo publico; se usara la variante reducida.")
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
        sql_rows = rows(db, sql, db_params)
        use_category = False

    result = []
    for row in sql_rows:
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
    return result


def _load_theme_fallback_catalog(
    db: Session,
    vendor_rows: list[dict],
    seen_slug: set[tuple[str, str]],
    seen_nombre: set[tuple[str, str]],
) -> list[dict]:
    persisted_product_ids = {int(row[0]) for row in db.query(Product.id).all()}
    themed_products: list[dict] = []
    themed_seen: set[tuple[str, str]] = set()
    for vendor in vendor_rows:
        theme = decode_theme(vendor.get("store_theme"))
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
            vendor_key = str(vendor["id"])
            slug = str(item.get("slug") or "").strip().lower()
            nombre_key = nombre.lower()
            db_product_id = item.get("db_product_id")
            if isinstance(db_product_id, int) and db_product_id in persisted_product_ids:
                continue
            if slug and (vendor_key, slug) in seen_slug:
                continue
            if (vendor_key, nombre_key) in seen_nombre:
                continue
            dedup_key = (vendor_key, slug or nombre_key)
            if dedup_key in themed_seen:
                continue
            themed_seen.add(dedup_key)
            raw_img = str(item.get("imagen") or "").strip()
            if raw_img.startswith(("http://localhost", "http://127.", "http://0.0.0.0")):
                raw_img = ""
            themed_item = {
                "id": db_product_id or item.get("_id") or item.get("id"),
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
            }
            themed_products.append(themed_item)
            if slug:
                seen_slug.add((vendor_key, slug))
            seen_nombre.add((vendor_key, nombre_key))

    ids_sin_imagen = [
        int(item["id"]) for item in themed_products
        if not item["imagen"] and isinstance(item["id"], int)
    ]
    if ids_sin_imagen:
        img_rows = orm_list(
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
    return themed_products


def list_public_catalog(db: Session, store_id: int | None = None, *, featured_only: bool = False) -> list:
    vendor_rows = _filtered_vendor_rows(db, store_id, featured_only)
    db_products = _load_db_public_catalog(db, store_id, featured_only)
    seen_slug: set[tuple[str, str]] = set()
    seen_nombre: set[tuple[str, str]] = set()
    for item in db_products:
        vendor_key = str(item.get("vendor_id") or "").strip()
        slug = str(item.get("slug") or "").strip().lower()
        nombre = str(item.get("nombre") or "").strip().lower()
        if slug:
            seen_slug.add((vendor_key, slug))
        if nombre:
            seen_nombre.add((vendor_key, nombre))
    themed_products = _load_theme_fallback_catalog(db, vendor_rows, seen_slug, seen_nombre)
    return db_products + themed_products
