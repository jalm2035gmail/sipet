from __future__ import annotations

from sqlalchemy import CheckConstraint, Column, Enum, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from fastapi_modulo.core.db import MAIN
from fastapi_modulo.modulos_sipet.modulo_base.core.audit import BaseEntity, SoftDeleteBaseEntity
from fastapi_modulo.modulos_sipet.modulo_base.modelos.enums import ModuloBaseEstado


class ModuloBaseCategoria(BaseEntity, MAIN):
    __tablename__ = "modulo_base_categorias"
    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", name="uq_modulo_base_categorias_tenant_slug"),
        Index("ix_modulo_base_categorias_tenant_nombre", "tenant_id", "nombre"),
    )

    nombre = Column(String(120), nullable=False)
    slug = Column(String(120), nullable=False)
    descripcion = Column(Text, nullable=True)

    registros = relationship("ModuloBaseRegistro", back_populates="categoria", cascade="save-update, merge")


class ModuloBaseRegistro(SoftDeleteBaseEntity, MAIN):
    __tablename__ = "modulo_base_registros"
    __table_args__ = (
        UniqueConstraint("tenant_id", "nombre", name="uq_modulo_base_registros_tenant_nombre"),
        CheckConstraint("length(nombre) >= 3", name="ck_modulo_base_registros_nombre_len"),
        Index("ix_modulo_base_registros_tenant_estado", "tenant_id", "estado"),
        Index("ix_modulo_base_registros_tenant_categoria", "tenant_id", "categoria_id"),
    )

    nombre = Column(String(150), nullable=False)
    descripcion = Column(Text, nullable=True)
    estado = Column(Enum(ModuloBaseEstado, native_enum=False, length=20), nullable=False, default=ModuloBaseEstado.ACTIVO, index=True)
    categoria_id = Column(ForeignKey("modulo_base_categorias.id", ondelete="RESTRICT"), nullable=False, index=True)

    categoria = relationship("ModuloBaseCategoria", back_populates="registros")
