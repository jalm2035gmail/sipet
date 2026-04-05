from __future__ import annotations

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import relationship

from fastapi_modulo.core.db import MAIN


class RepZona(MAIN):
    __tablename__ = 'rep_zona'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    code = Column(String(60), unique=True, nullable=False, index=True)
    description = Column(Text, default='')
    ciudad = Column(String(120), default='')
    radio_km = Column(Float, default=5.0)
    lat_centro = Column(Float, nullable=True)   # centro geográfico de la zona
    lng_centro = Column(Float, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    repartidores = relationship('RepRepartidor', back_populates='zona')
    entregas = relationship('RepEntrega', back_populates='zona')


class RepVehiculo(MAIN):
    __tablename__ = 'rep_vehiculo'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    tipo = Column(String(50), default='moto', index=True)
    placa = Column(String(50), default='', index=True)
    capacidad_kg = Column(Float, default=20.0)
    capacidad_pedidos = Column(Integer, default=5)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    repartidores = relationship('RepRepartidor', back_populates='vehiculo')


class RepRepartidor(MAIN):
    __tablename__ = 'rep_repartidor'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    codigo = Column(String(60), nullable=False, unique=True, index=True)
    telefono = Column(String(50), default='')
    email = Column(String(255), default='')
    tipo = Column(String(40), default='interno', index=True)
    state = Column(String(30), default='available', index=True)
    activo = Column(Boolean, default=True)
    zona_id = Column(Integer, ForeignKey('rep_zona.id'), nullable=True)
    vehiculo_id = Column(Integer, ForeignKey('rep_vehiculo.id'), nullable=True)
    negocio = Column(String(255), default='')
    sucursal = Column(String(255), default='')
    sipet_username = Column(String(120), nullable=True, index=True, default='')
    tarifa_base = Column(Numeric(12, 2), default=0)
    bono_por_entrega = Column(Numeric(12, 2), default=0)
    meta_entregas_diarias = Column(Integer, default=10)
    max_entregas_simultaneas = Column(Integer, default=5)
    notas = Column(Text, default='')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    zona = relationship('RepZona', back_populates='repartidores')
    vehiculo = relationship('RepVehiculo', back_populates='repartidores')
    entregas = relationship('RepEntrega', back_populates='repartidor')
    incidencias = relationship('RepIncidencia', back_populates='repartidor')
    liquidaciones = relationship('RepLiquidacion', back_populates='repartidor')
    posicion = relationship('RepRepartidorPosicion', back_populates='repartidor', uselist=False)


class RepEntrega(MAIN):
    __tablename__ = 'rep_entrega'

    id = Column(Integer, primary_key=True, autoincrement=True)
    folio = Column(String(80), nullable=False, unique=True, index=True)
    referencia_externa = Column(String(120), default='', index=True)
    cliente_nombre = Column(String(255), nullable=False)
    cliente_telefono = Column(String(50), default='')
    origen = Column(String(255), default='')
    destino = Column(String(255), nullable=False)
    lat_origen = Column(Float, nullable=True)
    lng_origen = Column(Float, nullable=True)
    lat_destino = Column(Float, nullable=True)
    lng_destino = Column(Float, nullable=True)
    descripcion = Column(Text, default='')
    prioridad = Column(String(20), default='normal', index=True)
    state = Column(String(30), default='draft', index=True)
    costo_envio = Column(Numeric(12, 2), default=0)
    distancia_km = Column(Float, default=0.0)
    tiempo_estimado_min = Column(Integer, default=0)
    tiempo_real_min = Column(Integer, default=0)
    fecha_programada = Column(DateTime, nullable=False)
    fecha_asignacion = Column(DateTime, nullable=True)
    fecha_recoleccion = Column(DateTime, nullable=True)
    fecha_entrega = Column(DateTime, nullable=True)
    evidencia_entrega = Column(Text, default='')
    motivo_cancelacion = Column(Text, default='')
    zona_id = Column(Integer, ForeignKey('rep_zona.id'), nullable=True)
    repartidor_id = Column(Integer, ForeignKey('rep_repartidor.id'), nullable=True)
    liquidable = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    zona = relationship('RepZona', back_populates='entregas')
    repartidor = relationship('RepRepartidor', back_populates='entregas')
    incidencias = relationship('RepIncidencia', back_populates='entrega', cascade='all, delete-orphan')
    lineas_liquidacion = relationship('RepLiquidacionLinea', back_populates='entrega')
    logs = relationship('RepEntregaLog', back_populates='entrega', cascade='all, delete-orphan')


class RepIncidencia(MAIN):
    __tablename__ = 'rep_incidencia'

    id = Column(Integer, primary_key=True, autoincrement=True)
    entrega_id = Column(Integer, ForeignKey('rep_entrega.id'), nullable=False)
    repartidor_id = Column(Integer, ForeignKey('rep_repartidor.id'), nullable=True)
    tipo = Column(String(40), default='general', index=True)
    severidad = Column(String(20), default='media', index=True)
    descripcion = Column(Text, default='')
    resolucion = Column(Text, default='')
    state = Column(String(20), default='open', index=True)
    created_at = Column(DateTime, default=func.now())
    resolved_at = Column(DateTime, nullable=True)

    entrega = relationship('RepEntrega', back_populates='incidencias')
    repartidor = relationship('RepRepartidor', back_populates='incidencias')


class RepLiquidacion(MAIN):
    __tablename__ = 'rep_liquidacion'

    id = Column(Integer, primary_key=True, autoincrement=True)
    repartidor_id = Column(Integer, ForeignKey('rep_repartidor.id'), nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    total_entregas = Column(Integer, default=0)
    total_base = Column(Numeric(12, 2), default=0)
    total_bonos = Column(Numeric(12, 2), default=0)
    total_descuentos = Column(Numeric(12, 2), default=0)
    total_pagar = Column(Numeric(12, 2), default=0)
    state = Column(String(20), default='draft', index=True)
    notas = Column(Text, default='')
    fecha_aprobacion = Column(DateTime, nullable=True)
    fecha_pago = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())

    repartidor = relationship('RepRepartidor', back_populates='liquidaciones')
    lineas = relationship('RepLiquidacionLinea', back_populates='liquidacion', cascade='all, delete-orphan')


class RepLiquidacionLinea(MAIN):
    __tablename__ = 'rep_liquidacion_linea'

    id = Column(Integer, primary_key=True, autoincrement=True)
    liquidacion_id = Column(Integer, ForeignKey('rep_liquidacion.id'), nullable=False)
    entrega_id = Column(Integer, ForeignKey('rep_entrega.id'), nullable=False)
    monto_base = Column(Numeric(12, 2), default=0)
    bono = Column(Numeric(12, 2), default=0)
    descuento = Column(Numeric(12, 2), default=0)
    total = Column(Numeric(12, 2), default=0)

    liquidacion = relationship('RepLiquidacion', back_populates='lineas')
    entrega = relationship('RepEntrega', back_populates='lineas_liquidacion')


class RepEntregaLog(MAIN):
    __tablename__ = 'rep_entrega_log'

    id = Column(Integer, primary_key=True, autoincrement=True)
    entrega_id = Column(Integer, ForeignKey('rep_entrega.id'), nullable=False)
    tipo = Column(String(30), default='estado', index=True)  # estado | asignacion
    estado_anterior = Column(String(30), nullable=True)
    estado_nuevo = Column(String(30), nullable=True)
    repartidor_id = Column(Integer, ForeignKey('rep_repartidor.id'), nullable=True)
    notas = Column(Text, default='')
    created_at = Column(DateTime, default=func.now())

    entrega = relationship('RepEntrega', back_populates='logs')


class RepRepartidorPosicion(MAIN):
    """Última posición conocida del repartidor (upsert por repartidor_id)."""
    __tablename__ = 'rep_repartidor_posicion'

    id = Column(Integer, primary_key=True, autoincrement=True)
    repartidor_id = Column(Integer, ForeignKey('rep_repartidor.id'), nullable=False, unique=True, index=True)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    precision_m = Column(Float, nullable=True)   # precisión GPS en metros
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    repartidor = relationship('RepRepartidor', back_populates='posicion')


class RepNotificacionLog(MAIN):
    __tablename__ = 'rep_notificacion_log'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tipo = Column(String(60), nullable=False, index=True)
    # entrega_asignada | repartidor_en_camino | entrega_confirmada |
    # nueva_asignacion | recordatorio_pendientes | entrega_vencida_sin_asignar |
    # entrega_asignada_sin_recoleccion | zona_sin_repartidores_disponibles
    canal = Column(String(30), default='sistema', index=True)
    # whatsapp | email | whatsapp+email | sistema
    destinatario = Column(String(255), default='')
    mensaje = Column(Text, default='')
    entrega_id = Column(Integer, ForeignKey('rep_entrega.id'), nullable=True, index=True)
    repartidor_id = Column(Integer, ForeignKey('rep_repartidor.id'), nullable=True, index=True)
    estado = Column(String(20), default='pendiente', index=True)
    # pendiente | enviado | registrada | error
    error_msg = Column(Text, default='')
    created_at = Column(DateTime, default=func.now())


def ensure_repartidores_schema(bind=None) -> None:
    from fastapi_modulo.core.db import get_current_engine

    target = bind or get_current_engine()
    RepZona.__table__.create(bind=target, checkfirst=True)
    RepVehiculo.__table__.create(bind=target, checkfirst=True)
    RepRepartidor.__table__.create(bind=target, checkfirst=True)
    RepEntrega.__table__.create(bind=target, checkfirst=True)
    RepIncidencia.__table__.create(bind=target, checkfirst=True)
    RepLiquidacion.__table__.create(bind=target, checkfirst=True)
    RepLiquidacionLinea.__table__.create(bind=target, checkfirst=True)
    RepEntregaLog.__table__.create(bind=target, checkfirst=True)
    RepRepartidorPosicion.__table__.create(bind=target, checkfirst=True)
    RepNotificacionLog.__table__.create(bind=target, checkfirst=True)
