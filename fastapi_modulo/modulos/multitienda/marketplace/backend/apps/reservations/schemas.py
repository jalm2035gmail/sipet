from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class ReservationStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"
    no_show = "no_show"


class StoreReservationCreate(BaseModel):
    product_id: Optional[int] = None
    reservation_date: datetime
    time_slot: Optional[str] = None
    duration_minutes: int = 60
    notes: Optional[str] = ""


class StoreReservationUpdate(BaseModel):
    status: Optional[ReservationStatus] = None
    notes: Optional[str] = None
    reservation_date: Optional[datetime] = None
    time_slot: Optional[str] = None


class StoreReservationRead(BaseModel):
    id: int
    vendor_id: int
    customer_user_id: int
    product_id: Optional[int]
    reservation_date: datetime
    time_slot: Optional[str]
    duration_minutes: int
    notes: Optional[str]
    status: ReservationStatus
    confirmed_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
