from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class StoreVideoCreate(BaseModel):
    product_id: Optional[int] = None
    title: str
    url: str
    thumbnail: Optional[str] = None
    description: Optional[str] = ""
    is_active: bool = True
    order: int = 0


class StoreVideoUpdate(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    thumbnail: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    order: Optional[int] = None


class StoreVideoRead(BaseModel):
    id: int
    vendor_id: int
    product_id: Optional[int]
    title: str
    url: str
    thumbnail: Optional[str]
    description: Optional[str]
    is_active: bool
    order: int
    created_at: datetime

    class Config:
        from_attributes = True
