from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, func
from sqlalchemy.orm import relationship
from fastapi_modulo.core.db import MAIN

class RefSettlement(MAIN):
    __tablename__ = "ref_settlement"

    id = Column(Integer, primary_key=True, autoincrement=True)
    referido_id = Column(Integer, ForeignKey("ref_referido.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    settled_at = Column(DateTime, default=func.now())
    settled_by = Column(Integer, nullable=True)  # user_id que aprobó/pagó
    notes = Column(String(500))
    created_at = Column(DateTime, default=func.now())

    referido = relationship("RefReferido", backref="settlements")
