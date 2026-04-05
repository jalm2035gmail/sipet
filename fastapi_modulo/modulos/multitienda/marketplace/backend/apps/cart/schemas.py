from __future__ import annotations
from decimal import Decimal
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class CartItemIn(BaseModel):
    product_id: str
    product_name: str = ""
    product_image: str = ""
    store_name: str = ""
    vendor_id: str = ""
    quantity: int = Field(1, ge=1, le=100)
    unit_price: Decimal = Field(Decimal("0"), ge=0)


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=0, le=100)


class CartItemOut(BaseModel):
    id: int
    product_id: str
    product_name: str
    product_image: str
    store_name: str
    vendor_id: str
    quantity: int
    unit_price: float
    subtotal: float

    class Config:
        from_attributes = True


class CartOut(BaseModel):
    session_key: str
    items: List[CartItemOut]
    total: float
    items_count: int
    benefits: List[Any] = []
