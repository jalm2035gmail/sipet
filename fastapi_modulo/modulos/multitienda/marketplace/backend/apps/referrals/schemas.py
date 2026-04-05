from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class ReferralStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    rewarded = "rewarded"
    expired = "expired"


class RewardType(str, Enum):
    percent = "percent"
    fixed = "fixed"
    points = "points"


class StoreReferralCreate(BaseModel):
    referral_code: str
    reward_type: Optional[RewardType] = None
    reward_value: Optional[float] = None


class StoreReferralRead(BaseModel):
    id: int
    vendor_id: int
    referrer_user_id: int
    referred_user_id: Optional[int]
    referral_code: str
    status: ReferralStatus
    reward_type: Optional[RewardType]
    reward_value: Optional[float]
    reward_given_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
