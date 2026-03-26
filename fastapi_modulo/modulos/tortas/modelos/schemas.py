from __future__ import annotations
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel


# ── Categoría ─────────────────────────────────────────────────────────────────

class CategoriaCreate(BaseModel):
    name: str
    descripcion: str = ""


class CategoriaRead(BaseModel):
    id: int
    name: str
    descripcion: str
    active: bool

    class Config:
        from_attributes = True


# ── Alérgeno ──────────────────────────────────────────────────────────────────

class AlergenoCreate(BaseModel):
    name: str
    codigo: str = ""
    descripcion: str = ""
    icono: str = "fa-exclamation-triangle"
    color: str = "#ff6b6b"
    advertencia: str = ""
    sequence: int = 10


class AlergenoRead(BaseModel):
    id: int
    name: str
    codigo: str
    icono: str
    color: str
    activo: bool

    class Config:
        from_attributes = True


# ── Tipo de Pan ───────────────────────────────────────────────────────────────

class TipoPanCreate(BaseModel):
    nombre: str
    descripcion: str = ""
    precio_extra: float = 0.0
    sequence: int = 10


class TipoPanRead(BaseModel):
    id: int
    nombre: str
    descripcion: str
    precio_extra: float
    disponible: bool
    activo: bool

    class Config:
        from_attributes = True


class TipoPanUpdate(BaseModel):
    disponible: Optional[bool] = None
    precio_extra: Optional[float] = None
    activo: Optional[bool] = None


# ── Topping ───────────────────────────────────────────────────────────────────

class ToppingCreate(BaseModel):
    name: str
    descripcion: str = ""
    tipo: str = "fijo"  # incluido, fijo, cantidad
    precio: float = 0.0
    unidad: str = ""
    maximo: int = 0
    sort_order: int = 10


class ToppingRead(BaseModel):
    id: int
    name: str
    descripcion: str
    tipo: str
    precio: float
    unidad: str
    maximo: int
    active: bool
    sort_order: int

    class Config:
        from_attributes = True


# ── Torta ─────────────────────────────────────────────────────────────────────

class TortaCreate(BaseModel):
    name: str
    descripcion: str = ""
    precio: float
    categoria_id: Optional[int] = None
    ingredientes: str = ""
    min_toppings: int = 0
    max_toppings: int = 0
    requiere_tipo_pan: bool = False
    tipo_pan_predeterminado_id: Optional[int] = None
    calorias: int = 0
    proteinas: float = 0.0
    carbohidratos: float = 0.0
    grasas: float = 0.0


class TortaUpdate(BaseModel):
    name: Optional[str] = None
    precio: Optional[float] = None
    active: Optional[bool] = None
    descripcion: Optional[str] = None
    categoria_id: Optional[int] = None


class TortaRead(BaseModel):
    id: int
    name: str
    descripcion: str
    precio: float
    categoria_id: Optional[int]
    ingredientes: str
    active: bool
    min_toppings: int
    max_toppings: int
    requiere_tipo_pan: bool
    tipo_pan_predeterminado_id: Optional[int]
    calorias: int
    proteinas: float
    carbohidratos: float
    grasas: float

    class Config:
        from_attributes = True


# ── Zona de entrega ───────────────────────────────────────────────────────────

class ZonaEntregaCreate(BaseModel):
    name: str
    descripcion: str = ""
    costo_envio: float = 0.0
    envio_gratis_desde: float = 0.0
    monto_minimo_pedido: float = 0.0
    tiempo_entrega_minutos: int = 45
    acepta_pedidos: bool = True
    mensaje_no_disponible: str = "Lo sentimos, no hacemos entregas a esta zona."


class ZonaEntregaRead(BaseModel):
    id: int
    name: str
    descripcion: str
    costo_envio: float
    envio_gratis_desde: float
    monto_minimo_pedido: float
    tiempo_entrega_minutos: int
    acepta_pedidos: bool
    active: bool

    class Config:
        from_attributes = True


class ZonaEntregaUpdate(BaseModel):
    acepta_pedidos: Optional[bool] = None
    costo_envio: Optional[float] = None
    tiempo_entrega_minutos: Optional[int] = None


# ── Forma de pago ─────────────────────────────────────────────────────────────

class FormaPagoCreate(BaseModel):
    name: str
    codigo: str = "efectivo"
    requiere_referencia: bool = False
    aplica_comision: bool = False
    porcentaje_comision: float = 0.0
    afecta_caja: bool = True
    icono: str = "fa-money-bill"
    sequence: int = 10


class FormaPagoRead(BaseModel):
    id: int
    name: str
    codigo: str
    requiere_referencia: bool
    aplica_comision: bool
    porcentaje_comision: float
    afecta_caja: bool
    icono: str
    active: bool

    class Config:
        from_attributes = True


# ── Cupón ─────────────────────────────────────────────────────────────────────

class CuponCreate(BaseModel):
    name: str
    codigo: str
    tipo_descuento: str = "porcentaje"  # porcentaje, monto_fijo
    valor_descuento: float
    descuento_maximo: float = 0.0
    fecha_inicio: date
    fecha_fin: date
    monto_minimo: float = 0.0
    uso_maximo: int = 0
    uso_maximo_cliente: int = 1
    aplica_a: str = "todos"
    descripcion: str = ""


class CuponRead(BaseModel):
    id: int
    name: str
    codigo: str
    tipo_descuento: str
    valor_descuento: float
    descuento_maximo: float
    fecha_inicio: date
    fecha_fin: date
    monto_minimo: float
    uso_maximo: int
    aplica_a: str
    active: bool

    class Config:
        from_attributes = True


class CuponValidarRequest(BaseModel):
    codigo: str
    subtotal: float


class CuponValidarResponse(BaseModel):
    valido: bool
    mensaje: str
    monto_descuento: float


# ── Línea de topping (para pedido) ────────────────────────────────────────────

class LineaToppingCreate(BaseModel):
    topping_id: int
    cantidad: int = 1
    precio_unitario: float = 0.0


# ── Línea de pedido ───────────────────────────────────────────────────────────

class LineaPedidoCreate(BaseModel):
    torta_id: int
    cantidad: int = 1
    precio_unitario: float
    tipo_pan_id: Optional[int] = None
    precio_pan: float = 0.0
    descripcion: str = ""
    notas: str = ""
    toppings: List[LineaToppingCreate] = []


class LineaPedidoRead(BaseModel):
    id: int
    torta_id: int
    cantidad: int
    precio_unitario: float
    tipo_pan_id: Optional[int]
    precio_pan: float
    notas: str

    class Config:
        from_attributes = True


# ── Pedido ────────────────────────────────────────────────────────────────────

class PedidoCreate(BaseModel):
    nombre_cliente: str = ""
    telefono: str = ""
    email: str = ""
    tipo_pedido: str = "mostrador"  # mostrador, para_llevar, domicilio
    zona_entrega_id: Optional[int] = None
    costo_envio: float = 0.0
    direccion_entrega: str = ""
    colonia: str = ""
    referencias: str = ""
    prioridad: str = "normal"
    descuento: float = 0.0
    impuesto: float = 0.0
    notas: str = ""
    notas_cocina: str = ""
    codigo_cupon: str = ""
    usuario: str = ""
    lineas: List[LineaPedidoCreate] = []


class PedidoUpdate(BaseModel):
    estado: Optional[str] = None
    prioridad: Optional[str] = None
    notas_cocina: Optional[str] = None
    ticket_impreso: Optional[bool] = None


class PedidoRead(BaseModel):
    id: int
    numero_pedido: str
    fecha_pedido: datetime
    nombre_cliente: str
    telefono: str
    tipo_pedido: str
    estado: str
    prioridad: str
    costo_envio: float
    descuento: float
    impuesto: float
    notas: str
    notas_cocina: str
    ticket_impreso: bool
    fecha_confirmacion: Optional[datetime]
    fecha_inicio_preparacion: Optional[datetime]
    fecha_listo: Optional[datetime]
    fecha_entregado: Optional[datetime]
    cupon_id: Optional[int]
    corte_caja_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Pago ──────────────────────────────────────────────────────────────────────

class PagoCreate(BaseModel):
    forma_pago_id: int
    monto: float
    referencia: str = ""
    notas: str = ""
    usuario: str = ""


class PagoRead(BaseModel):
    id: int
    pedido_id: int
    fecha: datetime
    forma_pago_id: int
    monto: float
    referencia: str
    cancelado: bool
    usuario: str

    class Config:
        from_attributes = True


# ── Propina ───────────────────────────────────────────────────────────────────

class PropinaCreate(BaseModel):
    monto: float
    tipo: str = "monto_fijo"
    porcentaje: float = 0.0
    notas: str = ""


# ── Corte de caja ─────────────────────────────────────────────────────────────

class CorteCajaCreate(BaseModel):
    monto_inicial: float = 0.0
    usuario_apertura: str = ""
    notas: str = ""


class CorteCajaCerrarRequest(BaseModel):
    efectivo_contado: float = 0.0
    usuario_cierre: str = ""
    total_gastos: float = 0.0
    total_retiros: float = 0.0
    notas: str = ""


class CorteCajaRead(BaseModel):
    id: int
    name: str
    fecha_inicio: datetime
    fecha_cierre: Optional[datetime]
    estado: str
    usuario_apertura: str
    monto_inicial: float
    efectivo_contado: float
    total_gastos: float
    total_retiros: float
    notas: str

    class Config:
        from_attributes = True


# ── Preorden ──────────────────────────────────────────────────────────────────

class LineaPreordenCreate(BaseModel):
    torta_id: int
    cantidad: int = 1
    precio_unitario: float
    notas: str = ""
    toppings: List[LineaToppingCreate] = []


class PreordenCreate(BaseModel):
    nombre_cliente: str
    telefono: str = ""
    email: str = ""
    fecha_entrega: date
    hora_entrega: str = "12:00"
    tipo_pedido: str = "para_llevar"
    direccion_entrega: str = ""
    zona_entrega_id: Optional[int] = None
    costo_envio: float = 0.0
    notas: str = ""
    lineas: List[LineaPreordenCreate] = []


class PreordenRead(BaseModel):
    id: int
    name: str
    nombre_cliente: str
    telefono: str
    fecha_entrega: date
    hora_entrega: str
    tipo_pedido: str
    state: str
    costo_envio: float
    notas: str
    recordatorio_enviado: bool
    pedido_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_pedidos: int
    por_estado: dict
    total_ventas_hoy: float
    pedidos_hoy: int
