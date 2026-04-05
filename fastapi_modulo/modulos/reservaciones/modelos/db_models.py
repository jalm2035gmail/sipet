from __future__ import annotations
from datetime import datetime
from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import relationship
from fastapi_modulo.core.db import MAIN


class ResEjecutivo(MAIN):
    __tablename__ = "res_ejecutivo"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), default="")
    phone = Column(String(50), default="")
    especialidad = Column(String(255), default="")
    disponible = Column(Boolean, default=True)
    active = Column(Boolean, default=True)
    codigo_pais = Column(String(10), default="+52")
    mensaje_whatsapp = Column(String(500), default="Se confirma su cita con ")
    semanas_a_mostrar = Column(Integer, default=2)
    tiempo_promedio_cita = Column(Integer, default=30)
    tiempo_descanso_sesiones = Column(Integer, default=0)
    notas = Column(Text, default="")
    # Descansos por día
    descanso_lunes = Column(Boolean, default=False)
    descanso_martes = Column(Boolean, default=False)
    descanso_miercoles = Column(Boolean, default=False)
    descanso_jueves = Column(Boolean, default=False)
    descanso_viernes = Column(Boolean, default=False)
    descanso_sabado = Column(Boolean, default=True)
    descanso_domingo = Column(Boolean, default=True)
    # Horas por día (float: 9.5 = 9:30)
    hora_inicial_lunes = Column(Float, default=9.0)
    hora_final_lunes = Column(Float, default=17.0)
    hora_inicial_martes = Column(Float, default=9.0)
    hora_final_martes = Column(Float, default=17.0)
    hora_inicial_miercoles = Column(Float, default=9.0)
    hora_final_miercoles = Column(Float, default=17.0)
    hora_inicial_jueves = Column(Float, default=9.0)
    hora_final_jueves = Column(Float, default=17.0)
    hora_inicial_viernes = Column(Float, default=9.0)
    hora_final_viernes = Column(Float, default=17.0)
    hora_inicial_sabado = Column(Float, default=9.0)
    hora_final_sabado = Column(Float, default=13.0)
    hora_inicial_domingo = Column(Float, default=0.0)
    hora_final_domingo = Column(Float, default=0.0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    citas = relationship("ResCita", back_populates="ejecutivo", cascade="all, delete-orphan")


class ResTipoCita(MAIN):
    __tablename__ = "res_tipo_cita"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    duracion_minutos = Column(Integer, default=30)
    color = Column(String(20), default="#1a6b3c")
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())


class ResCita(MAIN):
    __tablename__ = "res_cita"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, default="Nueva Cita")
    nombre_persona = Column(String(255), default="")
    celular_persona = Column(String(50), default="")
    email_persona = Column(String(255), default="")
    start_datetime = Column(DateTime, nullable=False, index=True)
    end_datetime = Column(DateTime, nullable=True)
    ejecutivo_id = Column(Integer, ForeignKey("res_ejecutivo.id"), nullable=True)
    tipo_id = Column(Integer, ForeignKey("res_tipo_cita.id"), nullable=True)
    state = Column(String(20), default="draft", index=True)
    source = Column(String(50), default="admin")
    notes = Column(Text, default="")
    confirmed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    cancellation_reason = Column(String(500), nullable=True)
    cancel_token = Column(String(64), nullable=True, unique=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    ejecutivo = relationship("ResEjecutivo", back_populates="citas")
    tipo = relationship("ResTipoCita", foreign_keys=[tipo_id])

    __table_args__ = (
        Index("ix_res_cita_ej_start", "ejecutivo_id", "start_datetime"),
        Index("ix_res_cita_ej_end",   "ejecutivo_id", "end_datetime"),
    )


class ResBloqueoAgenda(MAIN):
    """Bloqueo explícito de un tramo de tiempo en la agenda de un ejecutivo."""
    __tablename__ = "res_bloqueo_agenda"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ejecutivo_id = Column(Integer, ForeignKey("res_ejecutivo.id"), nullable=False, index=True)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    motivo = Column(String(500), default="")
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    ejecutivo = relationship("ResEjecutivo")


class ResExcepcionFecha(MAIN):
    """Fecha excluida globalmente o para un ejecutivo (feriados, vacaciones)."""
    __tablename__ = "res_excepcion_fecha"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ejecutivo_id = Column(Integer, ForeignKey("res_ejecutivo.id"), nullable=True, index=True)
    fecha = Column(Date, nullable=False, index=True)
    motivo = Column(String(500), default="")
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    ejecutivo = relationship("ResEjecutivo")


class ResHorarioSemanal(MAIN):
    """
    Franjas horarias por día de semana para un ejecutivo.
    Sobreescribe los campos hora_inicial_*/hora_final_* del ejecutivo
    cuando existen registros activos.
    """
    __tablename__ = "res_horario_semanal"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ejecutivo_id = Column(Integer, ForeignKey("res_ejecutivo.id"), nullable=False, index=True)
    dia_semana = Column(Integer, nullable=False)   # 0=lunes … 6=domingo
    hora_ini = Column(Float, nullable=False)
    hora_fin = Column(Float, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    ejecutivo = relationship("ResEjecutivo")


def ensure_reservaciones_schema(bind=None) -> None:
    from fastapi_modulo.core.db import get_current_engine
    target = bind or get_current_engine()
    ResEjecutivo.__table__.create(bind=target, checkfirst=True)
    ResTipoCita.__table__.create(bind=target, checkfirst=True)
    ResCita.__table__.create(bind=target, checkfirst=True)
    ResBloqueoAgenda.__table__.create(bind=target, checkfirst=True)
    ResExcepcionFecha.__table__.create(bind=target, checkfirst=True)
    ResHorarioSemanal.__table__.create(bind=target, checkfirst=True)
