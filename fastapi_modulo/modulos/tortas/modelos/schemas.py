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


# ── Base del producto ─────────────────────────────────────────────────────────
# Genérico: pan/telera (tortas), masa (pizza), arroz/bowl (sushi/ensaladas),
#           wrap/tortilla (burritos). El label se configura en TortasConcepto.

class BaseProductoCreate(BaseModel):
    nombre: str
    descripcion: str = ""
    tipo_base: str = "otro"  # pan, masa, arroz, wrap, tortilla, bowl, lechuga, otro
    precio_extra: float = 0.0
    sequence: int = 10


class BaseProductoRead(BaseModel):
    id: int
    nombre: str
    descripcion: str
    tipo_base: str
    precio_extra: float
    disponible: bool
    activo: bool

    class Config:
        from_attributes = True


class BaseProductoUpdate(BaseModel):
    disponible: Optional[bool] = None
    precio_extra: Optional[float] = None
    activo: Optional[bool] = None


# ── Topping / Modificador ─────────────────────────────────────────────────────

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


# ── Producto (Torta / Pizza / Burger / Roll / Bowl / etc.) ────────────────────

class TortaCreate(BaseModel):
    name: str
    descripcion: str = ""
    precio: float
    categoria_id: Optional[int] = None
    ingredientes: str = ""
    min_toppings: int = 0
    max_toppings: int = 0
    requiere_base: bool = False
    base_predeterminada_id: Optional[int] = None
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
    requiere_base: Optional[bool] = None
    base_predeterminada_id: Optional[int] = None


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
    requiere_base: bool
    base_predeterminada_id: Optional[int]
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


# ── Canal de venta ────────────────────────────────────────────────────────────



# ── Fase 2: Variantes ──────────────────────────────────────────────────────────
class VarianteCreate(BaseModel):
    nombre: str
    descripcion: str = ""
    precio_extra: float = 0.0
    activo: bool = True
    disponible: bool = True
    sequence: int = 10


class VarianteRead(BaseModel):
    id: int
    producto_id: int
    nombre: str
    descripcion: str = ""
    precio_extra: float = 0.0
    activo: bool
    disponible: bool
    sequence: int

    model_config = ConfigDict(from_attributes=True)


# ── Fase 2: Grupos de Modificadores ───────────────────────────────────────────
class OpcionModificadorCreate(BaseModel):
    name: str
    descripcion: str = ""
    precio: float = 0.0
    tipo: str = "extra"          # incluido | extra | removible | sustitucion
    activo: bool = True
    disponible: bool = True
    sequence: int = 10
    maximo_cantidad: int = 1
    instruccion_cocina: str = ""


class OpcionModificadorRead(BaseModel):
    id: int
    grupo_id: int
    name: str
    descripcion: str = ""
    precio: float
    tipo: str
    activo: bool
    disponible: bool
    sequence: int
    maximo_cantidad: int
    instruccion_cocina: str = ""

    model_config = ConfigDict(from_attributes=True)


class GrupoModificadorCreate(BaseModel):
    name: str
    descripcion: str = ""
    tipo_seleccion: str = "multiple"   # unico | multiple | cantidad
    obligatorio: bool = False
    minimo: int = 0
    maximo: int = 0
    activo: bool = True
    sequence: int = 10


class GrupoModificadorRead(BaseModel):
    id: int
    name: str
    descripcion: str = ""
    tipo_seleccion: str
    obligatorio: bool
    minimo: int
    maximo: int
    activo: bool
    sequence: int
    opciones: List["OpcionModificadorRead"] = []

    model_config = ConfigDict(from_attributes=True)


# ── Fase 2: Selección de modificadores en líneas ───────────────────────────────
class LineaModificadorCreate(BaseModel):
    opcion_id: int
    cantidad: int = 1
    precio_unitario: float = 0.0


class LineaModificadorRead(BaseModel):
    id: int
    opcion_id: int
    cantidad: int
    precio_unitario: float

    model_config = ConfigDict(from_attributes=True)


# ── Fase 3: Clientes y Direcciones ────────────────────────────────────────────

class DireccionClienteCreate(BaseModel):
    alias: str = ""
    calle: str = ""
    numero_exterior: str = ""
    numero_interior: str = ""
    colonia: str = ""
    ciudad: str = ""
    estado_geografico: str = ""
    codigo_postal: str = ""
    referencias: str = ""
    lat: Optional[float] = None
    lng: Optional[float] = None
    predeterminada: bool = False
    activa: bool = True


class DireccionClienteRead(BaseModel):
    id: int
    cliente_id: int
    alias: str = ""
    calle: str = ""
    numero_exterior: str = ""
    numero_interior: str = ""
    colonia: str = ""
    ciudad: str = ""
    estado_geografico: str = ""
    codigo_postal: str = ""
    referencias: str = ""
    lat: Optional[float] = None
    lng: Optional[float] = None
    predeterminada: bool
    activa: bool

    model_config = ConfigDict(from_attributes=True)


class ClienteCreate(BaseModel):
    nombre: str
    telefono: str = ""
    email: str = ""
    fecha_nacimiento: Optional[str] = None
    notas: str = ""


class ClienteUpdate(BaseModel):
    nombre: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    fecha_nacimiento: Optional[str] = None
    notas: Optional[str] = None
    activo: Optional[bool] = None


class ClienteRead(BaseModel):
    id: int
    nombre: str
    telefono: str = ""
    email: str = ""
    notas: str = ""
    activo: bool
    direcciones: List["DireccionClienteRead"] = []

    model_config = ConfigDict(from_attributes=True)



# ── Fase 4: Plantillas y mensajes ─────────────────────────────────────────────

class PlantillaMensajeCreate(BaseModel):
    name: str
    tipo: str = "confirmacion"   # confirmacion|seguimiento|listo|en_reparto|entregado|cancelado|otro
    canal: str = "whatsapp"      # whatsapp|sms|telefono|todos
    cuerpo: str
    activo: bool = True


class PlantillaMensajeRead(BaseModel):
    id: int
    name: str
    tipo: str
    canal: str
    cuerpo: str
    activo: bool

    model_config = ConfigDict(from_attributes=True)


class MensajePedidoCreate(BaseModel):
    pedido_id: int
    direccion: str = "enviado"      # enviado | recibido
    canal: str = "whatsapp"         # whatsapp | sms | telefono | email | sistema
    plantilla_id: Optional[int] = None
    cuerpo: str
    referencia_externa: str = ""
    enviado_por: str = ""


class MensajePedidoRead(BaseModel):
    id: int
    pedido_id: int
    direccion: str
    canal: str
    plantilla_id: Optional[int] = None
    cuerpo: str
    estado: str
    referencia_externa: str = ""
    enviado_por: str = ""

    model_config = ConfigDict(from_attributes=True)


class OrigenPedidoCreate(BaseModel):
    pedido_id: int
    operador_nombre: str = ""
    telefono_origen: str = ""
    referencia_chat: str = ""
    plataforma: str = ""
    script_usado: str = ""
    notas_operador: str = ""
    duracion_llamada_seg: Optional[int] = None


class OrigenPedidoRead(BaseModel):
    id: int
    pedido_id: int
    operador_nombre: str = ""
    telefono_origen: str = ""
    referencia_chat: str = ""
    plataforma: str = ""
    script_usado: str = ""
    notas_operador: str = ""
    duracion_llamada_seg: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class RenderPlantillaRequest(BaseModel):
    """Renderiza una plantilla sustituyendo variables con datos del pedido."""
    plantilla_id: int
    pedido_id: int



# ── Fase 5: Cocina y operación interna ────────────────────────────────────────

class EstacionCocinaCreate(BaseModel):
    name: str
    codigo: str = ""
    descripcion: str = ""
    activa: bool = True
    sequence: int = 10
    color: str = "#6c757d"
    icono: str = "fa-fire"


class EstacionCocinaRead(BaseModel):
    id: int
    name: str
    codigo: str = ""
    descripcion: str = ""
    activa: bool
    sequence: int
    color: str
    icono: str

    model_config = ConfigDict(from_attributes=True)


class TiempoProduccionCreate(BaseModel):
    torta_id: int
    estacion_id: int
    variante_id: Optional[int] = None
    minutos: int = 5
    activo: bool = True


class TiempoProduccionRead(BaseModel):
    id: int
    torta_id: int
    estacion_id: int
    variante_id: Optional[int] = None
    minutos: int

    model_config = ConfigDict(from_attributes=True)


class TicketCocinaLineaCreate(BaseModel):
    pedido_linea_id: Optional[int] = None
    descripcion: str
    cantidad: int = 1
    variante: str = ""
    modificadores_texto: str = ""
    notas: str = ""


class TicketCocinaCreate(BaseModel):
    pedido_id: int
    estacion_id: Optional[int] = None
    prioridad: str = "normal"
    notas: str = ""
    lineas: List["TicketCocinaLineaCreate"] = []


class TicketCocinaLineaRead(BaseModel):
    id: int
    descripcion: str
    cantidad: int
    variante: str = ""
    modificadores_texto: str = ""
    notas: str = ""
    estado: str

    model_config = ConfigDict(from_attributes=True)


class TicketCocinaRead(BaseModel):
    id: int
    pedido_id: int
    estacion_id: Optional[int] = None
    numero_ticket: str
    estado: str
    prioridad: str
    notas: str = ""
    impreso: bool
    lineas: List["TicketCocinaLineaRead"] = []

    model_config = ConfigDict(from_attributes=True)


class ActualizarEstadoTicketRequest(BaseModel):
    estado: str   # pendiente | en_preparacion | listo | cancelado


class ActualizarEstadoLineaTicketRequest(BaseModel):
    estado: str


# ── Fase 6: Clientes y fidelización ──────────────────────────────────────────

class PuntosHistorialRead(BaseModel):
    id: int
    cliente_id: int
    pedido_id: Optional[int] = None
    tipo: str
    puntos: int
    saldo_resultante: int
    descripcion: str = ""
    created_at: Optional[datetime] = None
    creado_por: str = ""
    model_config = ConfigDict(from_attributes=True)

class AjustePuntosRequest(BaseModel):
    puntos: int           # positivo=añadir, negativo=quitar
    descripcion: str = ""
    creado_por: str = ""

class RecompensaCreate(BaseModel):
    name: str
    descripcion: str = ""
    tipo: str = "descuento_fijo"
    valor: float = 0.0
    puntos_necesarios: int
    activa: bool = True
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    limite_usos: int = 0

class RecompensaRead(RecompensaCreate):
    id: int
    usos_actuales: int = 0
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class RecompensaUsoRead(BaseModel):
    id: int
    cliente_id: int
    recompensa_id: int
    pedido_id: Optional[int] = None
    puntos_usados: int
    valor_aplicado: float = 0.0
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class CanjearRecompensaRequest(BaseModel):
    recompensa_id: int
    pedido_id: Optional[int] = None

class PreferenciaClienteCreate(BaseModel):
    tipo: str = "preferencia"   # preferencia | restriccion | alergia
    nombre: str
    descripcion: str = ""
    activa: bool = True

class PreferenciaClienteRead(PreferenciaClienteCreate):
    id: int
    cliente_id: int
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class PromocionClienteCreate(BaseModel):
    name: str
    descripcion: str = ""
    tipo: str = "descuento_fijo"
    valor: float = 0.0
    codigo: str = ""
    activa: bool = True
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    usos_maximos: int = 1

class PromocionClienteRead(PromocionClienteCreate):
    id: int
    cliente_id: int
    usos_actuales: int = 0
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class ClienteStatsRead(BaseModel):
    cliente_id: int
    nombre: str
    nivel_fidelidad: str
    puntos_acumulados: int
    puntos_canjeados: int
    puntos_disponibles: int
    total_historico: float
    num_pedidos: int
    ultimo_pedido_at: Optional[datetime] = None


# ── Fase 7: Entrega y logística ───────────────────────────────────────────────

class RepartidorCreate(BaseModel):
    nombre: str
    telefono: str = ""
    email: str = ""
    vehiculo: str = "moto"
    placas: str = ""
    activo: bool = True
    disponible: bool = True
    notas: str = ""

class RepartidorRead(RepartidorCreate):
    id: int
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class EntregaCreate(BaseModel):
    pedido_id: int
    repartidor_id: Optional[int] = None
    tipo: str = "domicilio"   # domicilio | pickup | plataforma_tercero
    notas: str = ""

class EntregaRead(BaseModel):
    id: int
    pedido_id: int
    repartidor_id: Optional[int] = None
    tipo: str
    estado: str
    tiempo_salida: Optional[datetime] = None
    tiempo_estimado_llegada: Optional[datetime] = None
    tiempo_entrega_real: Optional[datetime] = None
    distancia_km: float = 0.0
    evidencia_url: str = ""
    firma_url: str = ""
    motivo_fallo: str = ""
    notas: str = ""
    cerrado_por: str = ""
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class AsignarRepartidorRequest(BaseModel):
    repartidor_id: int

class ActualizarEstadoEntregaRequest(BaseModel):
    # asignado | en_camino | entregado | fallido | cancelado
    estado: str
    tiempo_salida: Optional[datetime] = None
    tiempo_estimado_llegada: Optional[datetime] = None
    tiempo_entrega_real: Optional[datetime] = None
    distancia_km: Optional[float] = None
    motivo_fallo: str = ""
    notas: str = ""
    cerrado_por: str = ""

class RegistrarEvidenciaRequest(BaseModel):
    evidencia_url: str = ""
    firma_url: str = ""
    notas: str = ""
    cerrado_por: str = ""


# ── Fase 8: Caja y administración ────────────────────────────────────────────

class CajaCreate(BaseModel):
    name: str
    codigo: str = ""
    activa: bool = True
    descripcion: str = ""
    concepto_id: Optional[int] = None

class CajaRead(CajaCreate):
    id: int
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class TurnoCreate(BaseModel):
    caja_id: Optional[int] = None
    usuario: str
    nombre: str = "completo"   # matutino | vespertino | nocturno | completo
    monto_inicial_caja: float = 0.0
    notas: str = ""

class TurnoRead(TurnoCreate):
    id: int
    hora_inicio: Optional[datetime] = None
    hora_fin: Optional[datetime] = None
    estado: str = "abierto"
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class CerrarTurnoRequest(BaseModel):
    notas: str = ""

class CerrarCorteRequest(BaseModel):
    usuario_cierre: str = ""
    efectivo_contado: float = 0.0
    notas: str = ""

class AnulacionCreate(BaseModel):
    pedido_id: int
    tipo: str = "total"    # total | parcial
    motivo: str
    descripcion: str = ""
    monto_anulado: float
    autorizado_por: str = ""
    registrado_por: str = ""
    corte_caja_id: Optional[int] = None

class AnulacionRead(AnulacionCreate):
    id: int
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class DevolucionCreate(BaseModel):
    pedido_id: int
    tipo_reembolso: str = "efectivo"  # efectivo | credito | puntos | sin_reembolso
    motivo: str
    descripcion: str = ""
    monto_devuelto: float = 0.0
    puntos_devueltos: int = 0
    autorizado_por: str = ""
    registrado_por: str = ""
    corte_caja_id: Optional[int] = None

class DevolucionRead(DevolucionCreate):
    id: int
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class KPIsCorteRead(BaseModel):
    corte_id: int
    total_ventas: float
    total_efectivo: float
    total_tarjeta: float
    total_transferencia: float
    total_otros: float
    total_descuentos: float
    total_cupones: float
    total_anulaciones: float
    total_devoluciones: float
    num_pedidos: int
    num_anulaciones: int
    num_devoluciones: int
    # Desglose por canal y por forma de pago
    ventas_por_canal: dict = {}
    ventas_por_forma_pago: dict = {}


# ── Fase 9: Promociones y combos ─────────────────────────────────────────────

class PromocionCreate(BaseModel):
    name: str
    descripcion: str = ""
    activa: bool = True
    tipo_accion: str = "descuento_porcentaje"
    valor: float = 0.0
    descuento_maximo: float = 0.0
    producto_gratis_id: Optional[int] = None
    monto_minimo: float = 0.0
    canal_venta_id: Optional[int] = None
    concepto_id: Optional[int] = None
    dias_semana: str = ""        # JSON ej. '["0","1","5"]'
    hora_desde: Optional[float] = None
    hora_hasta: Optional[float] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    solo_primera_compra: bool = False
    aplica_a: str = "todos"
    limite_usos_total: int = 0
    limite_usos_cliente: int = 0
    prioridad: int = 10
    acumulable: bool = False

class PromocionRead(PromocionCreate):
    id: int
    usos_actuales: int = 0
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class PromocionUsoRead(BaseModel):
    id: int
    promocion_id: int
    pedido_id: Optional[int] = None
    cliente_id: Optional[int] = None
    monto_descuento: float = 0.0
    descripcion: str = ""
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class EvaluarPromocionesRequest(BaseModel):
    """Solicita calcular qué promociones aplican a un pedido/cotización."""
    monto_subtotal: float
    canal_venta_id: Optional[int] = None
    concepto_id: Optional[int] = None
    cliente_id: Optional[int] = None
    productos_ids: list[int] = []

class EvaluarPromocionesResponse(BaseModel):
    promociones_aplicables: list[PromocionRead] = []
    descuento_total: float = 0.0
    detalle: list[dict] = []

class ComboLineaCreate(BaseModel):
    producto_id: Optional[int] = None
    es_opcional: bool = False
    categoria_id: Optional[int] = None
    cantidad: int = 1
    precio_unitario: float = 0.0
    descripcion: str = ""

class ComboLineaRead(ComboLineaCreate):
    id: int
    combo_id: int
    model_config = ConfigDict(from_attributes=True)

class ComboCreate(BaseModel):
    name: str
    descripcion: str = ""
    concepto_id: Optional[int] = None
    precio_combo: float = 0.0
    activo: bool = True
    imagen_url: str = ""
    disponible: bool = True
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    descuento_porcentaje: float = 0.0
    lineas: list[ComboLineaCreate] = []

class ComboRead(BaseModel):
    id: int
    name: str
    descripcion: str = ""
    concepto_id: Optional[int] = None
    precio_combo: float = 0.0
    activo: bool = True
    imagen_url: str = ""
    disponible: bool = True
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    descuento_porcentaje: float = 0.0
    lineas: list[ComboLineaRead] = []
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ── Fase 9: Promociones y combos ─────────────────────────────────────────────

class PromocionCreate(BaseModel):
    name: str
    descripcion: str = ""
    activa: bool = True
    tipo_accion: str = "descuento_porcentaje"
    valor: float = 0.0
    descuento_maximo: float = 0.0
    producto_gratis_id: Optional[int] = None
    monto_minimo: float = 0.0
    canal_venta_id: Optional[int] = None
    concepto_id: Optional[int] = None
    dias_semana: str = ""        # JSON ej. '["0","1","5"]'
    hora_desde: Optional[float] = None
    hora_hasta: Optional[float] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    solo_primera_compra: bool = False
    aplica_a: str = "todos"
    limite_usos_total: int = 0
    limite_usos_cliente: int = 0
    prioridad: int = 10
    acumulable: bool = False

class PromocionRead(PromocionCreate):
    id: int
    usos_actuales: int = 0
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class PromocionUsoRead(BaseModel):
    id: int
    promocion_id: int
    pedido_id: Optional[int] = None
    cliente_id: Optional[int] = None
    monto_descuento: float = 0.0
    descripcion: str = ""
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class EvaluarPromocionesRequest(BaseModel):
    """Solicita calcular qué promociones aplican a un pedido/cotización."""
    monto_subtotal: float
    canal_venta_id: Optional[int] = None
    concepto_id: Optional[int] = None
    cliente_id: Optional[int] = None
    productos_ids: list[int] = []

class EvaluarPromocionesResponse(BaseModel):
    promociones_aplicables: list[PromocionRead] = []
    descuento_total: float = 0.0
    detalle: list[dict] = []

class ComboLineaCreate(BaseModel):
    producto_id: Optional[int] = None
    es_opcional: bool = False
    categoria_id: Optional[int] = None
    cantidad: int = 1
    precio_unitario: float = 0.0
    descripcion: str = ""

class ComboLineaRead(ComboLineaCreate):
    id: int
    combo_id: int
    model_config = ConfigDict(from_attributes=True)

class ComboCreate(BaseModel):
    name: str
    descripcion: str = ""
    concepto_id: Optional[int] = None
    precio_combo: float = 0.0
    activo: bool = True
    imagen_url: str = ""
    disponible: bool = True
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    descuento_porcentaje: float = 0.0
    lineas: list[ComboLineaCreate] = []

class ComboRead(BaseModel):
    id: int
    name: str
    descripcion: str = ""
    concepto_id: Optional[int] = None
    precio_combo: float = 0.0
    activo: bool = True
    imagen_url: str = ""
    disponible: bool = True
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    descuento_porcentaje: float = 0.0
    lineas: list[ComboLineaRead] = []
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ── Fase 10: Inventario y recetas ─────────────────────────────────────────────

class InsumoCreate(BaseModel):
    name: str
    descripcion: str = ""
    unidad: str = "pieza"
    stock_actual: float = 0.0
    stock_minimo: float = 0.0
    costo_unitario: float = 0.0
    activo: bool = True
    descuento_automatico: bool = True

class InsumoRead(InsumoCreate):
    id: int
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class InsumoStockAlerta(BaseModel):
    id: int
    name: str
    unidad: str
    stock_actual: float
    stock_minimo: float
    diferencia: float
    model_config = ConfigDict(from_attributes=True)

class MovimientoInsumoCreate(BaseModel):
    insumo_id: int
    tipo: str = "entrada"   # entrada | salida | ajuste | merma
    cantidad: float
    pedido_id: Optional[int] = None
    costo_unitario: float = 0.0
    descripcion: str = ""
    creado_por: str = ""

class MovimientoInsumoRead(MovimientoInsumoCreate):
    id: int
    stock_resultante: float = 0.0
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class RecetaLineaCreate(BaseModel):
    insumo_id: int
    cantidad: float
    unidad: str = ""
    notas: str = ""

class RecetaLineaRead(RecetaLineaCreate):
    id: int
    receta_id: int
    model_config = ConfigDict(from_attributes=True)

class RecetaCreate(BaseModel):
    producto_id: int
    variante_id: Optional[int] = None
    name: str = "Receta estándar"
    activa: bool = True
    porciones: int = 1
    notas: str = ""
    lineas: list[RecetaLineaCreate] = []

class RecetaRead(BaseModel):
    id: int
    producto_id: int
    variante_id: Optional[int] = None
    name: str
    activa: bool
    porciones: int
    notas: str = ""
    lineas: list[RecetaLineaRead] = []
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class OpcionModificadorInsumoCreate(BaseModel):
    opcion_id: int
    insumo_id: int
    cantidad: float = 1.0
    unidad: str = ""

class OpcionModificadorInsumoRead(OpcionModificadorInsumoCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)

class DescontarStockPedidoRequest(BaseModel):
    """Solicita descontar el stock de todos los insumos usados en un pedido."""
    pedido_id: int
    creado_por: str = ""

class AjusteStockRequest(BaseModel):
    insumo_id: int
    stock_nuevo: float
    motivo: str = ""
    creado_por: str = ""



# ── Fase 11: Reportes y analítica ─────────────────────────────────────────────

class ReportePeriodoRequest(BaseModel):
    fecha_inicio: date
    fecha_fin: date
    limit: int = 20


class ReporteVentasDiaItem(BaseModel):
    fecha: Optional[date]
    num_pedidos: int
    total_ventas: float
    ticket_promedio: float


class ReporteVentasCanalItem(BaseModel):
    canal_id: Optional[int]
    canal: str
    num_pedidos: int
    total_ventas: float
    ticket_promedio: float


class ReporteProductoTopItem(BaseModel):
    producto_id: Optional[int]
    nombre: str
    cantidad_vendida: float
    total_ventas: float


class ReporteModificadorTopItem(BaseModel):
    opcion_id: Optional[int]
    opcion: str
    grupo: str
    veces_usado: int


class ReporteClienteRecurrenteItem(BaseModel):
    cliente_id: int
    nombre: str
    telefono: str
    num_pedidos: int
    total_gastado: float
    ultima_visita: Optional[datetime]


class ReportePromocionEfectivaItem(BaseModel):
    promocion_id: int
    nombre: str
    veces_usada: int
    descuento_total: float


class ReporteTiempoPreparacionItem(BaseModel):
    estacion_id: Optional[int]
    estacion: str
    tiempo_promedio_min: float
    num_tickets: int


class ReporteTiempoEntregaItem(BaseModel):
    fecha: Optional[date]
    num_entregas: int
    tiempo_promedio_min: float


class DashboardGerencialResponse(BaseModel):
    ventas_hoy: float
    pedidos_hoy: int
    ticket_promedio_hoy: float
    ventas_semana: float
    pedidos_semana: int
    ventas_mes: float
    pedidos_mes: int
    ticket_promedio_mes: float
    clientes_nuevos_mes: int
    top_producto_hoy: str
    alertas_stock: int


class DashboardOperativoResponse(BaseModel):
    pedidos_pendientes: int
    pedidos_en_cocina: int
    pedidos_en_camino: int
    pedidos_listos: int
    repartidores_activos: int
    alertas_stock: int
    turnos_abiertos: int
    cajas_abiertas: int



# ── Fase 12: Automatización e integración ─────────────────────────────────────

class EventoSistemaRead(BaseModel):
    id: int
    tipo_evento: str
    entidad: str
    entidad_id: Optional[int]
    payload_json: str
    actor: str
    resultado: str
    detalle: str
    created_at: datetime

    class Config:
        from_attributes = True


class AutomatizacionCreate(BaseModel):
    name: str
    descripcion: str = ""
    activa: bool = True
    prioridad: int = 10
    evento_disparador: str
    condicion_estado: str = ""
    canal_venta_id: Optional[int] = None
    concepto_id: Optional[int] = None
    accion_tipo: str = "enviar_mensaje"
    plantilla_id: Optional[int] = None
    canal_mensaje: str = "whatsapp"
    estado_destino: str = ""
    delay_seg: int = 0


class AutomatizacionRead(AutomatizacionCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class WebhookSalidaCreate(BaseModel):
    name: str
    url: str
    eventos: str = ""
    header_auth: str = ""
    activo: bool = True


class WebhookSalidaRead(WebhookSalidaCreate):
    id: int
    ultimo_estado: str
    ultimo_error: str
    ultimo_envio_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class DisparadorEventoRequest(BaseModel):
    pedido_id: int
    evento: str
    actor: str = "sistema"
    payload: dict = {}

class CanalVentaCreate(BaseModel):
    name: str
    codigo: str  # mostrador, mesa, telefono, whatsapp, web, app, rappi, uber_eats, didi, preorden, catering, otro
    activo: bool = True
    sequence: int = 10
    icono: str = "fa-store"
    descripcion: str = ""
    requiere_confirmacion: bool = False


class CanalVentaRead(BaseModel):
    id: int
    name: str
    codigo: str
    activo: bool
    sequence: int
    icono: str
    descripcion: str
    requiere_confirmacion: bool

    class Config:
        from_attributes = True


# ── Concepto de restaurante ───────────────────────────────────────────────────

class ConceptoCreate(BaseModel):
    name: str
    tipo_cocina: str = "general"  # tortas, pizza, sushi, hamburguesas, ensaladas, tacos, general, otro
    descripcion: str = ""
    icono: str = "fa-utensils"
    color_primario: str = "#6c757d"
    label_producto: str = "Producto"
    label_base: str = "Base"
    label_modificador: str = "Modificador"


class ConceptoRead(BaseModel):
    id: int
    name: str
    tipo_cocina: str
    descripcion: str
    icono: str
    color_primario: str
    label_producto: str
    label_base: str
    label_modificador: str
    activo: bool

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


# ── Línea de topping / modificador (para pedido) ──────────────────────────────

class LineaToppingCreate(BaseModel):
    topping_id: int
    cantidad: int = 1
    precio_unitario: float = 0.0


# ── Línea de pedido ───────────────────────────────────────────────────────────

class LineaPedidoCreate(BaseModel):
    torta_id: int
    cantidad: int = 1
    precio_unitario: float
    base_id: Optional[int] = None
    precio_base: float = 0.0
    descripcion: str = ""
    notas: str = ""
    toppings: List[LineaToppingCreate] = []


class LineaPedidoRead(BaseModel):
    id: int
    torta_id: int
    cantidad: int
    precio_unitario: float
    base_id: Optional[int]
    precio_base: float
    notas: str

    class Config:
        from_attributes = True


# ── Pedido ────────────────────────────────────────────────────────────────────

class PedidoCreate(BaseModel):
    nombre_cliente: str = ""
    telefono: str = ""
    email: str = ""
    # mostrador, mesa, para_llevar, domicilio, preorden, catering
    tipo_pedido: str = "mostrador"
    canal_venta_id: Optional[int] = None
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
    canal_venta_id: Optional[int] = None


class PedidoRead(BaseModel):
    id: int
    numero_pedido: str
    fecha_pedido: datetime
    nombre_cliente: str
    telefono: str
    tipo_pedido: str
    canal_venta_id: Optional[int]
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
