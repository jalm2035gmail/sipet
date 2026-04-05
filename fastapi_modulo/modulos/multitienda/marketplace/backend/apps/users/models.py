from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, String
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import Base
import enum

class UserType(str, enum.Enum):
    superadmin = "superadmin"
    vendor = "vendor"
    customer = "customer"
    store_employee = "store_employee"
    financial_analyst = "financial_analyst"

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    user_type = Column(Enum(UserType), nullable=False)
    vendor_profile_id = Column(Integer, ForeignKey("vendors.id"), nullable=True, index=True)
    two_factor_enabled = Column(Boolean, nullable=False, default=False)
