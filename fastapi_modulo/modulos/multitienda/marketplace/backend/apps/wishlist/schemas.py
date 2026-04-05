from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class WishlistItemIn(BaseModel):
    product_id: str
    product_name: str = ""
    product_price: str = ""
    product_image: str = ""
    store_name: str = ""


class WishlistItemOut(BaseModel):
    id: int
    product_id: str
    product_name: str
    product_price: str
    product_image: str
    store_name: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
