from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class StoreSupplierCreate(BaseModel):
    name: str
    contact_name: Optional[str] = ""
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = ""
    country: Optional[str] = ""
    website: Optional[str] = None
    notes: Optional[str] = ""
    is_active: bool = True


class StoreSupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class StoreSupplierRead(BaseModel):
    id: int
    vendor_id: int
    name: str
    contact_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    country: Optional[str]
    website: Optional[str]
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
