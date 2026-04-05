import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Enum, Numeric
from sqlalchemy.orm import relationship
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import Base


class DiscountType(str, enum.Enum):
    percent = "percent"
    fixed = "fixed"


class StoreCoupon(Base):
    __tablename__ = "store_coupons"
    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)
    code = Column(String(50), nullable=False, index=True)
    discount_type = Column(Enum(DiscountType), default=DiscountType.percent)
    discount_value = Column(Numeric(10, 2), nullable=False)
    min_order_amount = Column(Numeric(10, 2), default=0)
    max_uses = Column(Integer, nullable=True)
    uses_count = Column(Integer, default=0)
    per_user_limit = Column(Integer, default=1)
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    vendor = relationship("VendorStore", foreign_keys=[vendor_id])
