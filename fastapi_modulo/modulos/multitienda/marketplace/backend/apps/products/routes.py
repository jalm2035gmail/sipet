from __future__ import annotations

import re
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import SessionLocal
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.routes import require_any_role
from .models import Product, Category, ProductImage, ProductVariant, ProductStatus, ProductRelated, BENEFIT_TYPES

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text


def _serialize_product(p: Product) -> dict:
    return {
        "id":             p.id,
        "vendor_id":      p.vendor_id,
        "name":           p.name,
        "description":    p.description or "",
        "price":          float(p.price),
        "compare_price":  float(p.compare_price) if p.compare_price else None,
        "discount_pct":   round((1 - float(p.price) / float(p.compare_price)) * 100, 1)
                          if p.compare_price and float(p.compare_price) > float(p.price) else None,
        "stock_quantity": p.stock_quantity,
        "slug":           p.slug,
        "is_active":      p.is_active,
        "status":         p.status.value if hasattr(p.status, "value") else str(p.status),
        "type":           p.type.value if hasattr(p.type, "value") else str(p.type),
        "created_at":     p.created_at.isoformat() if p.created_at else None,
        "updated_at":     p.updated_at.isoformat() if p.updated_at else None,
        "images":  [{"id": i.id, "image": i.image, "alt_text": i.alt_text,
                     "is_primary": i.is_primary, "order": i.order}
                    for i in (p.images or [])],
        "variants": [{"id": v.id, "sku": v.sku, "price": float(v.price),
                      "compare_price": float(v.compare_price) if v.compare_price else None,
                      "stock_quantity": v.stock_quantity, "attributes": v.attributes or {}}
                     for v in (p.variants or [])],
    }


# ── List products for a store ──────────────────────────────────────────────────

@router.get("/store/{vendor_id}")
def list_store_products(
    vendor_id: int,
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin", "store_employee")),
):
    query = db.query(Product).filter(Product.vendor_id == vendor_id)
    if status:
        query = query.filter(Product.status == status)
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))
    products = query.order_by(Product.id.desc()).all()
    return {"success": True, "data": [_serialize_product(p) for p in products]}


# ── Public catalog ─────────────────────────────────────────────────────────────

@router.get("/public/{vendor_id}")
def list_public_products(
    vendor_id: int,
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Product).filter(
        Product.vendor_id == vendor_id,
        Product.is_active == True,
        Product.status == ProductStatus.published,
    )
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))
    products = query.order_by(Product.id.desc()).all()
    return {"success": True, "data": [_serialize_product(p) for p in products]}


# ── Get single product ─────────────────────────────────────────────────────────

@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    return {"success": True, "data": _serialize_product(p)}


# ── Create product ─────────────────────────────────────────────────────────────

@router.post("/store/{vendor_id}", status_code=201)
def create_product(
    vendor_id: int,
    data: dict,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin")),
):
    name = str(data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio.")
    slug = str(data.get("slug") or _slugify(name) or "producto").strip()
    # make slug unique
    base_slug = slug
    counter = 1
    while db.query(Product).filter(Product.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    price = data.get("price")
    try:
        price = float(price)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="El precio debe ser un número.")

    compare_price = data.get("compare_price")
    if compare_price is not None:
        try:
            compare_price = float(compare_price)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="compare_price debe ser un número.")
        if compare_price <= price:
            raise HTTPException(status_code=400, detail="compare_price debe ser mayor al precio de venta.")

    product = Product(
        vendor_id=      vendor_id,
        name=           name,
        slug=           slug,
        description=    str(data.get("description") or ""),
        price=          price,
        compare_price=  compare_price,
        stock_quantity= int(data.get("stock_quantity") or 0),
        is_active=      bool(data.get("is_active", False)),
        status=         data.get("status", "draft"),
        type=           data.get("type", "simple"),
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return {"success": True, "data": _serialize_product(product)}


# ── Update product ─────────────────────────────────────────────────────────────

@router.put("/{product_id}")
def update_product(
    product_id: int,
    data: dict,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin")),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")

    for field in ("name", "description", "status", "type"):
        if field in data and data[field] is not None:
            setattr(product, field, data[field])
    if "price" in data and data["price"] is not None:
        product.price = float(data["price"])
    if "compare_price" in data:
        if data["compare_price"] is None:
            product.compare_price = None
        else:
            cp = float(data["compare_price"])
            sale = float(data.get("price") or product.price)
            if cp <= sale:
                raise HTTPException(status_code=400, detail="compare_price debe ser mayor al precio de venta.")
            product.compare_price = cp
    if "stock_quantity" in data and data["stock_quantity"] is not None:
        product.stock_quantity = int(data["stock_quantity"])
    if "is_active" in data:
        product.is_active = bool(data["is_active"])
    if "slug" in data and data["slug"]:
        slug = str(data["slug"]).strip()
        existing = db.query(Product).filter(Product.slug == slug, Product.id != product_id).first()
        if existing:
            raise HTTPException(status_code=409, detail="El slug ya pertenece a otro producto.")
        product.slug = slug

    db.commit()
    db.refresh(product)
    return {"success": True, "data": _serialize_product(product)}


# ── Delete product ─────────────────────────────────────────────────────────────

@router.delete("/{product_id}", status_code=200)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin")),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    db.delete(product)
    db.commit()
    return {"success": True}


# ── Product Images ─────────────────────────────────────────────────────────────

@router.get("/{product_id}/images")
def list_product_images(product_id: int, db: Session = Depends(get_db)):
    images = (
        db.query(ProductImage)
        .filter(ProductImage.product_id == product_id)
        .order_by(ProductImage.is_primary.desc(), ProductImage.order)
        .all()
    )
    return {"success": True, "data": [
        {"id": i.id, "image": i.image, "alt_text": i.alt_text,
         "is_primary": i.is_primary, "order": i.order}
        for i in images
    ]}


@router.post("/{product_id}/images", status_code=201)
def add_product_image(
    product_id: int,
    data: dict,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin")),
):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    is_primary = bool(data.get("is_primary", False))
    if is_primary:
        db.query(ProductImage).filter(ProductImage.product_id == product_id).update({"is_primary": False})
    image = ProductImage(
        product_id=product_id,
        image=str(data.get("image") or ""),
        alt_text=str(data.get("alt_text") or ""),
        is_primary=is_primary,
        order=int(data.get("order") or 0),
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return {"success": True, "data": {
        "id": image.id, "image": image.image, "alt_text": image.alt_text,
        "is_primary": image.is_primary, "order": image.order,
    }}


@router.put("/{product_id}/images/{image_id}/primary")
def set_primary_image(
    product_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin")),
):
    img = db.query(ProductImage).filter(
        ProductImage.id == image_id,
        ProductImage.product_id == product_id,
    ).first()
    if not img:
        raise HTTPException(status_code=404, detail="Imagen no encontrada.")
    db.query(ProductImage).filter(ProductImage.product_id == product_id).update({"is_primary": False})
    img.is_primary = True
    db.commit()
    return {"success": True}


@router.delete("/{product_id}/images/{image_id}", status_code=200)
def delete_product_image(
    product_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin")),
):
    img = db.query(ProductImage).filter(
        ProductImage.id == image_id,
        ProductImage.product_id == product_id,
    ).first()
    if not img:
        raise HTTPException(status_code=404, detail="Imagen no encontrada.")
    db.delete(img)
    db.commit()
    return {"success": True}


# ── Categories ─────────────────────────────────────────────────────────────────

@router.get("/categories/all")
def list_categories(db: Session = Depends(get_db)):
    cats = db.query(Category).order_by(Category.name).all()
    return {"success": True, "data": [
        {"id": c.id, "name": c.name, "slug": c.slug, "description": c.description,
         "parent_id": c.parent_id}
        for c in cats
    ]}


# ── Related products (cross-product benefits) ─────────────────────────────────

def _serialize_related(r: ProductRelated) -> dict:
    return {
        "id":                   r.id,
        "product_id":           r.product_id,
        "related_product_id":   r.related_product_id,
        "benefit_type":         r.benefit_type,
        "benefit_value":        float(r.benefit_value or 0),
        "related_product_name": r.related_product.name if r.related_product else None,
        "related_product_slug": r.related_product.slug if r.related_product else None,
        "related_product_price": float(r.related_product.price) if r.related_product else None,
    }


@router.get("/{product_id}/related")
def list_related_products(product_id: int, db: Session = Depends(get_db)):
    """Lista los productos que reciben un beneficio cuando se compra `product_id`."""
    rels = (
        db.query(ProductRelated)
        .filter(ProductRelated.product_id == product_id)
        .all()
    )
    return {"success": True, "data": [_serialize_related(r) for r in rels]}


@router.post("/{product_id}/related", status_code=201)
def add_related_product(
    product_id: int,
    data: dict,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin")),
):
    """Configura que al comprar `product_id`, un producto relacionado obtenga un beneficio."""
    if not db.query(Product).filter(Product.id == product_id).first():
        raise HTTPException(status_code=404, detail="Producto no encontrado.")

    try:
        related_id = int(data["related_product_id"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=400, detail="related_product_id es obligatorio y debe ser entero.")

    if related_id == product_id:
        raise HTTPException(status_code=400, detail="Un producto no puede relacionarse consigo mismo.")
    if not db.query(Product).filter(Product.id == related_id).first():
        raise HTTPException(status_code=404, detail="Producto relacionado no encontrado.")

    benefit_type = str(data.get("benefit_type") or "")
    if benefit_type not in BENEFIT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"benefit_type inválido. Válidos: {', '.join(BENEFIT_TYPES)}",
        )

    benefit_value = float(data.get("benefit_value") or 0)
    if benefit_type == "discount_pct" and not (0 < benefit_value <= 100):
        raise HTTPException(status_code=400, detail="discount_pct debe estar entre 1 y 100.")
    if benefit_type == "discount_fixed" and benefit_value <= 0:
        raise HTTPException(status_code=400, detail="discount_fixed debe ser mayor a 0.")

    if db.query(ProductRelated).filter_by(product_id=product_id, related_product_id=related_id).first():
        raise HTTPException(status_code=409, detail="La relación ya existe.")

    rel = ProductRelated(
        product_id=product_id,
        related_product_id=related_id,
        benefit_type=benefit_type,
        benefit_value=benefit_value,
    )
    db.add(rel)
    db.commit()
    db.refresh(rel)
    return {"success": True, "data": _serialize_related(rel)}


@router.put("/{product_id}/related/{related_id}")
def update_related_product(
    product_id: int,
    related_id: int,
    data: dict,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin")),
):
    """Actualiza el tipo o valor del beneficio de una relación existente."""
    rel = db.query(ProductRelated).filter_by(
        product_id=product_id, related_product_id=related_id
    ).first()
    if not rel:
        raise HTTPException(status_code=404, detail="Relación no encontrada.")

    if "benefit_type" in data:
        if data["benefit_type"] not in BENEFIT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"benefit_type inválido. Válidos: {', '.join(BENEFIT_TYPES)}",
            )
        rel.benefit_type = data["benefit_type"]

    if "benefit_value" in data:
        rel.benefit_value = float(data["benefit_value"])

    db.commit()
    db.refresh(rel)
    return {"success": True, "data": _serialize_related(rel)}


@router.delete("/{product_id}/related/{related_id}", status_code=200)
def delete_related_product(
    product_id: int,
    related_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_any_role("vendor", "superadmin")),
):
    rel = db.query(ProductRelated).filter_by(
        product_id=product_id, related_product_id=related_id
    ).first()
    if not rel:
        raise HTTPException(status_code=404, detail="Relación no encontrada.")
    db.delete(rel)
    db.commit()
    return {"success": True}


@router.post("/benefits/compute")
def compute_benefits(data: dict, db: Session = Depends(get_db)):
    """
    Dado un conjunto de IDs de productos en el carrito, devuelve todos los
    beneficios que aplican, indicando si el producto beneficiado está también
    en el carrito y el descuento calculado.

    Body: {"product_ids": [1, 2, 3], "cart_prices": {"2": 150.00, "3": 80.00}}
    `cart_prices` es opcional; si se envía, se calcula `discount_amount`.
    """
    raw_ids = data.get("product_ids") or []
    product_ids = [int(x) for x in raw_ids if str(x).lstrip("-").isdigit()]
    if not product_ids:
        return {"success": True, "data": []}

    cart_prices: dict = {str(k): float(v) for k, v in (data.get("cart_prices") or {}).items()}
    cart_id_set = set(str(pid) for pid in product_ids)

    rels = (
        db.query(ProductRelated)
        .filter(ProductRelated.product_id.in_(product_ids))
        .all()
    )

    result = []
    for r in rels:
        applied = str(r.related_product_id) in cart_id_set
        unit_price = cart_prices.get(str(r.related_product_id))

        discount_amount = None
        if applied and unit_price is not None:
            bv = float(r.benefit_value or 0)
            if r.benefit_type == "discount_pct":
                discount_amount = round(unit_price * bv / 100, 2)
            elif r.benefit_type == "discount_fixed":
                discount_amount = round(min(bv, unit_price), 2)
            elif r.benefit_type == "free_shipping":
                discount_amount = 0.0

        entry = _serialize_related(r)
        entry["applied"] = applied
        entry["discount_amount"] = discount_amount
        result.append(entry)

    return {"success": True, "data": result}

