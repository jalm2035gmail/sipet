from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime


class StoreAiConfigCreate(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    settings: Optional[Dict] = {}
    is_active: bool = True


class StoreAiConfigUpdate(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    settings: Optional[Dict] = None
    is_active: Optional[bool] = None


class StoreAiConfigRead(BaseModel):
    id: int
    vendor_id: int
    provider: str
    model: str
    settings: Optional[Dict]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
