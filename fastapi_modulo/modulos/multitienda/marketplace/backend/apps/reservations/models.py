import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import Base


class ReservationStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"
    no_show = "no_show"


class StoreReservation(Base):
    __tablename__ = "store_reservations"
    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)
    customer_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    reservation_date = Column(DateTime, nullable=False)
    time_slot = Column(String(20), nullable=True)
    duration_minutes = Column(Integer, default=60)
    notes = Column(Text, default="")
    status = Column(Enum(ReservationStatus), default=ReservationStatus.pending)
    confirmed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vendor = relationship("VendorStore", foreign_keys=[vendor_id])
    customer = relationship("User", foreign_keys=[customer_user_id])
    product = relationship("Product", foreign_keys=[product_id])
