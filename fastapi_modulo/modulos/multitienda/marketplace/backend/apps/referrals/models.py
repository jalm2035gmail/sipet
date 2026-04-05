import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Enum, Numeric
from sqlalchemy.orm import relationship
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import Base


class ReferralStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    rewarded = "rewarded"
    expired = "expired"


class RewardType(str, enum.Enum):
    percent = "percent"
    fixed = "fixed"
    points = "points"


class StoreReferral(Base):
    __tablename__ = "store_referrals"
    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)
    referrer_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    referred_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    referral_code = Column(String(50), nullable=False, unique=True, index=True)
    status = Column(Enum(ReferralStatus), default=ReferralStatus.pending)
    reward_type = Column(Enum(RewardType), nullable=True)
    reward_value = Column(Numeric(10, 2), nullable=True)
    reward_given_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    vendor = relationship("VendorStore", foreign_keys=[vendor_id])
    referrer = relationship("User", foreign_keys=[referrer_user_id])
    referred = relationship("User", foreign_keys=[referred_user_id])
