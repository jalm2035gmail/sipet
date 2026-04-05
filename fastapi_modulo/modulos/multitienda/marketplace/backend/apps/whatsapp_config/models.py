from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import Base


class StoreWhatsappConfig(Base):
    __tablename__ = "store_whatsapp_config"
    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False, unique=True, index=True)
    phone_number = Column(String(30), nullable=False)
    api_token = Column(String(500), nullable=True)
    webhook_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    settings = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vendor = relationship("VendorStore", foreign_keys=[vendor_id])
