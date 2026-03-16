from __future__ import annotations

from sqlalchemy import Column, DateTime, Index, Integer, String, Text

from fastapi_modulo.db import MAIN
from fastapi_modulo.modulos.modulo_base.core.audit import TenantAuditMixin
from fastapi_modulo.modulos.modulo_base.modelos.enums import ModuloBaseEstado


class ModuloBaseRegistro(TenantAuditMixin, MAIN):
    __tablename__ = "modulo_base_registros"
    __table_args__ = (
        Index("ix_modulo_base_registros_tenant_estado", "tenant_id", "estado"),
    )

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    descripcion = Column(Text, nullable=True)
    estado = Column(String(20), nullable=False, default=ModuloBaseEstado.ACTIVO.value, index=True)
