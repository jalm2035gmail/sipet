from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import Base


class StoreSupplier(Base):
    __tablename__ = "store_suppliers"
    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    contact_name = Column(String(200), default="")
    email = Column(String(200), nullable=True)
    phone = Column(String(30), nullable=True)
    address = Column(String(500), default="")
    country = Column(String(100), default="")
    website = Column(String(300), nullable=True)
    notes = Column(Text, default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vendor = relationship("VendorStore", foreign_keys=[vendor_id])
