from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from typing import List

from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.wishlist.models import WishlistItem
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.wishlist.schemas import (
    WishlistItemIn,
    WishlistItemOut,
)
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import get_db
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.dependencies import get_session_key as _get_session_key

router = APIRouter(prefix="/api/wishlist", tags=["wishlist"])


@router.get("/", response_model=List[WishlistItemOut])
def list_wishlist(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Devuelve todos los items de la wishlist de la sesión actual."""
    session_key = _get_session_key(request, response)
    items = db.query(WishlistItem).filter(WishlistItem.session_key == session_key).order_by(WishlistItem.created_at.desc()).all()
    return items


@router.post("/", response_model=WishlistItemOut, status_code=201)
def add_to_wishlist(
    payload: WishlistItemIn,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Agrega un producto a la wishlist. Si ya existe, lo devuelve sin duplicar."""
    session_key = _get_session_key(request, response)
    existing = db.query(WishlistItem).filter(
        WishlistItem.session_key == session_key,
        WishlistItem.product_id == payload.product_id,
    ).first()
    if existing:
        return existing
    item = WishlistItem(
        session_key=session_key,
        product_id=payload.product_id,
        product_name=payload.product_name,
        product_price=payload.product_price,
        product_image=payload.product_image,
        store_name=payload.store_name,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{product_id}", status_code=204)
def remove_from_wishlist(
    product_id: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Elimina un producto de la wishlist."""
    session_key = _get_session_key(request, response)
    item = db.query(WishlistItem).filter(
        WishlistItem.session_key == session_key,
        WishlistItem.product_id == product_id,
    ).first()
    if item:
        db.delete(item)
        db.commit()
    return Response(status_code=204)


@router.delete("/", status_code=204)
def clear_wishlist(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Vacía la wishlist completa de la sesión."""
    session_key = _get_session_key(request, response)
    db.query(WishlistItem).filter(WishlistItem.session_key == session_key).delete()
    db.commit()
    return Response(status_code=204)
