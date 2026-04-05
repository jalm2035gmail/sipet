from __future__ import annotations

from fastapi_modulo.modulos.multitienda.servicios.store_tables_shared import (
    decode_theme,
    managed_session,
    orm_list,
    row,
    rows,
)


def get_store_stats(store_id: int) -> dict:
    from datetime import date, timedelta
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.analytics.models import VendorAnalytics
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.coupons.models import StoreCoupon
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.employees.models import StoreEmployee
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.products.models import Product

    with managed_session() as db:
        def safe_count(sql, params):
            try:
                current = row(db, sql, params)
                return int(current["cnt"]) if current else 0
            except Exception:
                return 0

        products = db.query(Product).filter_by(vendor_id=store_id).count()
        employees = db.query(StoreEmployee).filter_by(vendor_id=store_id).count()
        coupons = db.query(StoreCoupon).filter_by(vendor_id=store_id, is_active=True).count()
        orders = safe_count("SELECT COUNT(*) AS cnt FROM orders WHERE vendor_id = :vid", {"vid": store_id})

        today = date.today()
        chart_labels, chart_values = [], []
        for i in range(6, -1, -1):
            current_date = today - timedelta(days=i)
            chart_labels.append(current_date.strftime("%d/%m"))
            try:
                analytics = db.query(VendorAnalytics).filter_by(vendor_id=store_id, date=current_date).first()
                chart_values.append(int(analytics.store_views or 0) if analytics else 0)
            except Exception:
                chart_values.append(0)

        return {
            "products": products,
            "employees": employees,
            "coupons": coupons,
            "orders": orders,
            "chart_labels": chart_labels,
            "chart_values": chart_values,
        }


def get_public_products(store_id: int = None, featured_only: bool = False) -> list:
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.products.models import ProductImage
    from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.vendors.models import VendorStore

    try:
        with managed_session() as db:
            vendor_query = db.query(VendorStore).filter_by(is_active=True)
            if store_id is not None:
                vendor_query = vendor_query.filter(VendorStore.id == store_id)
            elif featured_only:
                vendor_query = vendor_query.filter(VendorStore.is_featured.is_(True))
            vendor_rows = orm_list(vendor_query.order_by(VendorStore.id.desc()))
            themed_products = []
            themed_seen: set[tuple] = set()
            for vendor in vendor_rows:
                theme = decode_theme(vendor.get("store_theme"))
                catalog_products = theme.get("catalog_products")
                if not isinstance(catalog_products, list):
                    continue
                for item in catalog_products:
                    if not isinstance(item, dict):
                        continue
                    if not (bool(item.get("publicado")) or bool(item.get("ecomPublicado"))):
                        continue
                    nombre = str(item.get("nombre") or "").strip()
                    if not nombre:
                        continue
                    themed_key = (vendor["id"], nombre.lower())
                    if themed_key in themed_seen:
                        continue
                    themed_seen.add(themed_key)
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

            ids_sin_imagen = [int(item["id"]) for item in themed_products if not item["imagen"] and isinstance(item["id"], int)]
            if ids_sin_imagen:
                img_rows = orm_list(
                    db.query(ProductImage).filter(
                        ProductImage.is_primary.is_(True),
                        ProductImage.product_id.in_(ids_sin_imagen),
                    )
                )
                img_map = {int(item["product_id"]): str(item["image"] or "") for item in img_rows}
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
                db_rows = rows(db, sql, db_params)
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
                db_rows = rows(db, sql, db_params)
                use_category = False

            result = [{
                "id": current["id"],
                "vendor_id": current["vendor_id"],
                "nombre": current["name"] or "",
                "precio": float(current["price"] or 0),
                "imagen": current["primary_image"] or "",
                "galleryImages": [],
                "categoria": (current.get("category_name") or "") if use_category else "",
                "slug": current["slug"] or "",
                "store_slug": str(current.get("store_slug") or "").strip().lower(),
                "descCorta": current["description"] or "",
                "descLarga": current["description"] or "",
                "mostrarDetalles": False,
                "detallesHtml": "",
                "mostrarEspecificaciones": False,
                "especificacionesHtml": "",
                "mostrarCondiciones": False,
                "condicionesHtml": "",
                "tienda": current["store_name"] or "",
                "publicado": True,
                "nuevo": False,
            } for current in db_rows]

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
    except Exception:
        return []
