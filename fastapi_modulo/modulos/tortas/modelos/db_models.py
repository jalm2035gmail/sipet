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

torta_base_producto = Table(
    "torta_base_producto", MAIN.metadata,
    Column("torta_id", Integer, ForeignKey("tortas_torta.id", ondelete="CASCADE"), primary_key=True),
    Column("base_id", Integer, ForeignKey("tortas_base_producto.id", ondelete="CASCADE"), primary_key=True),
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

torta_grupo_modificador = Table(
    "torta_grupo_modificador", MAIN.metadata,
    Column("torta_id", Integer, ForeignKey("tortas_torta.id", ondelete="CASCADE"), primary_key=True),
    Column("grupo_id", Integer, ForeignKey("tortas_grupo_modificador.id", ondelete="CASCADE"), primary_key=True),
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


class TortasBaseProducto(MAIN):
    """Base configurable del producto. Ejemplos:
       pan/telera/bolillo (tortas), masa delgada/gruesa (pizza),
       arroz blanco/integral (sushi/bowls), wrap/tortilla (burritos),
       lechuga/quinoa (ensaladas). Configurable por tipo de restaurante.
    """
    __tablename__ = "tortas_base_producto"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(255), nullable=False, unique=True)
    descripcion = Column(Text, default="")
    # pan, masa, arroz, wrap, tortilla, bowl, lechuga, otro
    tipo_base = Column(String(30), default="otro")
    activo = Column(Boolean, default=True)
    sequence = Column(Integer, default=10)
    precio_extra = Column(Float, default=0.0)
    disponible = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    productos = relationship("TortasBase", secondary=torta_base_producto, back_populates="bases")


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

class TortasVariante(MAIN):
    """Variantes de un producto: tamaño, porción, cantidad de piezas, etc.
    Ejemplos:
      Tortas/Burgers: Chica, Mediana, Grande, Familiar
      Pizzas:         Personal, Mediana, Grande, Familiar
      Sushi:          8 piezas, 12 piezas, 16 piezas
      Ensaladas:      Chica, Normal, Grande
    """
    __tablename__ = "tortas_variante"

    id = Column(Integer, primary_key=True, autoincrement=True)
    producto_id = Column(Integer, ForeignKey("tortas_torta.id"), nullable=False)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text, default="")
    precio_extra = Column(Float, default=0.0)  # adicional sobre precio base
    activo = Column(Boolean, default=True)
    disponible = Column(Boolean, default=True)
    sequence = Column(Integer, default=10)
    created_at = Column(DateTime, default=func.now())

    producto = relationship("TortasBase", back_populates="variantes")


class TortasGrupoModificador(MAIN):
    """Grupo de modificadores de un producto. Ejemplos:
      Tipo de base (obligatorio, elige 1) → pan/masa/arroz/wrap
      Salsas (opcional, hasta 3)
      Extras premium (opcional, sin límite)
      Proteína (obligatorio, elige 1)
    """
    __tablename__ = "tortas_grupo_modificador"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    descripcion = Column(Text, default="")
    # unico=radio button (elige 1), multiple=checkbox, cantidad=con input de cantidad
    tipo_seleccion = Column(String(20), default="multiple")
    obligatorio = Column(Boolean, default=False)
    minimo = Column(Integer, default=0)
    maximo = Column(Integer, default=0)   # 0 = sin límite
    activo = Column(Boolean, default=True)
    sequence = Column(Integer, default=10)
    created_at = Column(DateTime, default=func.now())

    opciones = relationship(
        "TortasOpcionModificador", back_populates="grupo",
        cascade="all, delete-orphan", order_by="TortasOpcionModificador.sequence"
    )
    productos = relationship(
        "TortasBase", secondary="torta_grupo_modificador",
        back_populates="grupos_modificadores"
    )


class TortasOpcionModificador(MAIN):
    """Opción individual dentro de un grupo de modificadores. Ejemplos:
      Grupo 'Salsas': chipotle, mayonesa, sin salsa
      Grupo 'Extras': queso extra, aguacate, tocino
      Grupo 'Base':   bolillo, telera, integral
    """
    __tablename__ = "tortas_opcion_modificador"

    id = Column(Integer, primary_key=True, autoincrement=True)
    grupo_id = Column(Integer, ForeignKey("tortas_grupo_modificador.id"), nullable=False)
    name = Column(String(255), nullable=False)
    descripcion = Column(Text, default="")
    precio = Column(Float, default=0.0)
    # incluido: va de base sin costo
    # extra: costo adicional
    # removible: se puede quitar (sin costo)
    # sustitucion: reemplaza otro ingrediente
    tipo = Column(String(20), default="extra")
    activo = Column(Boolean, default=True)
    disponible = Column(Boolean, default=True)
    sequence = Column(Integer, default=10)
    maximo_cantidad = Column(Integer, default=1)
    instruccion_cocina = Column(String(255), default="")
    created_at = Column(DateTime, default=func.now())

    grupo = relationship("TortasGrupoModificador", back_populates="opciones")



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
    mensaje_min_toppings = Column(String(255), default="Debes seleccionar al menos {min} modificador(es)")
    mensaje_max_toppings = Column(String(255), default="Solo puedes seleccionar hasta {max} modificador(es)")
    requiere_base = Column(Boolean, default=False)
    base_predeterminada_id = Column(Integer, ForeignKey("tortas_base_producto.id"), nullable=True)
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
    base_predeterminada = relationship("TortasBaseProducto", foreign_keys=[base_predeterminada_id])
    alergenos = relationship("TortasAlergeno", secondary=torta_alergeno, back_populates="tortas")
    tipos_alimento = relationship("TortasTipoAlimento", secondary=torta_tipo_alimento, back_populates="tortas")
    bases = relationship("TortasBaseProducto", secondary=torta_base_producto, back_populates="productos")
    variantes = relationship(
        "TortasVariante", back_populates="producto",
        cascade="all, delete-orphan", order_by="TortasVariante.sequence"
    )
    grupos_modificadores = relationship(
        "TortasGrupoModificador", secondary="torta_grupo_modificador",
        back_populates="productos"
    )


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


class TortasConcepto(MAIN):
    """Configuración del concepto de restaurante.
    Define qué tipo de cocina opera el negocio y personaliza
    los labels del sistema (base, modificador, producto) según el concepto.
    Un negocio puede tener múltiples conceptos si opera varias cocinas.
    """
    __tablename__ = "tortas_concepto"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, default="Mi Restaurante")
    # tortas, pizza, sushi, hamburguesas, ensaladas, tacos, general, otro
    tipo_cocina = Column(String(50), default="general")
    descripcion = Column(Text, default="")
    icono = Column(String(100), default="fa-utensils")
    color_primario = Column(String(20), default="#6c757d")
    # Labels configurables por concepto
    label_producto = Column(String(100), default="Producto")    # Torta / Pizza / Roll / Burger
    label_base = Column(String(100), default="Base")            # Tipo de pan / Masa / Arroz / Bowl
    label_modificador = Column(String(100), default="Modificador")  # Topping / Ingrediente / Extra
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


# ── Canal de venta ────────────────────────────────────────────────────────────

class TortasCanalVenta(MAIN):
    """Catálogo de canales de venta.
    Ejemplos: mostrador, mesa, telefono, whatsapp, web, app,
              rappi, uber_eats, didi, preorden, catering.
    """
    __tablename__ = "tortas_canal_venta"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    # mostrador, mesa, telefono, whatsapp, web, app, rappi, uber_eats, didi, preorden, catering, otro
    codigo = Column(String(50), nullable=False, unique=True)
    activo = Column(Boolean, default=True)
    sequence = Column(Integer, default=10)
    icono = Column(String(100), default="fa-store")
    descripcion = Column(Text, default="")
    requiere_confirmacion = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())


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

    # KPIs calculados al cerrar el corte
    total_ventas = Column(Float, default=0.0)        # suma de todos los pedidos
    total_efectivo = Column(Float, default=0.0)
    total_tarjeta = Column(Float, default=0.0)
    total_transferencia = Column(Float, default=0.0)
    total_otros = Column(Float, default=0.0)
    total_descuentos = Column(Float, default=0.0)
    total_cupones = Column(Float, default=0.0)
    total_anulaciones = Column(Float, default=0.0)
    total_devoluciones = Column(Float, default=0.0)
    num_pedidos = Column(Integer, default=0)
    num_anulaciones = Column(Integer, default=0)
    num_devoluciones = Column(Integer, default=0)
    turno_id = Column(Integer, ForeignKey("tortas_turno.id"), nullable=True)
    caja_id = Column(Integer, ForeignKey("tortas_caja.id"), nullable=True)

    turno = relationship("TortasTurno", back_populates="cortes")
    caja = relationship("TortasCaja", back_populates="cortes")
    pedidos = relationship("TortasPedido", back_populates="corte_caja")
    pagos = relationship("TortasPago", back_populates="corte_caja")
    anulaciones = relationship("TortasAnulacion", back_populates="corte_caja")
    devoluciones = relationship("TortasDevolucion", back_populates="corte_caja")


# ── Pedidos ───────────────────────────────────────────────────────────────────


# ── Fase 3: Clientes ──────────────────────────────────────────────────────────

class TortasCliente(MAIN):
    """Ficha del cliente. Puede tener múltiples direcciones guardadas
    e historial de pedidos."""
    __tablename__ = "tortas_cliente"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)
    telefono = Column(String(50), default="", index=True)
    email = Column(String(255), default="", index=True)
    fecha_nacimiento = Column(DateTime, nullable=True)
    activo = Column(Boolean, default=True)
    # preferencias / restricciones alimentarias en texto libre
    notas = Column(Text, default="")
    # Fidelización
    puntos_acumulados = Column(Integer, default=0)
    puntos_canjeados = Column(Integer, default=0)
    # bronce | plata | oro | platino
    nivel_fidelidad = Column(String(20), default="bronce")
    total_historico = Column(Float, default=0.0)   # suma de todos sus pedidos pagados
    num_pedidos = Column(Integer, default=0)
    ultimo_pedido_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    direcciones = relationship(
        "TortasDireccionCliente", back_populates="cliente",
        cascade="all, delete-orphan", order_by="TortasDireccionCliente.id"
    )
    pedidos = relationship("TortasPedido", back_populates="cliente")
    puntos_historial = relationship(
        "TortasPuntosHistorial", back_populates="cliente",
        cascade="all, delete-orphan", order_by="TortasPuntosHistorial.created_at.desc()"
    )
    preferencias = relationship(
        "TortasPreferenciaCliente", back_populates="cliente",
        cascade="all, delete-orphan"
    )
    promociones = relationship("TortasPromocionCliente", back_populates="cliente")
    recompensas_usadas = relationship("TortasRecompensaUso", back_populates="cliente")


class TortasDireccionCliente(MAIN):
    """Direcciones guardadas de un cliente (libro de domicilios)."""
    __tablename__ = "tortas_direccion_cliente"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey("tortas_cliente.id"), nullable=False)
    alias = Column(String(100), default="")          # Casa, Oficina, etc.
    calle = Column(String(255), default="")
    numero_exterior = Column(String(30), default="")
    numero_interior = Column(String(30), default="")
    colonia = Column(String(255), default="")
    ciudad = Column(String(255), default="")
    estado_geografico = Column(String(100), default="")
    codigo_postal = Column(String(20), default="")
    referencias = Column(Text, default="")
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    predeterminada = Column(Boolean, default=False)
    activa = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    cliente = relationship("TortasCliente", back_populates="direcciones")

class TortasPedido(MAIN):
    __tablename__ = "tortas_pedido"

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_pedido = Column(String(50), nullable=False, unique=True, index=True)
    fecha_pedido = Column(DateTime, nullable=False, default=func.now())
    nombre_cliente = Column(String(255), default="")
    telefono = Column(String(50), default="")
    email = Column(String(255), default="")
    # mostrador, mesa, para_llevar, domicilio, preorden, catering
    tipo_pedido = Column(String(30), nullable=False, default="mostrador")
    # Cliente formal registrado (opcional, puede quedar como anónimo)
    cliente_id = Column(Integer, ForeignKey("tortas_cliente.id"), nullable=True)
    # Dirección guardada del cliente (opcional)
    direccion_cliente_id = Column(Integer, ForeignKey("tortas_direccion_cliente.id"), nullable=True)
    # Canal por donde llegó el pedido (FK a TortasCanalVenta)
    canal_venta_id = Column(Integer, ForeignKey("tortas_canal_venta.id"), nullable=True)
    zona_entrega_id = Column(Integer, ForeignKey("tortas_zona_entrega.id"), nullable=True)
    costo_envio = Column(Float, default=0.0)
    tiempo_entrega_estimado = Column(Integer, default=0)
    direccion_entrega = Column(Text, default="")
    colonia = Column(String(255), default="")
    codigo_postal = Column(String(20), default="")
    referencias = Column(Text, default="")
    # borrador, confirmado, enviado_cocina, en_preparacion, en_empaque,
    # listo, en_reparto, entregado, no_entregado, cancelado
    estado = Column(String(30), nullable=False, default="borrador", index=True)
    prioridad = Column(String(10), nullable=False, default="normal")  # baja, normal, alta, urgente
    fecha_confirmacion = Column(DateTime, nullable=True)
    fecha_inicio_preparacion = Column(DateTime, nullable=True)
    fecha_listo = Column(DateTime, nullable=True)
    fecha_entregado = Column(DateTime, nullable=True)
    fecha_entrega_programada = Column(DateTime, nullable=True)
    # Hora prometida al cliente (la que se le comunica, puede diferir de la estimada)
    tiempo_prometido = Column(DateTime, nullable=True)
    # Seguimiento de confirmación
    confirmacion_enviada = Column(Boolean, default=False)
    referencia_confirmacion = Column(String(255), default="")  # id chat WA, folio llamada, etc.
    ticket_impreso = Column(Boolean, default=False)
    notas_cocina = Column(Text, default="")
    descuento = Column(Float, default=0.0)
    impuesto = Column(Float, default=0.0)  # porcentaje
    notas = Column(Text, default="")
    cupon_id = Column(Integer, ForeignKey("tortas_cupon.id"), nullable=True)
    codigo_cupon = Column(String(50), default="")
    corte_caja_id = Column(Integer, ForeignKey("tortas_corte_caja.id"), nullable=True)
    turno_id = Column(Integer, ForeignKey("tortas_turno.id"), nullable=True)
    caja_id = Column(Integer, ForeignKey("tortas_caja.id"), nullable=True)
    usuario = Column(String(255), default="")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    cliente = relationship("TortasCliente", back_populates="pedidos")
    direccion_cliente = relationship("TortasDireccionCliente")
    canal_venta = relationship("TortasCanalVenta")
    zona_entrega = relationship("TortasZonaEntrega")
    mensajes = relationship("TortasMensajePedido", back_populates="pedido", cascade="all, delete-orphan")
    origen = relationship("TortasOrigenPedido", back_populates="pedido", uselist=False, cascade="all, delete-orphan")
    tickets_cocina = relationship("TortasTicketCocina", back_populates="pedido", cascade="all, delete-orphan")
    cupon = relationship("TortasCupon")
    corte_caja = relationship("TortasCorteCaja", back_populates="pedidos")
    lineas = relationship("TortasPedidoLinea", back_populates="pedido", cascade="all, delete-orphan")
    pagos = relationship("TortasPago", back_populates="pedido", cascade="all, delete-orphan")
    propinas = relationship("TortasPropina", back_populates="pedido", cascade="all, delete-orphan")
    entrega = relationship("TortasEntrega", back_populates="pedido", uselist=False, cascade="all, delete-orphan")
    turno = relationship("TortasTurno", back_populates="pedidos")
    caja = relationship("TortasCaja", back_populates="pedidos")


class TortasPedidoLinea(MAIN):
    __tablename__ = "tortas_pedido_linea"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("tortas_pedido.id"), nullable=False)
    sequence = Column(Integer, default=10)
    torta_id = Column(Integer, ForeignKey("tortas_torta.id"), nullable=False)
    descripcion = Column(Text, default="")
    cantidad = Column(Integer, nullable=False, default=1)
    variante_id = Column(Integer, ForeignKey("tortas_variante.id"), nullable=True)
    precio_variante = Column(Float, default=0.0)
    base_id = Column(Integer, ForeignKey("tortas_base_producto.id"), nullable=True)
    precio_base = Column(Float, default=0.0)
    precio_unitario = Column(Float, nullable=False, default=0.0)
    notas = Column(Text, default="")

    pedido = relationship("TortasPedido", back_populates="lineas")
    torta = relationship("TortasBase")
    variante = relationship("TortasVariante")
    base = relationship("TortasBaseProducto")
    toppings = relationship("TortasPedidoLineaTopping", back_populates="linea", cascade="all, delete-orphan")
    modificadores = relationship("TortasPedidoLineaModificador", back_populates="linea", cascade="all, delete-orphan")


class TortasPedidoLineaTopping(MAIN):
    __tablename__ = "tortas_pedido_linea_topping"

    id = Column(Integer, primary_key=True, autoincrement=True)
    linea_id = Column(Integer, ForeignKey("tortas_pedido_linea.id"), nullable=False)
    topping_id = Column(Integer, ForeignKey("tortas_topping.id"), nullable=False)
    cantidad = Column(Integer, default=1)
    precio_unitario = Column(Float, nullable=False, default=0.0)

    linea = relationship("TortasPedidoLinea", back_populates="toppings")
    topping = relationship("TortasTopping")


class TortasPedidoLineaModificador(MAIN):
    """Opción de modificador seleccionada en una línea de pedido.
    Usa la estructura de grupos/opciones de Fase 2 (estructurada).
    """
    __tablename__ = "tortas_pedido_linea_modificador"

    id = Column(Integer, primary_key=True, autoincrement=True)
    linea_id = Column(Integer, ForeignKey("tortas_pedido_linea.id"), nullable=False)
    opcion_id = Column(Integer, ForeignKey("tortas_opcion_modificador.id"), nullable=False)
    cantidad = Column(Integer, default=1)
    precio_unitario = Column(Float, nullable=False, default=0.0)

    linea = relationship("TortasPedidoLinea", back_populates="modificadores")
    opcion = relationship("TortasOpcionModificador")

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
    tipo_pedido = Column(String(30), nullable=False, default="para_llevar")
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
    variante_id = Column(Integer, ForeignKey("tortas_variante.id"), nullable=True)
    precio_variante = Column(Float, default=0.0)
    base_id = Column(Integer, ForeignKey("tortas_base_producto.id"), nullable=True)
    precio_base = Column(Float, default=0.0)
    precio_unitario = Column(Float, nullable=False, default=0.0)
    notas = Column(Text, default="")

    preorden = relationship("TortasPreorden", back_populates="lineas")
    torta = relationship("TortasBase")
    variante = relationship("TortasVariante")
    base = relationship("TortasBaseProducto")
    toppings = relationship("TortasPreordenLineaTopping", back_populates="linea", cascade="all, delete-orphan")
    modificadores = relationship("TortasPreordenLineaModificador", back_populates="linea", cascade="all, delete-orphan")


class TortasPreordenLineaTopping(MAIN):
    __tablename__ = "tortas_preorden_linea_topping"

    id = Column(Integer, primary_key=True, autoincrement=True)
    linea_id = Column(Integer, ForeignKey("tortas_preorden_linea.id"), nullable=False)
    topping_id = Column(Integer, ForeignKey("tortas_topping.id"), nullable=False)
    cantidad = Column(Integer, default=1)
    precio_unitario = Column(Float, nullable=False, default=0.0)

    linea = relationship("TortasPreordenLinea", back_populates="toppings")
    topping = relationship("TortasTopping")


class TortasPreordenLineaModificador(MAIN):
    """Opción de modificador seleccionada en una línea de preorden."""
    __tablename__ = "tortas_preorden_linea_modificador"

    id = Column(Integer, primary_key=True, autoincrement=True)
    linea_id = Column(Integer, ForeignKey("tortas_preorden_linea.id"), nullable=False)
    opcion_id = Column(Integer, ForeignKey("tortas_opcion_modificador.id"), nullable=False)
    cantidad = Column(Integer, default=1)
    precio_unitario = Column(Float, nullable=False, default=0.0)

    linea = relationship("TortasPreordenLinea", back_populates="modificadores")
    opcion = relationship("TortasOpcionModificador")


# ── Fase 4: Pedidos telefónicos y WhatsApp ───────────────────────────────────

class TortasPlantillaMensaje(MAIN):
    """Plantillas de mensaje reutilizables para confirmaciones, seguimiento y
    notificaciones por WhatsApp, SMS o teléfono.

    Variables disponibles en el cuerpo (se sustituyen en runtime):
      {nombre}           nombre del cliente
      {numero_pedido}    número de pedido
      {total}            total del pedido
      {tiempo_prometido} hora prometida
      {canal}            canal de venta
      {items}            resumen de artículos
    """
    __tablename__ = "tortas_plantilla_mensaje"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    # confirmacion, seguimiento, listo, en_reparto, entregado, cancelado,
    # no_contesta, bienvenida, encuesta, otro
    tipo = Column(String(50), nullable=False, default="confirmacion")
    # whatsapp, sms, telefono, todos
    canal = Column(String(30), nullable=False, default="whatsapp")
    cuerpo = Column(Text, nullable=False, default="")
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class TortasMensajePedido(MAIN):
    """Registro de mensajes enviados y/o recibidos asociados a un pedido.
    Permite auditar la comunicación con el cliente por canal.
    """
    __tablename__ = "tortas_mensaje_pedido"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("tortas_pedido.id"), nullable=False)
    # enviado | recibido
    direccion = Column(String(20), nullable=False, default="enviado")
    # whatsapp | sms | telefono | email | sistema
    canal = Column(String(30), nullable=False, default="whatsapp")
    plantilla_id = Column(Integer, ForeignKey("tortas_plantilla_mensaje.id"), nullable=True)
    cuerpo = Column(Text, nullable=False, default="")
    # pendiente | enviado | entregado | leido | fallido
    estado = Column(String(30), nullable=False, default="pendiente")
    referencia_externa = Column(String(255), default="")  # message_id de WA API, etc.
    enviado_por = Column(String(255), default="")   # usuario del sistema
    created_at = Column(DateTime, default=func.now())

    pedido = relationship("TortasPedido", back_populates="mensajes")
    plantilla = relationship("TortasPlantillaMensaje")


class TortasOrigenPedido(MAIN):
    """Metadata del canal de origen de un pedido.
    Captura información operativa del proceso de toma de pedido por teléfono
    o WhatsApp: quién atendió, referencia de conversación, script usado, etc.
    """
    __tablename__ = "tortas_origen_pedido"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("tortas_pedido.id"), nullable=False, unique=True)
    operador_nombre = Column(String(255), default="")    # agente que tomó el pedido
    telefono_origen = Column(String(50), default="")     # número desde el que llamó
    referencia_chat = Column(String(255), default="")    # id de hilo WA, folio llamada
    plataforma = Column(String(50), default="")          # whatsapp_business, twilio, etc.
    script_usado = Column(String(255), default="")       # nombre del script operativo
    notas_operador = Column(Text, default="")
    duracion_llamada_seg = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())

    pedido = relationship("TortasPedido", back_populates="origen")


# ── Fase 5: Cocina y operación interna ───────────────────────────────────────

class TortasEstacionCocina(MAIN):
    """Estaciones de trabajo configurables por concepto de restaurante.

    Ejemplos:
      Tortas / burgers : plancha, armado, empaquetado, bebidas
      Pizza            : horno, armado, corte, empaquetado
      Sushi            : preparacion_rolls, presentacion, empaquetado
      Ensaladas        : bowl_station, aderezos, presentacion
    """
    __tablename__ = "tortas_estacion_cocina"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    codigo = Column(String(50), nullable=False, default="")
    descripcion = Column(Text, default="")
    activa = Column(Boolean, default=True)
    sequence = Column(Integer, default=10)
    color = Column(String(20), default="#6c757d")   # para tablero visual
    icono = Column(String(50), default="fa-fire")
    created_at = Column(DateTime, default=func.now())

    tiempos_produccion = relationship("TortasTiempoProduccion", back_populates="estacion")


class TortasTiempoProduccion(MAIN):
    """Tiempo estimado de preparación de un producto en una estación.
    Permite calcular el tiempo total del pedido sumando por estación.
    """
    __tablename__ = "tortas_tiempo_produccion"

    id = Column(Integer, primary_key=True, autoincrement=True)
    torta_id = Column(Integer, ForeignKey("tortas_torta.id"), nullable=False)
    estacion_id = Column(Integer, ForeignKey("tortas_estacion_cocina.id"), nullable=False)
    variante_id = Column(Integer, ForeignKey("tortas_variante.id"), nullable=True)
    minutos = Column(Integer, nullable=False, default=5)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    torta = relationship("TortasBase")
    estacion = relationship("TortasEstacionCocina", back_populates="tiempos_produccion")
    variante = relationship("TortasVariante")


class TortasTicketCocina(MAIN):
    """Ticket de cocina generado al pasar un pedido a producción.
    Puede existir un ticket por pedido, o por estación (multi-ticket).
    """
    __tablename__ = "tortas_ticket_cocina"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("tortas_pedido.id"), nullable=False)
    estacion_id = Column(Integer, ForeignKey("tortas_estacion_cocina.id"), nullable=True)
    numero_ticket = Column(String(50), nullable=False, unique=True, index=True)
    # pendiente | en_preparacion | listo | cancelado
    estado = Column(String(30), nullable=False, default="pendiente")
    prioridad = Column(String(10), default="normal")  # baja | normal | alta | urgente
    notas = Column(Text, default="")
    impreso = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    inicio_preparacion = Column(DateTime, nullable=True)
    listo_at = Column(DateTime, nullable=True)

    pedido = relationship("TortasPedido", back_populates="tickets_cocina")
    estacion = relationship("TortasEstacionCocina")
    lineas = relationship(
        "TortasTicketCocinaLinea", back_populates="ticket",
        cascade="all, delete-orphan", order_by="TortasTicketCocinaLinea.id"
    )


class TortasTicketCocinaLinea(MAIN):
    """Ítem individual en el ticket de cocina con su estado de preparación."""
    __tablename__ = "tortas_ticket_cocina_linea"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tortas_ticket_cocina.id"), nullable=False)
    pedido_linea_id = Column(Integer, ForeignKey("tortas_pedido_linea.id"), nullable=True)
    descripcion = Column(Text, nullable=False, default="")
    cantidad = Column(Integer, default=1)
    variante = Column(String(255), default="")
    modificadores_texto = Column(Text, default="")  # resumen legible de modificadores
    notas = Column(Text, default="")
    # pendiente | en_preparacion | listo | cancelado
    estado = Column(String(30), nullable=False, default="pendiente")
    inicio_preparacion = Column(DateTime, nullable=True)
    listo_at = Column(DateTime, nullable=True)

    ticket = relationship("TortasTicketCocina", back_populates="lineas")
    pedido_linea = relationship("TortasPedidoLinea")


# ── Fase 6: Clientes y fidelización ──────────────────────────────────────────

class TortasPuntosHistorial(MAIN):
    """Registro de cada movimiento de puntos de un cliente.
    ganado: puntos obtenidos tras un pedido.
    canjeado: puntos usados para una recompensa.
    ajuste: corrección manual.
    """
    __tablename__ = "tortas_puntos_historial"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey("tortas_cliente.id"), nullable=False)
    pedido_id = Column(Integer, ForeignKey("tortas_pedido.id"), nullable=True)
    # ganado | canjeado | ajuste | expiracion
    tipo = Column(String(20), nullable=False, default="ganado")
    puntos = Column(Integer, nullable=False)   # positivo=ganado, negativo=canje/exp
    saldo_resultante = Column(Integer, default=0)
    descripcion = Column(String(255), default="")
    created_at = Column(DateTime, default=func.now())
    creado_por = Column(String(255), default="")

    cliente = relationship("TortasCliente", back_populates="puntos_historial")
    pedido = relationship("TortasPedido")


class TortasRecompensa(MAIN):
    """Catálogo de recompensas canjeables con puntos.
    Ejemplos: descuento $20, producto gratis, envío gratis.
    """
    __tablename__ = "tortas_recompensa"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    descripcion = Column(Text, default="")
    # descuento_fijo | descuento_porcentaje | producto_gratis | envio_gratis | otro
    tipo = Column(String(30), nullable=False, default="descuento_fijo")
    valor = Column(Float, default=0.0)      # monto o porcentaje según tipo
    puntos_necesarios = Column(Integer, nullable=False, default=100)
    activa = Column(Boolean, default=True)
    fecha_inicio = Column(DateTime, nullable=True)
    fecha_fin = Column(DateTime, nullable=True)
    limite_usos = Column(Integer, default=0)   # 0 = sin límite
    usos_actuales = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())

    usos = relationship("TortasRecompensaUso", back_populates="recompensa")


class TortasRecompensaUso(MAIN):
    """Registro de canje de una recompensa por un cliente."""
    __tablename__ = "tortas_recompensa_uso"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey("tortas_cliente.id"), nullable=False)
    recompensa_id = Column(Integer, ForeignKey("tortas_recompensa.id"), nullable=False)
    pedido_id = Column(Integer, ForeignKey("tortas_pedido.id"), nullable=True)
    puntos_usados = Column(Integer, nullable=False)
    valor_aplicado = Column(Float, default=0.0)
    created_at = Column(DateTime, default=func.now())

    cliente = relationship("TortasCliente", back_populates="recompensas_usadas")
    recompensa = relationship("TortasRecompensa", back_populates="usos")
    pedido = relationship("TortasPedido")


class TortasPreferenciaCliente(MAIN):
    """Preferencias y restricciones alimentarias estructuradas del cliente.
    Se pueden usar para alertar en cocina o sugerir productos.
    Ejemplos: vegetariano, vegano, sin gluten, sin lactosa, alérgico_cacahuate.
    """
    __tablename__ = "tortas_preferencia_cliente"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey("tortas_cliente.id"), nullable=False)
    # preferencia | restriccion | alergia
    tipo = Column(String(20), nullable=False, default="preferencia")
    nombre = Column(String(255), nullable=False)
    descripcion = Column(String(255), default="")
    activa = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    cliente = relationship("TortasCliente", back_populates="preferencias")


class TortasPromocionCliente(MAIN):
    """Promociones personalizadas asignadas a un cliente específico.
    Descuentos de cumpleaños, compensaciones, ofertas exclusivas, etc.
    """
    __tablename__ = "tortas_promocion_cliente"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey("tortas_cliente.id"), nullable=False)
    name = Column(String(255), nullable=False)
    descripcion = Column(Text, default="")
    # descuento_fijo | descuento_porcentaje | producto_gratis | envio_gratis
    tipo = Column(String(30), nullable=False, default="descuento_fijo")
    valor = Column(Float, default=0.0)
    codigo = Column(String(50), default="", index=True)
    activa = Column(Boolean, default=True)
    fecha_inicio = Column(DateTime, nullable=True)
    fecha_fin = Column(DateTime, nullable=True)
    usos_maximos = Column(Integer, default=1)
    usos_actuales = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())

    cliente = relationship("TortasCliente", back_populates="promociones")


# ── Fase 7: Entrega y logística ───────────────────────────────────────────────

class TortasRepartidor(MAIN):
    """Repartidor o mensajero asignado a entregas a domicilio.
    También puede representar un vehículo propio para pickup.
    """
    __tablename__ = "tortas_repartidor"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)
    telefono = Column(String(50), default="")
    email = Column(String(255), default="")
    # moto | bicicleta | auto | pie | otro
    vehiculo = Column(String(30), default="moto")
    placas = Column(String(30), default="")
    activo = Column(Boolean, default=True)
    disponible = Column(Boolean, default=True)
    notas = Column(Text, default="")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    entregas = relationship("TortasEntrega", back_populates="repartidor")


class TortasEntrega(MAIN):
    """Registro logístico de la entrega de un pedido.
    Una entrega puede ser a domicilio (con repartidor) o pickup.
    Permite rastrear estado, tiempos y evidencia de cierre.
    """
    __tablename__ = "tortas_entrega"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("tortas_pedido.id"), nullable=False, unique=True)
    repartidor_id = Column(Integer, ForeignKey("tortas_repartidor.id"), nullable=True)
    # domicilio | pickup | plataforma_tercero
    tipo = Column(String(30), nullable=False, default="domicilio")
    # pendiente | asignado | en_camino | entregado | fallido | cancelado
    estado = Column(String(20), nullable=False, default="pendiente", index=True)
    tiempo_salida = Column(DateTime, nullable=True)      # cuando salió del local
    tiempo_estimado_llegada = Column(DateTime, nullable=True)
    tiempo_entrega_real = Column(DateTime, nullable=True)  # cuando fue entregado
    distancia_km = Column(Float, default=0.0)
    # Evidencia de entrega (URL foto, firma digital, etc.)
    evidencia_url = Column(Text, default="")
    firma_url = Column(Text, default="")
    # Razón de fallo o cancelación
    motivo_fallo = Column(Text, default="")
    notas = Column(Text, default="")
    # Quién registró el cierre
    cerrado_por = Column(String(255), default="")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    pedido = relationship("TortasPedido", back_populates="entrega")
    repartidor = relationship("TortasRepartidor", back_populates="entregas")


# ── Fase 8: Caja y administración ────────────────────────────────────────────

class TortasCaja(MAIN):
    """Caja física o virtual del local (POS, ventanilla, módulo de WhatsApp, etc.)."""
    __tablename__ = "tortas_caja"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    codigo = Column(String(50), default="", index=True)
    activa = Column(Boolean, default=True)
    descripcion = Column(Text, default="")
    concepto_id = Column(Integer, ForeignKey("tortas_concepto.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())

    pedidos = relationship("TortasPedido", back_populates="caja")
    cortes = relationship("TortasCorteCaja", back_populates="caja")
    turnos = relationship("TortasTurno", back_populates="caja")


class TortasTurno(MAIN):
    """Turno de trabajo de un operador/cajero.
    Agrupa los pedidos y el corte de caja de esa jornada.
    Un turno pertenece a una caja.
    """
    __tablename__ = "tortas_turno"

    id = Column(Integer, primary_key=True, autoincrement=True)
    caja_id = Column(Integer, ForeignKey("tortas_caja.id"), nullable=True)
    usuario = Column(String(255), nullable=False)
    # matutino | vespertino | nocturno | completo
    nombre = Column(String(50), default="completo")
    hora_inicio = Column(DateTime, nullable=False, default=func.now())
    hora_fin = Column(DateTime, nullable=True)
    # abierto | cerrado
    estado = Column(String(20), nullable=False, default="abierto")
    monto_inicial_caja = Column(Float, default=0.0)
    notas = Column(Text, default="")
    created_at = Column(DateTime, default=func.now())

    caja = relationship("TortasCaja", back_populates="turnos")
    pedidos = relationship("TortasPedido", back_populates="turno")
    cortes = relationship("TortasCorteCaja", back_populates="turno")


class TortasAnulacion(MAIN):
    """Registro de anulación de un pedido o de una línea específica.
    Permite llevar control de motivo, autorización y afectación al corte.
    """
    __tablename__ = "tortas_anulacion"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("tortas_pedido.id"), nullable=False)
    corte_caja_id = Column(Integer, ForeignKey("tortas_corte_caja.id"), nullable=True)
    # total | parcial
    tipo = Column(String(20), nullable=False, default="total")
    motivo = Column(String(255), nullable=False, default="")
    descripcion = Column(Text, default="")
    monto_anulado = Column(Float, nullable=False, default=0.0)
    autorizado_por = Column(String(255), default="")
    registrado_por = Column(String(255), default="")
    created_at = Column(DateTime, default=func.now())

    pedido = relationship("TortasPedido")
    corte_caja = relationship("TortasCorteCaja", back_populates="anulaciones")


class TortasDevolucion(MAIN):
    """Registro de devolución (total o parcial) de un pedido ya entregado.
    Puede generar reembolso en efectivo, en crédito o en puntos.
    """
    __tablename__ = "tortas_devolucion"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("tortas_pedido.id"), nullable=False)
    corte_caja_id = Column(Integer, ForeignKey("tortas_corte_caja.id"), nullable=True)
    # efectivo | credito | puntos | sin_reembolso
    tipo_reembolso = Column(String(20), nullable=False, default="efectivo")
    motivo = Column(String(255), nullable=False, default="")
    descripcion = Column(Text, default="")
    monto_devuelto = Column(Float, nullable=False, default=0.0)
    puntos_devueltos = Column(Integer, default=0)
    autorizado_por = Column(String(255), default="")
    registrado_por = Column(String(255), default="")
    created_at = Column(DateTime, default=func.now())

    pedido = relationship("TortasPedido")
    corte_caja = relationship("TortasCorteCaja", back_populates="devoluciones")


# ── Fase 9: Promociones y combos ─────────────────────────────────────────────

class TortasPromocion(MAIN):
    """Motor de promociones automáticas — más potente que TortasCupon.
    Permite definir reglas de activación (horario, canal, día, monto mínimo)
    y acciones (descuento, producto gratis, combo especial).
    Se evalúa automáticamente al crear o cotizar un pedido.
    """
    __tablename__ = "tortas_promocion"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    descripcion = Column(Text, default="")
    activa = Column(Boolean, default=True)
    # ── Acción ──────────────────────────────────────────────────────────────
    # descuento_porcentaje | descuento_fijo | producto_gratis | envio_gratis | combo
    tipo_accion = Column(String(30), nullable=False, default="descuento_porcentaje")
    valor = Column(Float, default=0.0)          # porcentaje o monto según tipo
    descuento_maximo = Column(Float, default=0.0)  # tope si es porcentaje
    producto_gratis_id = Column(Integer, ForeignKey("tortas_base.id"), nullable=True)
    # ── Condiciones de activación ────────────────────────────────────────────
    monto_minimo = Column(Float, default=0.0)
    canal_venta_id = Column(Integer, ForeignKey("tortas_canal_venta.id"), nullable=True)
    concepto_id = Column(Integer, ForeignKey("tortas_concepto.id"), nullable=True)
    # JSON serializado: ["0","1","2","3","4","5","6"] — 0=Lunes, 6=Domingo
    dias_semana = Column(Text, default="")     # vacío = todos los días
    hora_desde = Column(Float, nullable=True)  # hora decimal (ej. 12.5 = 12:30)
    hora_hasta = Column(Float, nullable=True)
    fecha_inicio = Column(DateTime, nullable=True)
    fecha_fin = Column(DateTime, nullable=True)
    solo_primera_compra = Column(Boolean, default=False)
    aplica_a = Column(String(20), default="todos")  # todos | categoria | producto
    # Límites de uso
    limite_usos_total = Column(Integer, default=0)   # 0 = sin límite
    limite_usos_cliente = Column(Integer, default=0)
    usos_actuales = Column(Integer, default=0)
    prioridad = Column(Integer, default=10)  # menor número = mayor prioridad
    acumulable = Column(Boolean, default=False)  # si puede combinarse con otras promos
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    canal_venta = relationship("TortasCanalVenta")
    concepto = relationship("TortasConcepto")
    producto_gratis = relationship("TortasBase")
    usos = relationship("TortasPromocionUso", back_populates="promocion", cascade="all, delete-orphan")


class TortasPromocionUso(MAIN):
    """Registro de cada vez que se aplicó una TortasPromocion a un pedido."""
    __tablename__ = "tortas_promocion_uso"

    id = Column(Integer, primary_key=True, autoincrement=True)
    promocion_id = Column(Integer, ForeignKey("tortas_promocion.id"), nullable=False)
    pedido_id = Column(Integer, ForeignKey("tortas_pedido.id"), nullable=True)
    cliente_id = Column(Integer, ForeignKey("tortas_cliente.id"), nullable=True)
    monto_descuento = Column(Float, default=0.0)
    descripcion = Column(String(255), default="")
    created_at = Column(DateTime, default=func.now())

    promocion = relationship("TortasPromocion", back_populates="usos")
    pedido = relationship("TortasPedido")
    cliente = relationship("TortasCliente")


class TortasCombo(MAIN):
    """Combo de productos con precio especial.
    Adaptable por concepto: puede ser "combo torta + refresco" o
    "pizza + pan de ajo + refresco", según los productos definidos en sus líneas.
    """
    __tablename__ = "tortas_combo"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    descripcion = Column(Text, default="")
    concepto_id = Column(Integer, ForeignKey("tortas_concepto.id"), nullable=True)
    precio_combo = Column(Float, nullable=False, default=0.0)
    activo = Column(Boolean, default=True)
    imagen_url = Column(String(500), default="")
    disponible = Column(Boolean, default=True)
    fecha_inicio = Column(DateTime, nullable=True)
    fecha_fin = Column(DateTime, nullable=True)
    # Si el precio_combo es 0, el descuento se calcula sumando las líneas
    descuento_porcentaje = Column(Float, default=0.0)
    created_at = Column(DateTime, default=func.now())

    concepto = relationship("TortasConcepto")
    lineas = relationship("TortasComboLinea", back_populates="combo", cascade="all, delete-orphan")


class TortasComboLinea(MAIN):
    """Un ítem dentro de un combo (producto + cantidad + si es intercambiable)."""
    __tablename__ = "tortas_combo_linea"

    id = Column(Integer, primary_key=True, autoincrement=True)
    combo_id = Column(Integer, ForeignKey("tortas_combo.id"), nullable=False)
    producto_id = Column(Integer, ForeignKey("tortas_base.id"), nullable=True)
    # Si es True el cliente puede elegir cualquier producto de la categoría
    es_opcional = Column(Boolean, default=False)
    categoria_id = Column(Integer, ForeignKey("tortas_categoria.id"), nullable=True)
    cantidad = Column(Integer, default=1)
    precio_unitario = Column(Float, default=0.0)   # precio individual de referencia
    descripcion = Column(String(255), default="")

    combo = relationship("TortasCombo", back_populates="lineas")
    producto = relationship("TortasBase")
    categoria = relationship("TortasCategoria")


# ── Fase 10: Inventario y recetas ─────────────────────────────────────────────

class TortasInsumo(MAIN):
    """Insumo o ingrediente del inventario.
    Puede ser un producto genérico (harina, queso, refresco, caja) o
    específico de un concepto (chile chipotle para tacos, etc.).
    """
    __tablename__ = "tortas_insumo"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    descripcion = Column(Text, default="")
    # gramo | kilogramo | litro | mililitro | pieza | caja | paquete | otro
    unidad = Column(String(30), nullable=False, default="pieza")
    stock_actual = Column(Float, default=0.0)
    stock_minimo = Column(Float, default=0.0)    # dispara alerta si stock_actual < stock_minimo
    costo_unitario = Column(Float, default=0.0)  # costo por unidad para calcular merma
    activo = Column(Boolean, default=True)
    # Si True, se descuenta automáticamente del stock al vender
    descuento_automatico = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    movimientos = relationship(
        "TortasMovimientoInsumo", back_populates="insumo",
        cascade="all, delete-orphan", order_by="TortasMovimientoInsumo.created_at.desc()"
    )
    lineas_receta = relationship("TortasRecetaLinea", back_populates="insumo")
    opciones_modificador = relationship("TortasOpcionModificadorInsumo", back_populates="insumo")


class TortasMovimientoInsumo(MAIN):
    """Log de entradas y salidas de stock de un insumo.
    entrada: compra o ajuste positivo.
    salida: consumo por venta o merma.
    ajuste: corrección manual de inventario.
    """
    __tablename__ = "tortas_movimiento_insumo"

    id = Column(Integer, primary_key=True, autoincrement=True)
    insumo_id = Column(Integer, ForeignKey("tortas_insumo.id"), nullable=False)
    pedido_id = Column(Integer, ForeignKey("tortas_pedido.id"), nullable=True)
    # entrada | salida | ajuste | merma
    tipo = Column(String(20), nullable=False, default="entrada")
    cantidad = Column(Float, nullable=False)          # positiva=entrada, negativa=salida
    stock_resultante = Column(Float, default=0.0)
    costo_unitario = Column(Float, default=0.0)
    descripcion = Column(String(255), default="")
    creado_por = Column(String(255), default="")
    created_at = Column(DateTime, default=func.now())

    insumo = relationship("TortasInsumo", back_populates="movimientos")
    pedido = relationship("TortasPedido")


class TortasReceta(MAIN):
    """Receta de un producto (TortasBase).
    Define qué insumos y en qué cantidades se consumen al elaborar el producto.
    Una receta puede tener variante (ej. receta de torta chica vs grande).
    """
    __tablename__ = "tortas_receta"

    id = Column(Integer, primary_key=True, autoincrement=True)
    producto_id = Column(Integer, ForeignKey("tortas_base.id"), nullable=False)
    variante_id = Column(Integer, ForeignKey("tortas_variante.id"), nullable=True)
    name = Column(String(255), nullable=False, default="Receta estándar")
    activa = Column(Boolean, default=True)
    porciones = Column(Integer, default=1)   # cuántas porciones produce esta receta
    notas = Column(Text, default="")
    created_at = Column(DateTime, default=func.now())

    producto = relationship("TortasBase")
    variante = relationship("TortasVariante")
    lineas = relationship(
        "TortasRecetaLinea", back_populates="receta",
        cascade="all, delete-orphan"
    )


class TortasRecetaLinea(MAIN):
    """Un insumo dentro de una receta con la cantidad requerida."""
    __tablename__ = "tortas_receta_linea"

    id = Column(Integer, primary_key=True, autoincrement=True)
    receta_id = Column(Integer, ForeignKey("tortas_receta.id"), nullable=False)
    insumo_id = Column(Integer, ForeignKey("tortas_insumo.id"), nullable=False)
    cantidad = Column(Float, nullable=False, default=1.0)
    unidad = Column(String(30), default="")   # puede diferir de la unidad base del insumo
    notas = Column(String(255), default="")

    receta = relationship("TortasReceta", back_populates="lineas")
    insumo = relationship("TortasInsumo", back_populates="lineas_receta")


class TortasOpcionModificadorInsumo(MAIN):
    """Consumo de insumo adicional al elegir una opción de modificador.
    Ej: al elegir "extra queso" en un modificador, se consumen 30g de queso del insumo #12.
    """
    __tablename__ = "tortas_opcion_modificador_insumo"

    id = Column(Integer, primary_key=True, autoincrement=True)
    opcion_id = Column(Integer, ForeignKey("tortas_opcion_modificador.id"), nullable=False)
    insumo_id = Column(Integer, ForeignKey("tortas_insumo.id"), nullable=False)
    cantidad = Column(Float, nullable=False, default=1.0)
    unidad = Column(String(30), default="")

    opcion = relationship("TortasOpcionModificador")
    insumo = relationship("TortasInsumo", back_populates="opciones_modificador")


# ── Fase 12: Automatización e integración ─────────────────────────────────────

class TortasEventoSistema(MAIN):
    """Log inmutable de eventos del sistema.
    Se usa para auditoría, trazabilidad y como base para automatizaciones.
    Cada cambio de estado, mensaje enviado o acción automática queda registrada.
    """
    __tablename__ = "tortas_evento_sistema"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # cambio_estado | mensaje_enviado | webhook_disparado | automatizacion_ejecutada
    # pago_registrado | stock_descontado | cupon_aplicado | promocion_aplicada
    tipo_evento = Column(String(80), nullable=False, index=True)
    # pedido | cliente | insumo | turno | preorden | sistema
    entidad = Column(String(50), nullable=False, default="pedido")
    entidad_id = Column(Integer, nullable=True, index=True)
    payload_json = Column(Text, default="{}")   # contexto serializado en JSON
    actor = Column(String(255), default="sistema")   # usuario o proceso
    resultado = Column(String(30), default="ok")     # ok | error | omitido
    detalle = Column(Text, default="")
    created_at = Column(DateTime, default=func.now())


class TortasAutomatizacion(MAIN):
    """Regla de automatización: cuando ocurre un evento, disparar una acción.

    Ejemplo:
      evento_disparador = 'cambio_estado'
      condicion_estado  = 'confirmado'
      accion_tipo       = 'enviar_mensaje'
      plantilla_id      = 3   (plantilla de confirmación por WhatsApp)
      canal             = 'whatsapp'

    accion_tipo opciones:
      enviar_mensaje    → usa plantilla_id + canal
      cambiar_estado    → cambia el pedido a estado_destino
      registrar_evento  → solo lo registra sin acción adicional
    """
    __tablename__ = "tortas_automatizacion"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    descripcion = Column(Text, default="")
    activa = Column(Boolean, default=True)
    prioridad = Column(Integer, default=10)  # menor = mayor prioridad
    # Disparador
    # cambio_estado | pago_registrado | entrega_asignada | stock_bajo
    # preorden_creada | cupon_aplicado | pedido_creado
    evento_disparador = Column(String(80), nullable=False)
    # Si evento = 'cambio_estado', el estado que activa la regla
    condicion_estado = Column(String(30), default="")
    # Filtros adicionales (opcional)
    canal_venta_id = Column(Integer, ForeignKey("tortas_canal_venta.id"), nullable=True)
    concepto_id = Column(Integer, ForeignKey("tortas_concepto.id"), nullable=True)
    # Acción
    accion_tipo = Column(String(40), nullable=False, default="enviar_mensaje")
    plantilla_id = Column(Integer, ForeignKey("tortas_plantilla_mensaje.id"), nullable=True)
    # Canal por el que se envía el mensaje (whatsapp | sms | email | todos)
    canal_mensaje = Column(String(30), default="whatsapp")
    # Si accion_tipo = 'cambiar_estado', el nuevo estado
    estado_destino = Column(String(30), default="")
    # Delay en segundos antes de ejecutar (0 = inmediato)
    delay_seg = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    canal_venta = relationship("TortasCanalVenta")
    concepto = relationship("TortasConcepto")
    plantilla = relationship("TortasPlantillaMensaje")


class TortasWebhookSalida(MAIN):
    """Configuración de un webhook hacia sistema externo.
    Cuando ocurre un evento, se puede notificar a una URL externa (POS, CRM, WA Business API, etc.).
    """
    __tablename__ = "tortas_webhook_salida"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    # Lista de eventos que disparan este webhook (separados por coma)
    eventos = Column(Text, default="")
    # Cabecera de autenticación (Bearer token, API key, etc.) — cifrado en producción
    header_auth = Column(Text, default="")
    activo = Column(Boolean, default=True)
    # Último envío
    ultimo_estado = Column(String(20), default="")   # ok | error
    ultimo_error = Column(Text, default="")
    ultimo_envio_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


# ── Creación de tablas ────────────────────────────────────────────────────────

def ensure_tortas_schema(bind=None) -> None:
    from fastapi_modulo.core.db import get_current_engine
    target = bind or get_current_engine()
    ordered = [
        TortasCategoria.__table__,
        TortasAlergeno.__table__,
        TortasTipoAlimento.__table__,
        TortasBaseProducto.__table__,
        TortasTopping.__table__,
        TortasGrupoModificador.__table__,
        TortasOpcionModificador.__table__,
        TortasBase.__table__,
        torta_alergeno,
        torta_tipo_alimento,
        torta_base_producto,
        torta_grupo_modificador,
        topping_alergeno,
        TortasVariante.__table__,
        TortasZonaEntrega.__table__,
        TortasColonia.__table__,
        TortasMetodoEntrega.__table__,
        TortasHorario.__table__,
        TortasDiaFestivo.__table__,
        TortasConfiguracion.__table__,
        TortasConcepto.__table__,
        TortasCanalVenta.__table__,
        TortasFormaPago.__table__,
        TortasCorteCaja.__table__,
        # Fase 3
        TortasCliente.__table__,
        TortasDireccionCliente.__table__,
        TortasPedido.__table__,
        TortasPedidoLinea.__table__,
        TortasPedidoLineaTopping.__table__,
        TortasPedidoLineaModificador.__table__,
        TortasPago.__table__,
        TortasPropina.__table__,
        TortasCupon.__table__,
        cupon_categoria,
        cupon_torta,
        TortasCuponUso.__table__,
        TortasPreorden.__table__,
        TortasPreordenLinea.__table__,
        TortasPreordenLineaTopping.__table__,
        TortasPreordenLineaModificador.__table__,
        # Fase 4
        TortasPlantillaMensaje.__table__,
        TortasMensajePedido.__table__,
        TortasOrigenPedido.__table__,
        # Fase 5
        TortasEstacionCocina.__table__,
        TortasTiempoProduccion.__table__,
        TortasTicketCocina.__table__,
        TortasTicketCocinaLinea.__table__,
        # Fase 6
        TortasRecompensa.__table__,
        TortasPuntosHistorial.__table__,
        TortasRecompensaUso.__table__,
        TortasPreferenciaCliente.__table__,
        TortasPromocionCliente.__table__,
        # Fase 7
        TortasRepartidor.__table__,
        TortasEntrega.__table__,
        # Fase 8
        TortasCaja.__table__,
        TortasTurno.__table__,
        TortasAnulacion.__table__,
        TortasDevolucion.__table__,
        # Fase 9
        TortasPromocion.__table__,
        TortasPromocionUso.__table__,
        TortasCombo.__table__,
        TortasComboLinea.__table__,
        # Fase 10
        TortasInsumo.__table__,
        TortasMovimientoInsumo.__table__,
        TortasReceta.__table__,
        TortasRecetaLinea.__table__,
        TortasOpcionModificadorInsumo.__table__,
        # Fase 12
        TortasEventoSistema.__table__,
        TortasAutomatizacion.__table__,
        TortasWebhookSalida.__table__,
    ]
    for t in ordered:
        t.create(bind=target, checkfirst=True)
