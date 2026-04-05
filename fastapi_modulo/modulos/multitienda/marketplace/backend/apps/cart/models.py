from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, UniqueConstraint
from sqlalchemy.sql import func
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import Base


class Cart(Base):
    """Carrito de compras identificado por session_key (anónimo o autenticado)."""
    __tablename__ = "mt_cart"

    id = Column(Integer, primary_key=True)
    session_key = Column(String(120), nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CartItem(Base):
    """Ítem dentro de un carrito. Almacena snapshot del producto para evitar
    dependencias de FK al catálogo dinámico."""
    __tablename__ = "mt_cart_items"
    __table_args__ = (
        UniqueConstraint("cart_id", "product_id", name="uq_cartitem_cart_product"),
    )

    id = Column(Integer, primary_key=True)
    cart_id = Column(Integer, nullable=False, index=True)   # → mt_cart.id
    product_id = Column(String(100), nullable=False)         # slug o id externo
    product_name = Column(String(200), nullable=False, default="")
    product_image = Column(Text, nullable=False, default="")
    store_name = Column(String(200), nullable=False, default="")
    vendor_id = Column(String(50), nullable=False, default="")
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(12, 2), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def get_subtotal(self) -> float:
        return round(float(self.unit_price or 0) * (self.quantity or 1), 2)
