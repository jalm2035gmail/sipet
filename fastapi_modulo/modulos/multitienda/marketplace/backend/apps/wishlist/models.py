from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import Base


class WishlistItem(Base):
    __tablename__ = "wishlist_items"
    __table_args__ = (
        UniqueConstraint("session_key", "product_id", name="uq_wishlist_session_product"),
    )

    id = Column(Integer, primary_key=True)
    # Identificador de sesión anónima (cookie/localStorage key enviada por el cliente)
    session_key = Column(String(120), nullable=False, index=True)
    # Referencia lógica al producto (por slug o id externo, sin FK dura para soportar catálogo dinámico)
    product_id = Column(String(100), nullable=False)
    product_name = Column(String(200), nullable=False, default="")
    product_price = Column(String(40), nullable=False, default="")
    product_image = Column(Text, nullable=False, default="")
    store_name = Column(String(200), nullable=False, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
