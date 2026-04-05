from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from fastapi_modulo.core.db import MAIN
from fastapi_modulo.modulos.crm.modelos.enums import (
    EstadoActividad,
    EstadoCampania,
    EstadoContactoCampania,
    EtapaOportunidad,
    FuenteContacto,
    PrioridadActividad,
    TipoActividad,
    TipoCampania,
    TipoContacto,
)


class CrmMotivoPerdida(MAIN):
    __tablename__ = "crm_motivos_perdida"
    __table_args__ = (
        UniqueConstraint("tenant_id", "nombre", name="uq_crm_motivo_perdida_tenant_nombre"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    nombre = Column(String(120), nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)


class CrmMotivoGanancia(MAIN):
    __tablename__ = "crm_motivos_ganancia"
    __table_args__ = (
        UniqueConstraint("tenant_id", "nombre", name="uq_crm_motivo_ganancia_tenant_nombre"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    nombre = Column(String(120), nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)


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
    lead_temperatura = Column(String(20), nullable=True)
    notas = Column(Text, nullable=True)
    creado_por = Column(String(100), nullable=False, default="")
    actualizado_por = Column(String(100), nullable=False, default="")
    asignado_a = Column(String(100), nullable=False, default="")
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)
    actualizado_en = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    activo = Column(Boolean, nullable=False, default=True, index=True)
    archivado_en = Column(DateTime, nullable=True)
    archivado_por = Column(String(100), nullable=True)


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
    # Campos Fase 1
    motivo_perdida_id = Column(Integer, ForeignKey("crm_motivos_perdida.id", ondelete="SET NULL"), nullable=True)
    motivo_ganancia_id = Column(Integer, ForeignKey("crm_motivos_ganancia.id", ondelete="SET NULL"), nullable=True)
    monto_real = Column(Float, nullable=True)
    producto_vendido = Column(String(200), nullable=True)
    # Campos Fase 3
    probabilidad_sistema = Column(Float, nullable=True)
    probabilidad_usuario = Column(Float, nullable=True)
    # Soft delete
    activo = Column(Boolean, nullable=False, default=True, index=True)
    archivado_en = Column(DateTime, nullable=True)
    archivado_por = Column(String(100), nullable=True)
    # Concurrencia optimista
    version = Column(Integer, nullable=False, default=1)


class CrmHistorialEtapa(MAIN):
    __tablename__ = "crm_historial_etapas"
    __table_args__ = (
        Index("ix_crm_historial_etapas_tenant_oportunidad", "tenant_id", "oportunidad_id"),
        Index("ix_crm_historial_etapas_fecha", "fecha_cambio"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    oportunidad_id = Column(Integer, ForeignKey("crm_oportunidades.id", ondelete="CASCADE"), nullable=False, index=True)
    etapa_anterior = Column(String(30), nullable=True)
    etapa_nueva = Column(String(30), nullable=False)
    fecha_cambio = Column(DateTime, nullable=False, default=datetime.utcnow)
    actor = Column(String(100), nullable=False, default="")
    comentario = Column(Text, nullable=True)
    motivo = Column(String(200), nullable=True)


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
    prioridad = Column(String(20), nullable=False, default=PrioridadActividad.MEDIA.value, index=True)
    estado = Column(String(20), nullable=False, default=EstadoActividad.PENDIENTE.value, index=True)
    tipo_resultado = Column(String(30), nullable=True)
    sla_horas = Column(Integer, nullable=True)
    siguiente_accion = Column(Text, nullable=True)
    creado_por = Column(String(100), nullable=False, default="")
    actualizado_por = Column(String(100), nullable=False, default="")
    asignado_a = Column(String(100), nullable=False, default="")
    responsable = Column(String(100), nullable=False, default="", index=True)
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)
    # Soft delete
    activo = Column(Boolean, nullable=False, default=True, index=True)
    archivado_en = Column(DateTime, nullable=True)
    archivado_por = Column(String(100), nullable=True)


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
    # Soft delete
    activo = Column(Boolean, nullable=False, default=True, index=True)
    archivado_en = Column(DateTime, nullable=True)
    archivado_por = Column(String(100), nullable=True)


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
    tipo_objetivo = Column(String(40), nullable=True)
    costo_campania = Column(Float, nullable=True)
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)
    # Soft delete
    activo = Column(Boolean, nullable=False, default=True, index=True)
    archivado_en = Column(DateTime, nullable=True)
    archivado_por = Column(String(100), nullable=True)


class CrmAtribucionCampania(MAIN):
    __tablename__ = "crm_atribucion_campania"
    __table_args__ = (
        Index("ix_crm_atribucion_campania_tenant_campania", "tenant_id", "campania_id"),
        Index("ix_crm_atribucion_campania_tenant_contacto", "tenant_id", "contacto_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    campania_id = Column(Integer, ForeignKey("crm_campanias.id", ondelete="CASCADE"), nullable=False, index=True)
    contacto_id = Column(Integer, ForeignKey("crm_contactos.id", ondelete="CASCADE"), nullable=False, index=True)
    oportunidad_id = Column(Integer, ForeignKey("crm_oportunidades.id", ondelete="SET NULL"), nullable=True, index=True)
    etapa_alcanzada = Column(String(30), nullable=True)
    convertido = Column(Boolean, nullable=False, default=False)
    monto_ganado = Column(Float, nullable=True)
    fecha_atribucion = Column(DateTime, nullable=False, default=datetime.utcnow)


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


# ── Fase 6: Nuevas entidades ──────────────────────────────────────────────────

class CrmProductoInteres(MAIN):
    """Productos o servicios de interés declarados por contacto/oportunidad."""
    __tablename__ = "crm_productos_interes"
    __table_args__ = (
        Index("ix_crm_productos_interes_tenant_contacto", "tenant_id", "contacto_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    contacto_id = Column(Integer, ForeignKey("crm_contactos.id", ondelete="CASCADE"), nullable=False, index=True)
    oportunidad_id = Column(Integer, ForeignKey("crm_oportunidades.id", ondelete="SET NULL"), nullable=True, index=True)
    nombre = Column(String(200), nullable=False)
    categoria = Column(String(100), nullable=False, default="")
    notas = Column(Text, nullable=True)
    creado_por = Column(String(100), nullable=False, default="")
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)


class CrmFuenteDetallada(MAIN):
    """Catálogo enriquecido de fuentes de origen de leads."""
    __tablename__ = "crm_fuentes_detalladas"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    fuente_principal = Column(String(50), nullable=False)   # e.g. "digital"
    fuente_detalle = Column(String(120), nullable=False)     # e.g. "Google Ads - campaña verano"
    activa = Column(Boolean, nullable=False, default=True)
    descripcion = Column(Text, nullable=True)
    creado_por = Column(String(100), nullable=False, default="")
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)


class CrmSegmento(MAIN):
    """Segmentos de contactos (calculados o manuales)."""
    __tablename__ = "crm_segmentos"
    __table_args__ = (
        Index("ix_crm_segmentos_tenant", "tenant_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    filtros_json = Column(JSON, nullable=True)   # criterios de filtrado serializados
    es_dinamico = Column(Boolean, nullable=False, default=True)
    total_contactos = Column(Integer, nullable=False, default=0)
    creado_por = Column(String(100), nullable=False, default="")
    actualizado_por = Column(String(100), nullable=False, default="")
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)
    actualizado_en = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class CrmObjetivoComercial(MAIN):
    """Metas de ventas por ejecutivo / sucursal / periodo."""
    __tablename__ = "crm_objetivos_comerciales"
    __table_args__ = (
        Index("ix_crm_objetivos_tenant_periodo", "tenant_id", "periodo"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    periodo = Column(String(7), nullable=False)          # YYYY-MM
    ejecutivo = Column(String(100), nullable=False, default="")
    sucursal = Column(String(100), nullable=False, default="")
    meta_monto = Column(Float, nullable=False, default=0.0)
    meta_cierres = Column(Integer, nullable=False, default=0)
    logrado_monto = Column(Float, nullable=False, default=0.0)
    logrado_cierres = Column(Integer, nullable=False, default=0)
    creado_por = Column(String(100), nullable=False, default="")
    actualizado_por = Column(String(100), nullable=False, default="")
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)
    actualizado_en = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class CrmNotificacion(MAIN):
    """Alertas internas entregadas a usuarios del CRM."""
    __tablename__ = "crm_notificaciones"
    __table_args__ = (
        Index("ix_crm_notificaciones_tenant_usuario", "tenant_id", "usuario_dest"),
        Index("ix_crm_notificaciones_leida", "tenant_id", "leida"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    usuario_dest = Column(String(100), nullable=False, index=True)
    tipo = Column(String(60), nullable=False, index=True)
    referencia_id = Column(Integer, nullable=True)
    referencia_tipo = Column(String(50), nullable=True)   # "oportunidad" | "actividad" | …
    mensaje = Column(String(500), nullable=False)
    leida = Column(Boolean, nullable=False, default=False, index=True)
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class CrmReglaAutomatizacion(MAIN):
    """Reglas configurables de automatización (trigger → acción)."""
    __tablename__ = "crm_reglas_automatizacion"
    __table_args__ = (
        Index("ix_crm_reglas_tenant_activa", "tenant_id", "activa"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    nombre = Column(String(200), nullable=False)
    evento_trigger = Column(String(100), nullable=False, index=True)
    condicion_json = Column(JSON, nullable=True)
    accion_tipo = Column(String(100), nullable=False)
    accion_params_json = Column(JSON, nullable=True)
    activa = Column(Boolean, nullable=False, default=True, index=True)
    creado_por = Column(String(100), nullable=False, default="")
    actualizado_por = Column(String(100), nullable=False, default="")
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)
    actualizado_en = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class CrmAdjunto(MAIN):
    """Archivos adjuntos ligados a oportunidades o contactos."""
    __tablename__ = "crm_adjuntos"
    __table_args__ = (
        Index("ix_crm_adjuntos_tenant_referencia", "tenant_id", "referencia_tipo", "referencia_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    referencia_tipo = Column(String(50), nullable=False)   # "oportunidad" | "contacto" | "actividad"
    referencia_id = Column(Integer, nullable=False, index=True)
    nombre_archivo = Column(String(255), nullable=False)
    ruta = Column(String(500), nullable=False)             # path relativo o URL
    mime_type = Column(String(100), nullable=True)
    tamano_bytes = Column(Integer, nullable=True)
    creado_por = Column(String(100), nullable=False, default="")
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)


class CrmRecordatorio(MAIN):
    """Recordatorios visibles en UI ligados a entidades CRM."""
    __tablename__ = "crm_recordatorios"
    __table_args__ = (
        Index("ix_crm_recordatorios_tenant_usuario", "tenant_id", "usuario"),
        Index("ix_crm_recordatorios_fecha", "tenant_id", "fecha_recordatorio"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    usuario = Column(String(100), nullable=False, index=True)
    referencia_tipo = Column(String(50), nullable=True)
    referencia_id = Column(Integer, nullable=True)
    mensaje = Column(String(500), nullable=False)
    fecha_recordatorio = Column(DateTime, nullable=False, index=True)
    completado = Column(Boolean, nullable=False, default=False)
    creado_por = Column(String(100), nullable=False, default="")
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)


class CrmMetricaDiaria(MAIN):
    """Snapshot diario de KPIs para histórico y tendencias."""
    __tablename__ = "crm_metricas_diarias"
    __table_args__ = (
        UniqueConstraint("tenant_id", "fecha", name="uq_crm_metricas_tenant_fecha"),
        Index("ix_crm_metricas_tenant_fecha", "tenant_id", "fecha"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    fecha = Column(Date, nullable=False, index=True)
    total_contactos = Column(Integer, nullable=False, default=0)
    total_oportunidades_abiertas = Column(Integer, nullable=False, default=0)
    total_pipeline_monto = Column(Float, nullable=False, default=0.0)
    total_ganado_mes = Column(Float, nullable=False, default=0.0)
    actividades_pendientes = Column(Integer, nullable=False, default=0)
    actividades_vencidas = Column(Integer, nullable=False, default=0)
    tasa_ganancia = Column(Float, nullable=False, default=0.0)
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)


class CrmSnapshotPipeline(MAIN):
    """Foto del estado del embudo en momentos clave."""
    __tablename__ = "crm_snapshot_pipeline"
    __table_args__ = (
        Index("ix_crm_snapshot_tenant_fecha", "tenant_id", "fecha"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    fecha = Column(DateTime, nullable=False, index=True)
    etapa = Column(String(30), nullable=False)
    total = Column(Integer, nullable=False, default=0)
    monto = Column(Float, nullable=False, default=0.0)
    ejecutivo = Column(String(100), nullable=False, default="")
    sucursal = Column(String(100), nullable=False, default="")
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)


class CrmConversacion(MAIN):
    """Conversación interna vinculada a una entidad CRM (contacto, oportunidad, actividad o campaña)."""
    __tablename__ = "crm_conversacion"
    __table_args__ = (
        Index("ix_crm_conv_tenant_ref", "tenant_id", "ref_tipo", "ref_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    ref_tipo = Column(String(30), nullable=False)          # contacto | oportunidad | actividad | campania
    ref_id = Column(Integer, nullable=False, index=True)
    asunto = Column(String(255), nullable=False, default="")
    estado = Column(String(20), nullable=False, default="abierta")  # abierta | cerrada | archivada
    actor = Column(String(100), nullable=True)             # quien abrió la conversación
    multitienda_uuid = Column(String(100), nullable=True)  # UUID externo si se vincula con Multitienda Messaging
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)
    actualizado_en = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    mensajes = relationship("CrmMensaje", back_populates="conversacion", cascade="all, delete-orphan")


class CrmMensaje(MAIN):
    """Mensaje dentro de una CrmConversacion."""
    __tablename__ = "crm_mensaje"
    __table_args__ = (
        Index("ix_crm_mensaje_conv", "conversacion_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    conversacion_id = Column(Integer, ForeignKey("crm_conversacion.id"), nullable=False)
    actor = Column(String(100), nullable=False)
    contenido = Column(Text, nullable=False)
    tipo = Column(String(30), nullable=False, default="comentario")  # comentario | apoyo | validacion | cierre
    leido = Column(Boolean, nullable=False, default=False)
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)

    conversacion = relationship("CrmConversacion", back_populates="mensajes")
