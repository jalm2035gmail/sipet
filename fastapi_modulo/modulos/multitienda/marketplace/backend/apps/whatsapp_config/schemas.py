from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime


class StoreWhatsappConfigCreate(BaseModel):
    phone_number: str
    api_token: Optional[str] = None
    webhook_url: Optional[str] = None
    is_active: bool = True
    settings: Optional[Dict] = {}


class StoreWhatsappConfigUpdate(BaseModel):
    phone_number: Optional[str] = None
    api_token: Optional[str] = None
    webhook_url: Optional[str] = None
    is_active: Optional[bool] = None
    settings: Optional[Dict] = None


class StoreWhatsappConfigRead(BaseModel):
    id: int
    vendor_id: int
    phone_number: str
    webhook_url: Optional[str]
    is_active: bool
    settings: Optional[Dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
