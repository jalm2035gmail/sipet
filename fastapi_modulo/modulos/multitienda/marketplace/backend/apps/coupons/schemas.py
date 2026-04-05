from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class DiscountType(str, Enum):
    percent = "percent"
    fixed = "fixed"


class StoreCouponCreate(BaseModel):
    code: str
    discount_type: DiscountType = DiscountType.percent
    discount_value: float
    min_order_amount: float = 0
    max_uses: Optional[int] = None
    per_user_limit: int = 1
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: bool = True


class StoreCouponUpdate(BaseModel):
    discount_value: Optional[float] = None
    min_order_amount: Optional[float] = None
    max_uses: Optional[int] = None
    per_user_limit: Optional[int] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: Optional[bool] = None


class StoreCouponRead(BaseModel):
    id: int
    vendor_id: int
    code: str
    discount_type: DiscountType
    discount_value: float
    min_order_amount: float
    max_uses: Optional[int]
    uses_count: int
    per_user_limit: int
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
