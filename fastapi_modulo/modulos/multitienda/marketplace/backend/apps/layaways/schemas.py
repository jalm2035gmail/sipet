from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class LayawayStatus(str, Enum):
    active = "active"
    completed = "completed"
    cancelled = "cancelled"
    expired = "expired"


class StoreLayawayCreate(BaseModel):
    product_id: int
    total_amount: float
    downpayment: float
    due_date: Optional[datetime] = None
    notes: Optional[str] = ""


class StoreLayawayUpdate(BaseModel):
    status: Optional[LayawayStatus] = None
    balance_due: Optional[float] = None
    due_date: Optional[datetime] = None
    notes: Optional[str] = None


class StoreLayawayRead(BaseModel):
    id: int
    vendor_id: int
    customer_user_id: int
    product_id: int
    total_amount: float
    downpayment: float
    balance_due: float
    due_date: Optional[datetime]
    status: LayawayStatus
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
