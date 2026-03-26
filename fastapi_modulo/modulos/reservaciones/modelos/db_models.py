from __future__ import annotations
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, func
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
    duracion = Column(Float, default=1.0)
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
    start_datetime = Column(DateTime, nullable=False)
    ejecutivo_id = Column(Integer, ForeignKey("res_ejecutivo.id"), nullable=True)
    tipo_id = Column(Integer, ForeignKey("res_tipo_cita.id"), nullable=True)
    state = Column(String(20), default="draft", index=True)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    ejecutivo = relationship("ResEjecutivo", back_populates="citas")
    tipo = relationship("ResTipoCita", foreign_keys=[tipo_id])


def ensure_reservaciones_schema(bind=None) -> None:
    from fastapi_modulo.core.db import get_current_engine
    target = bind or get_current_engine()
    ResEjecutivo.__table__.create(bind=target, checkfirst=True)
    ResTipoCita.__table__.create(bind=target, checkfirst=True)
    ResCita.__table__.create(bind=target, checkfirst=True)
