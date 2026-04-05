import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Enum, Numeric, Text
from sqlalchemy.orm import relationship
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import Base


class LayawayStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    cancelled = "cancelled"
    expired = "expired"


class StoreLayaway(Base):
    __tablename__ = "store_layaways"
    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)
    customer_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    downpayment = Column(Numeric(12, 2), nullable=False)
    balance_due = Column(Numeric(12, 2), nullable=False)
    due_date = Column(DateTime, nullable=True)
    status = Column(Enum(LayawayStatus), default=LayawayStatus.active)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vendor = relationship("VendorStore", foreign_keys=[vendor_id])
    customer = relationship("User", foreign_keys=[customer_user_id])
    product = relationship("Product", foreign_keys=[product_id])
