from __future__ import annotations
from datetime import date, datetime
from sqlalchemy import (
    Boolean, Column, Date, DateTime, Float, ForeignKey,
    Integer, String, Table, Text, func
)
from sqlalchemy.orm import relationship
from fastapi_modulo.core.db import MAIN

# ── Tablas de asociación (Many2many) ──────────────────────────────────────────

torta_alergeno = Table(
    "torta_alergeno", MAIN.metadata,
    Column("torta_id", Integer, ForeignKey("tortas_torta.id", ondelete="CASCADE"), primary_key=True),
    Column("alergeno_id", Integer, ForeignKey("tortas_alergeno.id", ondelete="CASCADE"), primary_key=True),
)

torta_tipo_alimento = Table(
    "torta_tipo_alimento", MAIN.metadata,
    Column("torta_id", Integer, ForeignKey("tortas_torta.id", ondelete="CASCADE"), primary_key=True),
    Column("tipo_alimento_id", Integer, ForeignKey("tortas_tipo_alimento.id", ondelete="CASCADE"), primary_key=True),
)

torta_tipo_pan = Table(
    "torta_tipo_pan", MAIN.metadata,
    Column("torta_id", Integer, ForeignKey("tortas_torta.id", ondelete="CASCADE"), primary_key=True),
    Column("tipo_pan_id", Integer, ForeignKey("tortas_tipo_pan.id", ondelete="CASCADE"), primary_key=True),
)

topping_alergeno = Table(
    "topping_alergeno", MAIN.metadata,
    Column("topping_id", Integer, ForeignKey("tortas_topping.id", ondelete="CASCADE"), primary_key=True),
    Column("alergeno_id", Integer, ForeignKey("tortas_alergeno.id", ondelete="CASCADE"), primary_key=True),
)

cupon_categoria = Table(
    "cupon_categoria", MAIN.metadata,
    Column("cupon_id", Integer, ForeignKey("tortas_cupon.id", ondelete="CASCADE"), primary_key=True),
    Column("categoria_id", Integer, ForeignKey("tortas_categoria.id", ondelete="CASCADE"), primary_key=True),
)

cupon_torta = Table(
    "cupon_torta", MAIN.metadata,
    Column("cupon_id", Integer, ForeignKey("tortas_cupon.id", ondelete="CASCADE"), primary_key=True),
    Column("torta_id", Integer, ForeignKey("tortas_torta.id", ondelete="CASCADE"), primary_key=True),
)


# ── Catálogo base ─────────────────────────────────────────────────────────────

class TortasCategoria(MAIN):
    __tablename__ = "tortas_categoria"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    descripcion = Column(Text, default="")
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    tortas = relationship("TortasBase", back_populates="categoria")


class TortasAlergeno(MAIN):
    __tablename__ = "tortas_alergeno"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    codigo = Column(String(50), default="")
    descripcion = Column(Text, default="")
    icono = Column(String(100), default="fa-exclamation-triangle")
    color = Column(String(20), default="#ff6b6b")
    advertencia = Column(Text, default="")
    activo = Column(Boolean, default=True)
    sequence = Column(Integer, default=10)
    created_at = Column(DateTime, default=func.now())

    tortas = relationship("TortasBase", secondary=torta_alergeno, back_populates="alergenos")
    toppings = relationship("TortasTopping", secondary=topping_alergeno, back_populates="alergenos")


class TortasTipoAlimento(MAIN):
    __tablename__ = "tortas_tipo_alimento"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    codigo = Column(String(50), default="")
    descripcion = Column(Text, default="")
    icono = Column(String(100), default="fa-leaf")
    color = Column(String(20), default="#28a745")
    activo = Column(Boolean, default=True)
    sequence = Column(Integer, default=10)
    permite_carne = Column(Boolean, default=False)
    permite_lacteos = Column(Boolean, default=True)
    permite_huevos = Column(Boolean, default=True)
    permite_miel = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    tortas = relationship("TortasBase", secondary=torta_tipo_alimento, back_populates="tipos_alimento")


class TipoPan(MAIN):
    __tablename__ = "tortas_tipo_pan"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(255), nullable=False, unique=True)
    descripcion = Column(Text, default="")
    activo = Column(Boolean, default=True)
    sequence = Column(Integer, default=10)
    precio_extra = Column(Float, default=0.0)
    disponible = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    tortas = relationship("TortasBase", secondary=torta_tipo_pan, back_populates="tipos_pan")


class TortasTopping(MAIN):
    __tablename__ = "tortas_topping"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    descripcion = Column(Text, default="")
    tipo = Column(String(20), nullable=False, default="fijo")  # incluido, fijo, cantidad
    precio = Column(Float, default=0.0)
    unidad = Column(String(100), default="")
    maximo = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=10)
    created_at = Column(DateTime, default=func.now())

    alergenos = relationship("TortasAlergeno", secondary=topping_alergeno, back_populates="toppings")


class TortasBase(MAIN):
    __tablename__ = "tortas_torta"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    descripcion = Column(Text, default="")
    precio = Column(Float, nullable=False, default=0.0)
    categoria_id = Column(Integer, ForeignKey("tortas_categoria.id"), nullable=True)
    ingredientes = Column(Text, default="")
    active = Column(Boolean, default=True)
    min_toppings = Column(Integer, default=0)
    max_toppings = Column(Integer, default=0)
    mensaje_min_toppings = Column(String(255), default="Debes seleccionar al menos {min} topping(s)")
    mensaje_max_toppings = Column(String(255), default="Solo puedes seleccionar hasta {max} topping(s)")
    requiere_tipo_pan = Column(Boolean, default=False)
    tipo_pan_predeterminado_id = Column(Integer, ForeignKey("tortas_tipo_pan.id"), nullable=True)
    # Nutrición
    calorias = Column(Integer, default=0)
    proteinas = Column(Float, default=0.0)
    carbohidratos = Column(Float, default=0.0)
    grasas = Column(Float, default=0.0)
    fibra = Column(Float, default=0.0)
    azucares = Column(Float, default=0.0)
    sodio = Column(Float, default=0.0)
    info_nutricional_adicional = Column(Text, default="")
    disclaimer_alergenos = Column(
        Text,
        default="Este producto puede contener trazas de otros alérgenos por manipulación cruzada."
    )
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    categoria = relationship("TortasCategoria", back_populates="tortas")
    tipo_pan_predeterminado = relationship("TipoPan", foreign_keys=[tipo_pan_predeterminado_id])
    alergenos = relationship("TortasAlergeno", secondary=torta_alergeno, back_populates="tortas")
    tipos_alimento = relationship("TortasTipoAlimento", secondary=torta_tipo_alimento, back_populates="tortas")
    tipos_pan = relationship("TipoPan", secondary=torta_tipo_pan, back_populates="tortas")


# ── Entrega ───────────────────────────────────────────────────────────────────

class TortasZonaEntrega(MAIN):
    __tablename__ = "tortas_zona_entrega"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    active = Column(Boolean, default=True)
    codigo_postal = Column(String(255), default="")
    descripcion = Column(Text, default="")
    costo_envio = Column(Float, default=0.0)
    envio_gratis_desde = Column(Float, default=0.0)
    monto_minimo_pedido = Column(Float, default=0.0)
    tiempo_entrega_minutos = Column(Integer, default=45)
    tiempo_minimo = Column(Integer, default=30)
    tiempo_maximo = Column(Integer, default=60)
    acepta_pedidos = Column(Boolean, default=True)
    mensaje_no_disponible = Column(Text, default="Lo sentimos, no hacemos entregas a esta zona.")
    horario_desde = Column(Float, default=0.0)
    horario_hasta = Column(Float, default=24.0)
    created_at = Column(DateTime, default=func.now())

    colonias = relationship("TortasColonia", back_populates="zona", cascade="all, delete-orphan")


class TortasColonia(MAIN):
    __tablename__ = "tortas_colonia"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    codigo_postal = Column(String(20), default="")
    zona_id = Column(Integer, ForeignKey("tortas_zona_entrega.id"), nullable=False)
    active = Column(Boolean, default=True)
    notas = Column(Text, default="")

    zona = relationship("TortasZonaEntrega", back_populates="colonias")


class TortasMetodoEntrega(MAIN):
    __tablename__ = "tortas_metodo_entrega"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    sequence = Column(Integer, default=10)
    active = Column(Boolean, default=True)
    codigo = Column(String(20), default="otro")  # mostrador, para_llevar, domicilio, otro
    requiere_direccion = Column(Boolean, default=False)
    requiere_zona = Column(Boolean, default=False)
    tiene_costo_adicional = Column(Boolean, default=False)
    costo_adicional = Column(Float, default=0.0)
    disponible = Column(Boolean, default=True)
    mensaje_no_disponible = Column(Text, default="Este método de entrega no está disponible")
    tiempo_preparacion_extra = Column(Integer, default=0)
    descripcion = Column(Text, default="")
    icono = Column(String(100), default="fa-box")
    created_at = Column(DateTime, default=func.now())


# ── Horarios ──────────────────────────────────────────────────────────────────

class TortasHorario(MAIN):
    __tablename__ = "tortas_horario"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dia_semana = Column(String(1), nullable=False)  # 0=Lunes..6=Domingo
    cerrado = Column(Boolean, default=False)
    hora_apertura = Column(Float, default=9.0)
    hora_cierre = Column(Float, default=20.0)
    tiene_segunda_jornada = Column(Boolean, default=False)
    hora_apertura_2 = Column(Float, default=17.0)
    hora_cierre_2 = Column(Float, default=22.0)
    tiempo_preparacion_minutos = Column(Integer, default=30)
    tiempo_entrega_domicilio = Column(Integer, default=45)
    acepta_para_llevar = Column(Boolean, default=True)
    acepta_domicilio = Column(Boolean, default=True)
    acepta_mostrador = Column(Boolean, default=True)
    active = Column(Boolean, default=True)


class TortasDiaFestivo(MAIN):
    __tablename__ = "tortas_dia_festivo"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    fecha = Column(Date, nullable=False)
    cerrado = Column(Boolean, default=True)
    hora_apertura = Column(Float, default=10.0)
    hora_cierre = Column(Float, default=18.0)
    mensaje = Column(Text, default="")
    notas = Column(Text, default="")
    active = Column(Boolean, default=True)


class TortasConfiguracion(MAIN):
    __tablename__ = "tortas_configuracion"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, default="Configuración General")
    negocio_abierto = Column(Boolean, default=True)
    mensaje_cierre_temporal = Column(Text, default="Lo sentimos, estamos temporalmente cerrados.")
    tiempo_preparacion_default = Column(Integer, default=30)
    tiempo_domicilio_default = Column(Integer, default=45)
    pedido_minimo_domicilio = Column(Float, default=100.0)
    acepta_pedidos_adelantados = Column(Boolean, default=True)
    dias_adelanto_maximo = Column(Integer, default=7)
    mensaje_bienvenida = Column(Text, default="¡Bienvenido! Haz tu pedido en línea")
    mensaje_horario_cierre = Column(Text, default="Estamos cerrados.")
    active = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


# ── Formas de pago ────────────────────────────────────────────────────────────

class TortasFormaPago(MAIN):
    __tablename__ = "tortas_forma_pago"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    sequence = Column(Integer, default=10)
    active = Column(Boolean, default=True)
    # efectivo, tarjeta_debito, tarjeta_credito, transferencia, cheque, vale, otro
    codigo = Column(String(30), nullable=False, default="efectivo")
    requiere_referencia = Column(Boolean, default=False)
    aplica_comision = Column(Boolean, default=False)
    porcentaje_comision = Column(Float, default=0.0)
    cuenta_bancaria = Column(String(255), default="")
    afecta_caja = Column(Boolean, default=True)
    icono = Column(String(100), default="fa-money-bill")
    notas = Column(Text, default="")
    created_at = Column(DateTime, default=func.now())


# ── Cupones ───────────────────────────────────────────────────────────────────

class TortasCupon(MAIN):
    __tablename__ = "tortas_cupon"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    codigo = Column(String(50), nullable=False, unique=True)
    active = Column(Boolean, default=True)
    tipo_descuento = Column(String(20), nullable=False, default="porcentaje")  # porcentaje, monto_fijo
    valor_descuento = Column(Float, nullable=False, default=0.0)
    descuento_maximo = Column(Float, default=0.0)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    monto_minimo = Column(Float, default=0.0)
    uso_maximo = Column(Integer, default=0)
    uso_maximo_cliente = Column(Integer, default=1)
    aplica_a = Column(String(20), default="todos")  # todos, categoria, producto
    solo_primera_compra = Column(Boolean, default=False)
    descripcion = Column(Text, default="")
    notas_internas = Column(Text, default="")
    created_at = Column(DateTime, default=func.now())

    categorias = relationship("TortasCategoria", secondary=cupon_categoria)
    tortas_asociadas = relationship("TortasBase", secondary=cupon_torta)
    usos = relationship("TortasCuponUso", back_populates="cupon", cascade="all, delete-orphan")


class TortasCuponUso(MAIN):
    __tablename__ = "tortas_cupon_uso"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cupon_id = Column(Integer, ForeignKey("tortas_cupon.id"), nullable=False)
    pedido_id = Column(Integer, ForeignKey("tortas_pedido.id"), nullable=True)
    nombre_cliente = Column(String(255), default="")
    fecha_uso = Column(DateTime, nullable=False, default=func.now())
    monto_pedido = Column(Float, nullable=False, default=0.0)
    monto_descuento = Column(Float, nullable=False, default=0.0)
    codigo_cupon = Column(String(50), default="")
    created_at = Column(DateTime, default=func.now())

    cupon = relationship("TortasCupon", back_populates="usos")


# ── Corte de caja ─────────────────────────────────────────────────────────────

class TortasCorteCaja(MAIN):
    __tablename__ = "tortas_corte_caja"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, default="Nuevo")
    fecha_inicio = Column(DateTime, nullable=False, default=func.now())
    fecha_cierre = Column(DateTime, nullable=True)
    estado = Column(String(20), nullable=False, default="abierto")  # abierto, cerrado, cancelado
    usuario_apertura = Column(String(255), default="")
    usuario_cierre = Column(String(255), default="")
    monto_inicial = Column(Float, default=0.0)
    efectivo_contado = Column(Float, default=0.0)
    total_gastos = Column(Float, default=0.0)
    total_retiros = Column(Float, default=0.0)
    notas = Column(Text, default="")
    created_at = Column(DateTime, default=func.now())

    pedidos = relationship("TortasPedido", back_populates="corte_caja")
    pagos = relationship("TortasPago", back_populates="corte_caja")


# ── Pedidos ───────────────────────────────────────────────────────────────────

class TortasPedido(MAIN):
    __tablename__ = "tortas_pedido"

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_pedido = Column(String(50), nullable=False, unique=True, index=True)
    fecha_pedido = Column(DateTime, nullable=False, default=func.now())
    nombre_cliente = Column(String(255), default="")
    telefono = Column(String(50), default="")
    email = Column(String(255), default="")
    tipo_pedido = Column(String(20), nullable=False, default="mostrador")  # mostrador, para_llevar, domicilio
    zona_entrega_id = Column(Integer, ForeignKey("tortas_zona_entrega.id"), nullable=True)
    costo_envio = Column(Float, default=0.0)
    tiempo_entrega_estimado = Column(Integer, default=0)
    direccion_entrega = Column(Text, default="")
    colonia = Column(String(255), default="")
    codigo_postal = Column(String(20), default="")
    referencias = Column(Text, default="")
    estado = Column(String(20), nullable=False, default="borrador", index=True)
    prioridad = Column(String(10), nullable=False, default="normal")  # baja, normal, alta, urgente
    fecha_confirmacion = Column(DateTime, nullable=True)
    fecha_inicio_preparacion = Column(DateTime, nullable=True)
    fecha_listo = Column(DateTime, nullable=True)
    fecha_entregado = Column(DateTime, nullable=True)
    fecha_entrega_programada = Column(DateTime, nullable=True)
    ticket_impreso = Column(Boolean, default=False)
    notas_cocina = Column(Text, default="")
    descuento = Column(Float, default=0.0)
    impuesto = Column(Float, default=0.0)  # porcentaje
    notas = Column(Text, default="")
    cupon_id = Column(Integer, ForeignKey("tortas_cupon.id"), nullable=True)
    codigo_cupon = Column(String(50), default="")
    corte_caja_id = Column(Integer, ForeignKey("tortas_corte_caja.id"), nullable=True)
    usuario = Column(String(255), default="")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    zona_entrega = relationship("TortasZonaEntrega")
    cupon = relationship("TortasCupon")
    corte_caja = relationship("TortasCorteCaja", back_populates="pedidos")
    lineas = relationship("TortasPedidoLinea", back_populates="pedido", cascade="all, delete-orphan")
    pagos = relationship("TortasPago", back_populates="pedido", cascade="all, delete-orphan")
    propinas = relationship("TortasPropina", back_populates="pedido", cascade="all, delete-orphan")


class TortasPedidoLinea(MAIN):
    __tablename__ = "tortas_pedido_linea"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("tortas_pedido.id"), nullable=False)
    sequence = Column(Integer, default=10)
    torta_id = Column(Integer, ForeignKey("tortas_torta.id"), nullable=False)
    descripcion = Column(Text, default="")
    cantidad = Column(Integer, nullable=False, default=1)
    tipo_pan_id = Column(Integer, ForeignKey("tortas_tipo_pan.id"), nullable=True)
    precio_pan = Column(Float, default=0.0)
    precio_unitario = Column(Float, nullable=False, default=0.0)
    notas = Column(Text, default="")

    pedido = relationship("TortasPedido", back_populates="lineas")
    torta = relationship("TortasBase")
    tipo_pan = relationship("TipoPan")
    toppings = relationship("TortasPedidoLineaTopping", back_populates="linea", cascade="all, delete-orphan")


class TortasPedidoLineaTopping(MAIN):
    __tablename__ = "tortas_pedido_linea_topping"

    id = Column(Integer, primary_key=True, autoincrement=True)
    linea_id = Column(Integer, ForeignKey("tortas_pedido_linea.id"), nullable=False)
    topping_id = Column(Integer, ForeignKey("tortas_topping.id"), nullable=False)
    cantidad = Column(Integer, default=1)
    precio_unitario = Column(Float, nullable=False, default=0.0)

    linea = relationship("TortasPedidoLinea", back_populates="toppings")
    topping = relationship("TortasTopping")


# ── Pagos ─────────────────────────────────────────────────────────────────────

class TortasPago(MAIN):
    __tablename__ = "tortas_pago"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("tortas_pedido.id"), nullable=False)
    fecha = Column(DateTime, nullable=False, default=func.now())
    forma_pago_id = Column(Integer, ForeignKey("tortas_forma_pago.id"), nullable=False)
    monto = Column(Float, nullable=False, default=0.0)
    referencia = Column(String(255), default="")
    notas = Column(Text, default="")
    cancelado = Column(Boolean, default=False)
    fecha_cancelacion = Column(DateTime, nullable=True)
    motivo_cancelacion = Column(Text, default="")
    corte_caja_id = Column(Integer, ForeignKey("tortas_corte_caja.id"), nullable=True)
    usuario = Column(String(255), default="")
    created_at = Column(DateTime, default=func.now())

    pedido = relationship("TortasPedido", back_populates="pagos")
    forma_pago = relationship("TortasFormaPago")
    corte_caja = relationship("TortasCorteCaja", back_populates="pagos")


class TortasPropina(MAIN):
    __tablename__ = "tortas_propina"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("tortas_pedido.id"), nullable=False)
    fecha = Column(DateTime, nullable=False, default=func.now())
    monto = Column(Float, nullable=False, default=0.0)
    tipo = Column(String(20), default="monto_fijo")  # porcentaje, monto_fijo
    porcentaje = Column(Float, default=0.0)
    notas = Column(Text, default="")

    pedido = relationship("TortasPedido", back_populates="propinas")


# ── Preordenes ────────────────────────────────────────────────────────────────

class TortasPreorden(MAIN):
    __tablename__ = "tortas_preorden"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, default="Nueva Preorden")
    nombre_cliente = Column(String(255), nullable=False, default="")
    telefono = Column(String(50), default="")
    email = Column(String(255), default="")
    pedido_id = Column(Integer, ForeignKey("tortas_pedido.id"), nullable=True)
    fecha_entrega = Column(Date, nullable=False)
    hora_entrega = Column(String(5), nullable=False, default="12:00")  # HH:MM
    tipo_pedido = Column(String(20), nullable=False, default="para_llevar")
    direccion_entrega = Column(Text, default="")
    zona_entrega_id = Column(Integer, ForeignKey("tortas_zona_entrega.id"), nullable=True)
    state = Column(String(30), nullable=False, default="borrador", index=True)
    notas = Column(Text, default="")
    costo_envio = Column(Float, default=0.0)
    recordatorio_enviado = Column(Boolean, default=False)
    fecha_recordatorio = Column(DateTime, nullable=True)
    motivo_cancelacion = Column(Text, default="")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    pedido = relationship("TortasPedido")
    zona_entrega = relationship("TortasZonaEntrega")
    lineas = relationship("TortasPreordenLinea", back_populates="preorden", cascade="all, delete-orphan")


class TortasPreordenLinea(MAIN):
    __tablename__ = "tortas_preorden_linea"

    id = Column(Integer, primary_key=True, autoincrement=True)
    preorden_id = Column(Integer, ForeignKey("tortas_preorden.id"), nullable=False)
    torta_id = Column(Integer, ForeignKey("tortas_torta.id"), nullable=False)
    cantidad = Column(Integer, nullable=False, default=1)
    precio_unitario = Column(Float, nullable=False, default=0.0)
    notas = Column(Text, default="")

    preorden = relationship("TortasPreorden", back_populates="lineas")
    torta = relationship("TortasBase")
    toppings = relationship("TortasPreordenLineaTopping", back_populates="linea", cascade="all, delete-orphan")


class TortasPreordenLineaTopping(MAIN):
    __tablename__ = "tortas_preorden_linea_topping"

    id = Column(Integer, primary_key=True, autoincrement=True)
    linea_id = Column(Integer, ForeignKey("tortas_preorden_linea.id"), nullable=False)
    topping_id = Column(Integer, ForeignKey("tortas_topping.id"), nullable=False)
    cantidad = Column(Integer, default=1)
    precio_unitario = Column(Float, nullable=False, default=0.0)

    linea = relationship("TortasPreordenLinea", back_populates="toppings")
    topping = relationship("TortasTopping")


# ── Creación de tablas ────────────────────────────────────────────────────────

def ensure_tortas_schema(bind=None) -> None:
    from fastapi_modulo.core.db import get_current_engine
    target = bind or get_current_engine()
    ordered = [
        TortasCategoria.__table__,
        TortasAlergeno.__table__,
        TortasTipoAlimento.__table__,
        TipoPan.__table__,
        TortasTopping.__table__,
        TortasBase.__table__,
        torta_alergeno,
        torta_tipo_alimento,
        torta_tipo_pan,
        topping_alergeno,
        TortasZonaEntrega.__table__,
        TortasColonia.__table__,
        TortasMetodoEntrega.__table__,
        TortasHorario.__table__,
        TortasDiaFestivo.__table__,
        TortasConfiguracion.__table__,
        TortasFormaPago.__table__,
        TortasCorteCaja.__table__,
        TortasPedido.__table__,
        TortasPedidoLinea.__table__,
        TortasPedidoLineaTopping.__table__,
        TortasPago.__table__,
        TortasPropina.__table__,
        TortasCupon.__table__,
        cupon_categoria,
        cupon_torta,
        TortasCuponUso.__table__,
        TortasPreorden.__table__,
        TortasPreordenLinea.__table__,
        TortasPreordenLineaTopping.__table__,
    ]
    for t in ordered:
        t.create(bind=target, checkfirst=True)
