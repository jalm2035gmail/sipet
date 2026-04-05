from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class ZonaCreate(BaseModel):
    name: str
    code: str
    description: str = ''
    ciudad: str = ''
    radio_km: float = 5.0
    lat_centro: Optional[float] = None
    lng_centro: Optional[float] = None
    active: bool = True


class ZonaRead(BaseModel):
    id: int
    name: str
    code: str
    description: str
    ciudad: str
    radio_km: float
    lat_centro: Optional[float]
    lng_centro: Optional[float]
    active: bool

    class Config:
        from_attributes = True


class VehiculoCreate(BaseModel):
    name: str
    tipo: str = 'moto'
    placa: str = ''
    capacidad_kg: float = 20.0
    capacidad_pedidos: int = 5
    activo: bool = True


class VehiculoRead(BaseModel):
    id: int
    name: str
    tipo: str
    placa: str
    capacidad_kg: float
    capacidad_pedidos: int
    activo: bool

    class Config:
        from_attributes = True


class RepartidorCreate(BaseModel):
    name: str
    codigo: str
    telefono: str = ''
    email: str = ''
    tipo: str = 'interno'
    state: str = 'available'
    activo: bool = True
    zona_id: Optional[int] = None
    vehiculo_id: Optional[int] = None
    negocio: str = ''
    sucursal: str = ''
    sipet_username: str = ''
    tarifa_base: Decimal = Decimal('0')
    bono_por_entrega: Decimal = Decimal('0')
    meta_entregas_diarias: int = 10
    max_entregas_simultaneas: int = 5
    notas: str = ''


class RepartidorUpdate(BaseModel):
    name: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    tipo: Optional[str] = None
    state: Optional[str] = None
    activo: Optional[bool] = None
    zona_id: Optional[int] = None
    vehiculo_id: Optional[int] = None
    negocio: Optional[str] = None
    sucursal: Optional[str] = None
    sipet_username: Optional[str] = None
    tarifa_base: Optional[Decimal] = None
    bono_por_entrega: Optional[Decimal] = None
    meta_entregas_diarias: Optional[int] = None
    max_entregas_simultaneas: Optional[int] = None
    notas: Optional[str] = None


class RepartidorRead(BaseModel):
    id: int
    name: str
    codigo: str
    telefono: str
    email: str
    tipo: str
    state: str
    activo: bool
    zona_id: Optional[int]
    vehiculo_id: Optional[int]
    negocio: str
    sucursal: str
    sipet_username: str
    tarifa_base: Decimal
    bono_por_entrega: Decimal
    meta_entregas_diarias: int
    max_entregas_simultaneas: int
    notas: str

    class Config:
        from_attributes = True


class EntregaCreate(BaseModel):
    referencia_externa: str = ''
    cliente_nombre: str
    cliente_telefono: str = ''
    origen: str = ''
    destino: str
    lat_origen: Optional[float] = None
    lng_origen: Optional[float] = None
    lat_destino: Optional[float] = None
    lng_destino: Optional[float] = None
    descripcion: str = ''
    prioridad: str = 'normal'
    costo_envio: Decimal = Decimal('0')
    distancia_km: float = 0.0
    tiempo_estimado_min: int = 0
    fecha_programada: datetime
    zona_id: Optional[int] = None
    repartidor_id: Optional[int] = None
    liquidable: bool = True


class EntregaRead(BaseModel):
    id: int
    folio: str
    referencia_externa: str
    cliente_nombre: str
    cliente_telefono: str
    origen: str
    destino: str
    lat_origen: Optional[float]
    lng_origen: Optional[float]
    lat_destino: Optional[float]
    lng_destino: Optional[float]
    descripcion: str
    prioridad: str
    state: str
    costo_envio: Decimal
    distancia_km: float
    tiempo_estimado_min: int
    tiempo_real_min: int
    fecha_programada: datetime
    fecha_asignacion: Optional[datetime]
    fecha_recoleccion: Optional[datetime]
    fecha_entrega: Optional[datetime]
    evidencia_entrega: str
    motivo_cancelacion: str
    zona_id: Optional[int]
    repartidor_id: Optional[int]
    liquidable: bool

    class Config:
        from_attributes = True


class AsignarEntregaInput(BaseModel):
    repartidor_id: int


class ActualizarEstadoEntregaInput(BaseModel):
    state: str
    evidencia_entrega: str = ''
    motivo_cancelacion: str = ''
    tiempo_real_min: Optional[int] = None


class IncidenciaCreate(BaseModel):
    entrega_id: int
    repartidor_id: Optional[int] = None
    tipo: str = 'general'
    severidad: str = 'media'
    descripcion: str = Field(min_length=3)
    resolucion: str = ''
    state: str = 'open'


class IncidenciaRead(BaseModel):
    id: int
    entrega_id: int
    repartidor_id: Optional[int]
    tipo: str
    severidad: str
    descripcion: str
    resolucion: str
    state: str

    class Config:
        from_attributes = True


class GenerarLiquidacionInput(BaseModel):
    repartidor_id: int
    fecha_inicio: date
    fecha_fin: date
    descuentos: Decimal = Decimal('0')
    notas: str = ''


class LiquidacionRead(BaseModel):
    id: int
    repartidor_id: int
    fecha_inicio: date
    fecha_fin: date
    total_entregas: int
    total_base: Decimal
    total_bonos: Decimal
    total_descuentos: Decimal
    total_pagar: Decimal
    state: str
    notas: str
    fecha_aprobacion: Optional[datetime] = None
    fecha_pago: Optional[datetime] = None

    class Config:
        from_attributes = True


class ActualizarLiquidacionEstadoInput(BaseModel):
    state: str  # approved | paid
    notas: str = ''


class EntregaLogRead(BaseModel):
    id: int
    entrega_id: int
    tipo: str
    estado_anterior: Optional[str]
    estado_nuevo: Optional[str]
    repartidor_id: Optional[int]
    notas: str
    created_at: datetime

    class Config:
        from_attributes = True


class NotificacionLogRead(BaseModel):
    id: int
    tipo: str
    canal: str
    destinatario: str
    mensaje: str
    entrega_id: Optional[int]
    repartidor_id: Optional[int]
    estado: str
    error_msg: str
    created_at: datetime

    class Config:
        from_attributes = True


class AlertaOperativa(BaseModel):
    tipo: str
    severidad: str
    mensaje: str
    entrega_id: Optional[int] = None
    folio: Optional[str] = None
    repartidor_id: Optional[int] = None
    zona_id: Optional[int] = None
    zona_code: Optional[str] = None
    zona_name: Optional[str] = None
    minutos_vencida: Optional[int] = None
    minutos_sin_recoleccion: Optional[int] = None
    fecha_programada: Optional[str] = None


# ---------------------------------------------------------------------------
# FASE 7 — GEOLOCALIZACIÓN
# ---------------------------------------------------------------------------

class PosicionUpdate(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    precision_m: Optional[float] = None


class PosicionRead(BaseModel):
    repartidor_id: int
    lat: float
    lng: float
    precision_m: Optional[float]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class EntregaMapaData(BaseModel):
    id: int
    folio: str
    state: str
    prioridad: str
    cliente_nombre: str
    destino: str
    lat_origen: Optional[float]
    lng_origen: Optional[float]
    lat_destino: Optional[float]
    lng_destino: Optional[float]
    repartidor_id: Optional[int]
    repartidor_nombre: Optional[str]
    zona_id: Optional[int]
    zona_name: Optional[str]


class RepartidorMapaData(BaseModel):
    id: int
    nombre: str
    codigo: str
    state: str
    lat: Optional[float]
    lng: Optional[float]
    precision_m: Optional[float]
    posicion_updated_at: Optional[datetime]
    zona_id: Optional[int]
    zona_name: Optional[str]
    entregas_activas: int
