from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String


class TenantMixin:
    tenant_id = Column(String(100), nullable=False, default="default", index=True)


class TimestampMixin:
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)
    actualizado_en = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditUserMixin:
    creado_por = Column(String(100), nullable=True, default=None)
    actualizado_por = Column(String(100), nullable=True, default=None)


class SoftDeleteMixin:
    eliminado = Column(Boolean, nullable=False, default=False, index=True)
    eliminado_en = Column(DateTime, nullable=True, default=None)
    eliminado_por = Column(String(100), nullable=True, default=None)


class TenantAuditMixin(TenantMixin, TimestampMixin, AuditUserMixin):
    pass


class BaseEntity(TenantAuditMixin):
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)


class SoftDeleteBaseEntity(BaseEntity, SoftDeleteMixin):
    __abstract__ = True
