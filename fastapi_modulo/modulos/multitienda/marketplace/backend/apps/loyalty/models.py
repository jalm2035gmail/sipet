from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Numeric, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship

from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import Base


class LoyaltyPlan(Base):
    """Configuración del programa de puntos por tienda (1 por vendor)."""
    __tablename__ = "loyalty_plans"

    id = Column(Integer, primary_key=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False, unique=True)
    name = Column(String(100), default="Programa de puntos")
    points_per_peso = Column(Numeric(8, 4), default=1.0)    # puntos ganados por $ gastado
    min_redeem_points = Column(Integer, default=100)          # mínimo para redimir
    redeem_rate = Column(Numeric(8, 4), default=0.01)         # $ por punto al redimir
    is_active = Column(Boolean, default=True)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vendor = relationship("VendorStore", foreign_keys=[vendor_id])


class LoyaltyAccount(Base):
    """Cuenta de puntos de un cliente en una tienda específica."""
    __tablename__ = "loyalty_accounts"

    id = Column(Integer, primary_key=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    customer_email = Column(String(255), nullable=False)
    customer_name = Column(String(200), default="")
    current_points = Column(Integer, default=0)
    lifetime_points = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vendor = relationship("VendorStore", foreign_keys=[vendor_id])
    transactions = relationship("LoyaltyTransaction", back_populates="account", cascade="all, delete-orphan")


class LoyaltyTransaction(Base):
    """Historial de movimientos de puntos."""
    __tablename__ = "loyalty_transactions"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("loyalty_accounts.id"), nullable=False)
    points = Column(Integer, nullable=False)       # positivo=ganado, negativo=redimido/expirado
    transaction_type = Column(String(20), nullable=False, default="earned")
    reference = Column(String(100), default="")    # num. pedido u otra referencia
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    account = relationship("LoyaltyAccount", back_populates="transactions")
