from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import get_db
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.dependencies import get_session_key as _get_session_key
from .models import Cart, CartItem
from .schemas import CartItemIn, CartItemOut, CartItemUpdate, CartOut
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.products.models import Product, ProductRelated

router = APIRouter(prefix="/api/cart", tags=["cart"])


def _get_or_create_cart(session_key: str, db: Session) -> Cart:
    cart = db.query(Cart).filter(Cart.session_key == session_key).first()
    if not cart:
        cart = Cart(session_key=session_key)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def _serialize_item(item: CartItem) -> dict:
    unit = float(item.unit_price or 0)
    return {
        "id": item.id,
        "product_id": item.product_id,
        "product_name": item.product_name,
        "product_image": item.product_image,
        "store_name": item.store_name,
        "vendor_id": item.vendor_id,
        "quantity": item.quantity,
        "unit_price": unit,
        "subtotal": round(unit * (item.quantity or 1), 2),
    }


def _compute_cart_benefits(items: list, db: Session) -> list:
    """
    Dado el listado de CartItem, devuelve los beneficios activos.
    Solo se consideran items cuyo product_id sea un entero válido.
    Cada entrada indica:
      - trigger_product_id/name: el producto que activa el beneficio
      - related_product_id/name: el producto que recibe el beneficio
      - benefit_type / benefit_value
      - applied: True si el producto beneficiado también está en el carrito
      - discount_amount: monto ahorrado (si applied y hay precio disponible)
    """
    int_ids: dict[int, CartItem] = {}
    for item in items:
        try:
            int_ids[int(item.product_id)] = item
        except (TypeError, ValueError):
            pass

    if not int_ids:
        return []

    rels = (
        db.query(ProductRelated)
        .filter(ProductRelated.product_id.in_(list(int_ids.keys())))
        .all()
    )

    result = []
    for r in rels:
        trigger_item = int_ids.get(r.product_id)
        applied = r.related_product_id in int_ids
        related_item = int_ids.get(r.related_product_id)

        discount_amount = None
        if applied and related_item is not None:
            unit = float(related_item.unit_price or 0)
            bv = float(r.benefit_value or 0)
            if r.benefit_type == "discount_pct":
                discount_amount = round(unit * bv / 100, 2)
            elif r.benefit_type == "discount_fixed":
                discount_amount = round(min(bv, unit), 2)
            elif r.benefit_type == "free_shipping":
                discount_amount = 0.0

        result.append({
            "trigger_product_id":   r.product_id,
            "trigger_product_name": trigger_item.product_name if trigger_item else None,
            "related_product_id":   r.related_product_id,
            "related_product_name": r.related_product.name if r.related_product else None,
            "benefit_type":         r.benefit_type,
            "benefit_value":        float(r.benefit_value or 0),
            "applied":              applied,
            "discount_amount":      discount_amount,
        })

    return result


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/", response_model=CartOut)
def get_cart(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Devuelve el carrito de la sesión actual, incluyendo beneficios activos."""
    session_key = _get_session_key(request, response)
    cart = _get_or_create_cart(session_key, db)
    items = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id)
        .order_by(CartItem.created_at.asc())
        .all()
    )
    items_out = [_serialize_item(i) for i in items]
    total = round(sum(i["subtotal"] for i in items_out), 2)

    # ── Calcular beneficios por productos relacionados ─────────────────────
    benefits = _compute_cart_benefits(items, db)

    return {
        "session_key": session_key,
        "items": items_out,
        "total": total,
        "items_count": len(items_out),
        "benefits": benefits,
    }


@router.post("/items", status_code=201)
def add_item(
    payload: CartItemIn,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Agrega un producto al carrito o incrementa su cantidad si ya existe."""
    try:
        product_id_int = int(payload.product_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="product_id invalido")

    product = (
        db.query(Product)
        .filter(Product.id == product_id_int, Product.is_active.is_(True))
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    session_key = _get_session_key(request, response)
    cart = _get_or_create_cart(session_key, db)

    existing = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id, CartItem.product_id == str(product.id))
        .first()
    )
    if existing:
        existing.quantity += payload.quantity
        db.commit()
        db.refresh(existing)
        return {"message": "Cantidad actualizada", "item": _serialize_item(existing)}

    item = CartItem(
        cart_id=cart.id,
        product_id=str(product.id),
        product_name=payload.product_name or str(product.name or ""),
        product_image=payload.product_image,
        store_name=payload.store_name,
        vendor_id=payload.vendor_id or str(product.vendor_id or ""),
        quantity=payload.quantity,
        unit_price=product.price,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"message": "Producto agregado al carrito", "item": _serialize_item(item)}


@router.put("/items/{item_id}")
def update_item(
    item_id: int,
    payload: CartItemUpdate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Actualiza la cantidad de un ítem (quantity=0 lo elimina)."""
    session_key = _get_session_key(request, response)
    cart = db.query(Cart).filter(Cart.session_key == session_key).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Carrito no encontrado")
    item = (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.cart_id == cart.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado en el carrito")
    if payload.quantity <= 0:
        db.delete(item)
        db.commit()
        return {"message": "Item eliminado del carrito"}
    item.quantity = payload.quantity
    db.commit()
    db.refresh(item)
    return {"message": "Carrito actualizado", "item": _serialize_item(item)}


@router.delete("/items/{item_id}", status_code=204)
def remove_item(
    item_id: int,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Elimina un ítem del carrito."""
    session_key = _get_session_key(request, response)
    cart = db.query(Cart).filter(Cart.session_key == session_key).first()
    if cart:
        item = (
            db.query(CartItem)
            .filter(CartItem.id == item_id, CartItem.cart_id == cart.id)
            .first()
        )
        if item:
            db.delete(item)
            db.commit()
    return Response(status_code=204)


@router.delete("/", status_code=204)
def clear_cart(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Vacía el carrito completo de la sesión."""
    session_key = _get_session_key(request, response)
    cart = db.query(Cart).filter(Cart.session_key == session_key).first()
    if cart:
        db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
        db.commit()
    return Response(status_code=204)
