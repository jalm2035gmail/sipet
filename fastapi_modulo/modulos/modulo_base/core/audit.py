from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, String


class TenantAuditMixin:
    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)
    actualizado_en = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    creado_por = Column(String(100), nullable=True, default=None)
    actualizado_por = Column(String(100), nullable=True, default=None)
