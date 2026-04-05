from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import Base


class StoreVideo(Base):
    __tablename__ = "store_videos"
    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True, index=True)
    title = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    thumbnail = Column(String(500), nullable=True)
    description = Column(Text, default="")
    is_active = Column(Boolean, default=True)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    vendor = relationship("VendorStore", foreign_keys=[vendor_id])
    product = relationship("Product", foreign_keys=[product_id])
