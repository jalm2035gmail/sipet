from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint

from fastapi_modulo.db import MAIN
from fastapi_modulo.modulos.crm.modelos.enums import (
    EstadoCampania,
    EstadoContactoCampania,
    EtapaOportunidad,
    FuenteContacto,
    TipoActividad,
    TipoCampania,
    TipoContacto,
)


class CrmContacto(MAIN):
    __tablename__ = "crm_contactos"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_crm_contacto_tenant_email"),
        Index("ix_crm_contactos_tenant_email", "tenant_id", "email"),
        Index("ix_crm_contactos_tenant_tipo", "tenant_id", "tipo"),
        Index("ix_crm_contactos_tenant_sucursal", "tenant_id", "sucursal"),
        Index("ix_crm_contactos_tenant_lead_score", "tenant_id", "lead_score"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    nombre = Column(String(150), nullable=False)
    email = Column(String(150), nullable=True, index=True)
    telefono = Column(String(30), nullable=False, default="")
    empresa = Column(String(150), nullable=False, default="")
    puesto = Column(String(100), nullable=False, default="")
    sucursal = Column(String(100), nullable=False, default="", index=True)
    tipo = Column(String(20), nullable=False, default=TipoContacto.PROSPECTO.value, index=True)
    fuente = Column(String(50), nullable=False, default=FuenteContacto.MANUAL.value)
    fuente_detalle = Column(String(120), nullable=False, default="")
    lead_score = Column(Integer, nullable=False, default=0, index=True)
    notas = Column(Text, nullable=True)
    creado_por = Column(String(100), nullable=False, default="")
    actualizado_por = Column(String(100), nullable=False, default="")
    asignado_a = Column(String(100), nullable=False, default="")
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)
    actualizado_en = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class CrmOportunidad(MAIN):
    __tablename__ = "crm_oportunidades"
    __table_args__ = (
        Index("ix_crm_oportunidades_tenant_etapa", "tenant_id", "etapa"),
        Index("ix_crm_oportunidades_tenant_responsable", "tenant_id", "responsable"),
        Index("ix_crm_oportunidades_tenant_fecha_cierre_est", "tenant_id", "fecha_cierre_est"),
        Index("ix_crm_oportunidades_tenant_sucursal", "tenant_id", "sucursal"),
        Index("ix_crm_oportunidades_tenant_ultimo_movimiento_en", "tenant_id", "ultimo_movimiento_en"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    contacto_id = Column(Integer, ForeignKey("crm_contactos.id", ondelete="CASCADE"), nullable=False, index=True)
    nombre = Column(String(200), nullable=False)
    sucursal = Column(String(100), nullable=False, default="", index=True)
    etapa = Column(String(30), nullable=False, default=EtapaOportunidad.PROSPECTO.value, index=True)
    valor_estimado = Column(Float, nullable=False, default=0.0)
    probabilidad = Column(Integer, nullable=False, default=0)
    fecha_cierre_est = Column(Date, nullable=True, index=True)
    fecha_cierre_real = Column(Date, nullable=True)
    cerrado_por = Column(String(100), nullable=False, default="")
    cerrado_en = Column(DateTime, nullable=True)
    creado_por = Column(String(100), nullable=False, default="")
    actualizado_por = Column(String(100), nullable=False, default="")
    asignado_a = Column(String(100), nullable=False, default="")
    responsable = Column(String(100), nullable=False, default="", index=True)
    descripcion = Column(Text, nullable=True)
    ultimo_movimiento_en = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)
    actualizado_en = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class CrmActividad(MAIN):
    __tablename__ = "crm_actividades"
    __table_args__ = (
        Index("ix_crm_actividades_tenant_tipo", "tenant_id", "tipo"),
        Index("ix_crm_actividades_tenant_responsable", "tenant_id", "responsable"),
        Index("ix_crm_actividades_tenant_fecha", "tenant_id", "fecha"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    contacto_id = Column(Integer, ForeignKey("crm_contactos.id", ondelete="CASCADE"), nullable=True, index=True)
    oportunidad_id = Column(Integer, ForeignKey("crm_oportunidades.id", ondelete="CASCADE"), nullable=True, index=True)
    tipo = Column(String(30), nullable=False, default=TipoActividad.TAREA.value, index=True)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    fecha = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    completada = Column(Boolean, nullable=False, default=False)
    fecha_completada = Column(DateTime, nullable=True)
    creado_por = Column(String(100), nullable=False, default="")
    actualizado_por = Column(String(100), nullable=False, default="")
    asignado_a = Column(String(100), nullable=False, default="")
    responsable = Column(String(100), nullable=False, default="", index=True)
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)


class CrmNota(MAIN):
    __tablename__ = "crm_notas"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    contacto_id = Column(Integer, ForeignKey("crm_contactos.id", ondelete="CASCADE"), nullable=True, index=True)
    oportunidad_id = Column(Integer, ForeignKey("crm_oportunidades.id", ondelete="CASCADE"), nullable=True, index=True)
    contenido = Column(Text, nullable=False)
    autor = Column(String(100), nullable=False, default="")
    creado_por = Column(String(100), nullable=False, default="")
    actualizado_por = Column(String(100), nullable=False, default="")
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)


class CrmCampania(MAIN):
    __tablename__ = "crm_campanias"
    __table_args__ = (
        UniqueConstraint("tenant_id", "nombre", name="uq_crm_campania_tenant_nombre"),
        Index("ix_crm_campanias_tenant_estado", "tenant_id", "estado"),
        Index("ix_crm_campanias_tenant_fecha_inicio", "tenant_id", "fecha_inicio"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    nombre = Column(String(150), nullable=False)
    tipo = Column(String(50), nullable=False, default=TipoCampania.EMAIL.value)
    estado = Column(String(20), nullable=False, default=EstadoCampania.BORRADOR.value, index=True)
    fecha_inicio = Column(Date, nullable=True, index=True)
    fecha_fin = Column(Date, nullable=True)
    cerrado_por = Column(String(100), nullable=False, default="")
    cerrado_en = Column(DateTime, nullable=True)
    creado_por = Column(String(100), nullable=False, default="")
    actualizado_por = Column(String(100), nullable=False, default="")
    asignado_a = Column(String(100), nullable=False, default="")
    descripcion = Column(Text, nullable=True)
    resultado = Column(Text, nullable=True)
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)


class CrmContactoCampania(MAIN):
    __tablename__ = "crm_contactos_campanias"
    __table_args__ = (
        UniqueConstraint("tenant_id", "contacto_id", "campania_id", name="uq_crm_contacto_campania"),
        Index("ix_crm_contactos_campanias_tenant_estado", "tenant_id", "estado"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    contacto_id = Column(Integer, ForeignKey("crm_contactos.id", ondelete="CASCADE"), nullable=False, index=True)
    campania_id = Column(Integer, ForeignKey("crm_campanias.id", ondelete="CASCADE"), nullable=False, index=True)
    estado = Column(String(20), nullable=False, default=EstadoContactoCampania.PENDIENTE.value, index=True)
    creado_por = Column(String(100), nullable=False, default="")
    actualizado_por = Column(String(100), nullable=False, default="")


class CrmEvento(MAIN):
    __tablename__ = "crm_eventos"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    entidad = Column(String(50), nullable=False, index=True)
    entidad_id = Column(Integer, nullable=True, index=True)
    tipo_evento = Column(String(50), nullable=False, index=True)
    actor = Column(String(100), nullable=False, default="")
    descripcion = Column(String(255), nullable=False, default="")
    payload = Column(JSON, nullable=True)
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
