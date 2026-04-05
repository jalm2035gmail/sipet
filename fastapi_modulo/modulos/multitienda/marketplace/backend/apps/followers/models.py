from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import Base


class StoreFollower(Base):
    __tablename__ = "store_followers"
    __table_args__ = (UniqueConstraint("vendor_id", "user_id", name="uq_store_follower"),)
    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    vendor = relationship("VendorStore", foreign_keys=[vendor_id])
    user = relationship("User", foreign_keys=[user_id])
