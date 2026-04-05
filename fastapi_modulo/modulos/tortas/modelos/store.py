from __future__ import annotations
from datetime import date, datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from fastapi_modulo.modulos.tortas.modelos.db_models import (
    TortasCategoria, TortasAlergeno, TortasTipoAlimento, TortasBaseProducto,
    TortasTopping, TortasBase, TortasZonaEntrega, TortasMetodoEntrega,
    TortasFormaPago, TortasCupon, TortasCuponUso,
    TortasCorteCaja, TortasPedido, TortasPedidoLinea, TortasPedidoLineaTopping,
    TortasPedidoLineaModificador, TortasOpcionModificador, TortasGrupoModificador,
    TortasPago, TortasPropina,
    TortasPreorden, TortasPreordenLinea, TortasPreordenLineaTopping,
    TortasConfiguracion, TortasCanalVenta, TortasConcepto,
    # Fase 3
    TortasCliente, TortasDireccionCliente,
    # Fase 4
    TortasPlantillaMensaje, TortasMensajePedido, TortasOrigenPedido,
    # Fase 5
    TortasEstacionCocina, TortasTiempoProduccion,
    TortasTicketCocina, TortasTicketCocinaLinea,
    # Fase 6
    TortasPuntosHistorial, TortasRecompensa, TortasRecompensaUso,
    TortasPreferenciaCliente, TortasPromocionCliente,
    # Fase 7
    TortasRepartidor, TortasEntrega,
    # Fase 8
    TortasCaja, TortasTurno, TortasAnulacion, TortasDevolucion,
    # Fase 9
    TortasPromocion, TortasPromocionUso, TortasCombo, TortasComboLinea,
    # Fase 10
    TortasInsumo, TortasMovimientoInsumo,
    TortasReceta, TortasRecetaLinea, TortasOpcionModificadorInsumo,
    # Fase 12
    TortasEventoSistema, TortasAutomatizacion, TortasWebhookSalida,
)
from fastapi_modulo.modulos.tortas.modelos.schemas import (
    CategoriaCreate, AlergenoCreate, BaseProductoCreate, BaseProductoUpdate,
    ToppingCreate, TortaCreate, TortaUpdate,
    ZonaEntregaCreate, ZonaEntregaUpdate, FormaPagoCreate,
    CanalVentaCreate, ConceptoCreate,
    CuponCreate, PedidoCreate, PedidoUpdate, PagoCreate, PropinaCreate,
    CorteCajaCreate, CorteCajaCerrarRequest,
    PreordenCreate,
    # Fase 3
    ClienteCreate, ClienteUpdate, DireccionClienteCreate,
    # Fase 4
    PlantillaMensajeCreate, MensajePedidoCreate, OrigenPedidoCreate,
    # Fase 5
    EstacionCocinaCreate, TiempoProduccionCreate, TicketCocinaCreate,
    ActualizarEstadoTicketRequest, ActualizarEstadoLineaTicketRequest,
    # Fase 6
    AjustePuntosRequest, RecompensaCreate, CanjearRecompensaRequest,
    PreferenciaClienteCreate, PromocionClienteCreate,
    # Fase 7
    RepartidorCreate, EntregaCreate, AsignarRepartidorRequest,
    ActualizarEstadoEntregaRequest, RegistrarEvidenciaRequest,
    # Fase 8
    CajaCreate, TurnoCreate, CerrarTurnoRequest, CerrarCorteRequest,
    AnulacionCreate, DevolucionCreate,
    # Fase 9
    PromocionCreate, EvaluarPromocionesRequest,
    ComboCreate, ComboLineaCreate,
    # Fase 10
    InsumoCreate, MovimientoInsumoCreate,
    RecetaCreate, RecetaLineaCreate, OpcionModificadorInsumoCreate,
    DescontarStockPedidoRequest, AjusteStockRequest,
    # Fase 12
    AutomatizacionCreate, WebhookSalidaCreate, DisparadorEventoRequest,
)


# ── Categorías ────────────────────────────────────────────────────────────────

def list_categorias(db: Session, solo_activas: bool = True) -> List[TortasCategoria]:
    q = db.query(TortasCategoria)
    if solo_activas:
        q = q.filter(TortasCategoria.active == True)
    return q.order_by(TortasCategoria.name).all()


def get_categoria(db: Session, categoria_id: int) -> Optional[TortasCategoria]:
    return db.query(TortasCategoria).filter(TortasCategoria.id == categoria_id).first()


def create_categoria(db: Session, data: CategoriaCreate) -> TortasCategoria:
    obj = TortasCategoria(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ── Alérgenos ─────────────────────────────────────────────────────────────────

def list_alergenos(db: Session) -> List[TortasAlergeno]:
    return db.query(TortasAlergeno).filter(TortasAlergeno.activo == True).order_by(TortasAlergeno.sequence, TortasAlergeno.name).all()


def create_alergeno(db: Session, data: AlergenoCreate) -> TortasAlergeno:
    obj = TortasAlergeno(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ── Bases del producto ────────────────────────────────────────────────────────
# Genérico: pan/telera (tortas), masa (pizza), arroz/bowl (sushi),
#           wrap/tortilla (burritos). Label configurable por concepto.

def list_bases_producto(db: Session, solo_activos: bool = True) -> List[TortasBaseProducto]:
    q = db.query(TortasBaseProducto)
    if solo_activos:
        q = q.filter(TortasBaseProducto.activo == True)
    return q.order_by(TortasBaseProducto.sequence, TortasBaseProducto.nombre).all()


def get_base_producto(db: Session, base_id: int) -> Optional[TortasBaseProducto]:
    return db.query(TortasBaseProducto).filter(TortasBaseProducto.id == base_id).first()


def create_base_producto(db: Session, data: BaseProductoCreate) -> TortasBaseProducto:
    obj = TortasBaseProducto(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_base_producto(db: Session, base_id: int, data: BaseProductoUpdate) -> Optional[TortasBaseProducto]:
    obj = get_base_producto(db, base_id)
    if not obj:
        return None
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


# ── Toppings ──────────────────────────────────────────────────────────────────

def list_toppings(db: Session, solo_activos: bool = True) -> List[TortasTopping]:
    q = db.query(TortasTopping)
    if solo_activos:
        q = q.filter(TortasTopping.active == True)
    return q.order_by(TortasTopping.sort_order, TortasTopping.name).all()


def get_topping(db: Session, topping_id: int) -> Optional[TortasTopping]:
    return db.query(TortasTopping).filter(TortasTopping.id == topping_id).first()


def create_topping(db: Session, data: ToppingCreate) -> TortasTopping:
    obj = TortasTopping(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ── Tortas (menú) ─────────────────────────────────────────────────────────────

def list_tortas(db: Session, solo_activas: bool = True, categoria_id: Optional[int] = None) -> List[TortasBase]:
    q = db.query(TortasBase)
    if solo_activas:
        q = q.filter(TortasBase.active == True)
    if categoria_id:
        q = q.filter(TortasBase.categoria_id == categoria_id)
    return q.order_by(TortasBase.name).all()


def get_torta(db: Session, torta_id: int) -> Optional[TortasBase]:
    return db.query(TortasBase).filter(TortasBase.id == torta_id).first()


def create_torta(db: Session, data: TortaCreate) -> TortasBase:
    obj = TortasBase(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_torta(db: Session, torta_id: int, data: TortaUpdate) -> Optional[TortasBase]:
    obj = get_torta(db, torta_id)
    if not obj:
        return None
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


# ── Zonas de entrega ──────────────────────────────────────────────────────────

def list_zonas(db: Session, solo_activas: bool = True) -> List[TortasZonaEntrega]:
    q = db.query(TortasZonaEntrega)
    if solo_activas:
        q = q.filter(TortasZonaEntrega.active == True)
    return q.order_by(TortasZonaEntrega.name).all()


def get_zona(db: Session, zona_id: int) -> Optional[TortasZonaEntrega]:
    return db.query(TortasZonaEntrega).filter(TortasZonaEntrega.id == zona_id).first()


def create_zona(db: Session, data: ZonaEntregaCreate) -> TortasZonaEntrega:
    obj = TortasZonaEntrega(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_zona(db: Session, zona_id: int, data: ZonaEntregaUpdate) -> Optional[TortasZonaEntrega]:
    obj = get_zona(db, zona_id)
    if not obj:
        return None
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def calcular_costo_envio(db: Session, zona_id: int, subtotal: float) -> Tuple[bool, str, float]:
    """Retorna (acepta, mensaje, costo)"""
    zona = get_zona(db, zona_id)
    if not zona:
        return False, "Zona no encontrada", 0.0
    if not zona.acepta_pedidos:
        return False, zona.mensaje_no_disponible, 0.0
    if subtotal < zona.monto_minimo_pedido:
        return False, f"Monto mínimo: ${zona.monto_minimo_pedido:.2f}", 0.0
    if zona.envio_gratis_desde > 0 and subtotal >= zona.envio_gratis_desde:
        return True, "Envío gratis", 0.0
    return True, "", zona.costo_envio


# ── Formas de pago ────────────────────────────────────────────────────────────

def list_formas_pago(db: Session) -> List[TortasFormaPago]:
    return db.query(TortasFormaPago).filter(TortasFormaPago.active == True).order_by(TortasFormaPago.sequence).all()


def get_forma_pago(db: Session, forma_pago_id: int) -> Optional[TortasFormaPago]:
    return db.query(TortasFormaPago).filter(TortasFormaPago.id == forma_pago_id).first()


def create_forma_pago(db: Session, data: FormaPagoCreate) -> TortasFormaPago:
    obj = TortasFormaPago(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ── Cupones ───────────────────────────────────────────────────────────────────

def list_cupones(db: Session) -> List[TortasCupon]:
    return db.query(TortasCupon).filter(TortasCupon.active == True).order_by(TortasCupon.name).all()


def get_cupon_by_codigo(db: Session, codigo: str) -> Optional[TortasCupon]:
    return db.query(TortasCupon).filter(
        TortasCupon.codigo == codigo.strip().upper(),
        TortasCupon.active == True,
    ).first()


def create_cupon(db: Session, data: CuponCreate) -> TortasCupon:
    d = data.model_dump()
    d["codigo"] = d["codigo"].strip().upper()
    obj = TortasCupon(**d)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def validar_cupon(db: Session, codigo: str, subtotal: float) -> Tuple[bool, str, float]:
    """Retorna (valido, mensaje, monto_descuento)"""
    cupon = get_cupon_by_codigo(db, codigo)
    if not cupon:
        return False, "Cupón no encontrado o inactivo", 0.0

    hoy = date.today()
    if hoy < cupon.fecha_inicio:
        return False, f"El cupón es válido desde {cupon.fecha_inicio}", 0.0
    if hoy > cupon.fecha_fin:
        return False, "El cupón ha expirado", 0.0

    total_usos = len(cupon.usos)
    if cupon.uso_maximo > 0 and total_usos >= cupon.uso_maximo:
        return False, "El cupón ha alcanzado su límite de uso", 0.0

    if subtotal < cupon.monto_minimo:
        return False, f"Monto mínimo requerido: ${cupon.monto_minimo:.2f}", 0.0

    # Calcular descuento
    if cupon.tipo_descuento == "porcentaje":
        monto = subtotal * (cupon.valor_descuento / 100.0)
        if cupon.descuento_maximo > 0 and monto > cupon.descuento_maximo:
            monto = cupon.descuento_maximo
    else:
        monto = min(cupon.valor_descuento, subtotal)

    return True, "Cupón válido", round(monto, 2)


# ── Pedidos ───────────────────────────────────────────────────────────────────

def _generar_numero_pedido(pedido_id: int) -> str:
    return f"PED-{pedido_id:05d}"


def list_pedidos(
    db: Session,
    estado: Optional[str] = None,
    limit: int = 100,
) -> List[TortasPedido]:
    q = db.query(TortasPedido)
    if estado:
        q = q.filter(TortasPedido.estado == estado)
    return q.order_by(TortasPedido.fecha_pedido.desc()).limit(limit).all()


def get_pedido(db: Session, pedido_id: int) -> Optional[TortasPedido]:
    return db.query(TortasPedido).filter(TortasPedido.id == pedido_id).first()


def create_pedido(db: Session, data: PedidoCreate) -> TortasPedido:
    lineas_data = data.lineas
    pedido_data = data.model_dump(exclude={"lineas"})
    pedido_data.pop("codigo_cupon", None)

    # Si viene cliente_id, auto-poblar nombre/teléfono si están vacíos
    if data.cliente_id:
        cliente = db.query(TortasCliente).filter(TortasCliente.id == data.cliente_id).first()
        if cliente:
            if not pedido_data.get("nombre_cliente"):
                pedido_data["nombre_cliente"] = cliente.nombre
            if not pedido_data.get("telefono"):
                pedido_data["telefono"] = cliente.telefono

    # Si viene direccion_cliente_id, volcar campos de dirección si están vacíos
    if data.direccion_cliente_id:
        dir_c = db.query(TortasDireccionCliente).filter(
            TortasDireccionCliente.id == data.direccion_cliente_id
        ).first()
        if dir_c:
            if not pedido_data.get("direccion_entrega"):
                pedido_data["direccion_entrega"] = f"{dir_c.calle} {dir_c.numero_exterior}".strip()
            if not pedido_data.get("colonia"):
                pedido_data["colonia"] = dir_c.colonia
            if not pedido_data.get("codigo_postal"):
                pedido_data["codigo_postal"] = dir_c.codigo_postal
            if not pedido_data.get("referencias"):
                pedido_data["referencias"] = dir_c.referencias

    # Placeholder número — se actualiza tras insertar
    pedido_data["numero_pedido"] = "TEMP"
    pedido_data["codigo_cupon"] = data.codigo_cupon

    obj = TortasPedido(**pedido_data)
    db.add(obj)
    db.flush()  # obtiene el id

    obj.numero_pedido = _generar_numero_pedido(obj.id)

    for linea_data in lineas_data:
        toppings_data = linea_data.toppings
        linea_dict = linea_data.model_dump(exclude={"toppings"})
        linea = TortasPedidoLinea(pedido_id=obj.id, **linea_dict)
        db.add(linea)
        db.flush()
        for t in toppings_data:
            db.add(TortasPedidoLineaTopping(linea_id=linea.id, **t.model_dump()))

    db.commit()
    db.refresh(obj)
    return obj


def update_estado_pedido(db: Session, pedido_id: int, estado: str) -> Optional[TortasPedido]:
    obj = get_pedido(db, pedido_id)
    if not obj:
        return None
    obj.estado = estado
    now = datetime.utcnow()
    if estado == "confirmado" and not obj.fecha_confirmacion:
        obj.fecha_confirmacion = now
    elif estado == "en_preparacion" and not obj.fecha_inicio_preparacion:
        obj.fecha_inicio_preparacion = now
    elif estado == "listo" and not obj.fecha_listo:
        obj.fecha_listo = now
    elif estado == "entregado" and not obj.fecha_entregado:
        obj.fecha_entregado = now
    db.commit()
    db.refresh(obj)
    return obj


def _calcular_totales_pedido(pedido: TortasPedido) -> dict:
    subtotal = sum(
        (l.precio_unitario + l.precio_base + sum(t.precio_unitario * t.cantidad for t in l.toppings)) * l.cantidad
        for l in pedido.lineas
    )
    subtotal_desc = subtotal - pedido.descuento
    total_impuesto = subtotal_desc * (pedido.impuesto / 100.0)
    total = subtotal_desc + total_impuesto + pedido.costo_envio
    total_pagado = sum(p.monto for p in pedido.pagos if not p.cancelado)
    return {
        "subtotal": round(subtotal, 2),
        "descuento": round(pedido.descuento, 2),
        "total_impuesto": round(total_impuesto, 2),
        "costo_envio": round(pedido.costo_envio, 2),
        "total": round(total, 2),
        "total_pagado": round(total_pagado, 2),
        "saldo_pendiente": round(total - total_pagado, 2),
    }


def get_dashboard_stats(db: Session) -> dict:
    total = db.query(TortasPedido).count()
    estados = ["borrador", "confirmado", "en_preparacion", "listo", "entregado", "cancelado"]
    por_estado = {e: db.query(TortasPedido).filter(TortasPedido.estado == e).count() for e in estados}

    hoy_inicio = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    pedidos_hoy_q = db.query(TortasPedido).filter(
        TortasPedido.fecha_pedido >= hoy_inicio,
        TortasPedido.estado != "cancelado",
    ).all()
    pedidos_hoy = len(pedidos_hoy_q)

    return {
        "total_pedidos": total,
        "por_estado": por_estado,
        "pedidos_hoy": pedidos_hoy,
    }


# ── Pagos ─────────────────────────────────────────────────────────────────────

def list_pagos_pedido(db: Session, pedido_id: int) -> List[TortasPago]:
    return db.query(TortasPago).filter(TortasPago.pedido_id == pedido_id).all()


def create_pago(db: Session, pedido_id: int, data: PagoCreate) -> TortasPago:
    obj = TortasPago(pedido_id=pedido_id, **data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def cancelar_pago(db: Session, pago_id: int, motivo: str = "") -> Optional[TortasPago]:
    obj = db.query(TortasPago).filter(TortasPago.id == pago_id).first()
    if not obj:
        return None
    obj.cancelado = True
    obj.fecha_cancelacion = datetime.utcnow()
    obj.motivo_cancelacion = motivo
    db.commit()
    db.refresh(obj)
    return obj


# ── Corte de caja ─────────────────────────────────────────────────────────────

def list_cortes(db: Session, limit: int = 50) -> List[TortasCorteCaja]:
    return db.query(TortasCorteCaja).order_by(TortasCorteCaja.fecha_inicio.desc()).limit(limit).all()


def get_corte_abierto(db: Session) -> Optional[TortasCorteCaja]:
    return db.query(TortasCorteCaja).filter(TortasCorteCaja.estado == "abierto").first()


def create_corte(db: Session, data: CorteCajaCreate) -> TortasCorteCaja:
    corte_num = db.query(TortasCorteCaja).count() + 1
    obj = TortasCorteCaja(
        name=f"CORTE-{corte_num:04d}",
        **data.model_dump(),
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def cerrar_corte(db: Session, corte_id: int, req: CorteCajaCerrarRequest) -> Optional[TortasCorteCaja]:
    obj = db.query(TortasCorteCaja).filter(TortasCorteCaja.id == corte_id).first()
    if not obj or obj.estado != "abierto":
        return None

    now = datetime.utcnow()

    # Asociar pagos sin corte dentro del período
    db.query(TortasPago).filter(
        TortasPago.corte_caja_id.is_(None),
        TortasPago.cancelado == False,
        TortasPago.fecha >= obj.fecha_inicio,
        TortasPago.fecha <= now,
    ).update({"corte_caja_id": corte_id})

    # Asociar pedidos sin corte dentro del período
    db.query(TortasPedido).filter(
        TortasPedido.corte_caja_id.is_(None),
        TortasPedido.fecha_pedido >= obj.fecha_inicio,
        TortasPedido.fecha_pedido <= now,
        TortasPedido.estado.in_(["confirmado", "en_preparacion", "listo", "entregado"]),
    ).update({"corte_caja_id": corte_id})

    obj.estado = "cerrado"
    obj.fecha_cierre = now
    obj.efectivo_contado = req.efectivo_contado
    obj.usuario_cierre = req.usuario_cierre
    obj.total_gastos = req.total_gastos
    obj.total_retiros = req.total_retiros
    if req.notas:
        obj.notas = req.notas

    db.commit()
    db.refresh(obj)
    return obj


# ── Preordenes ────────────────────────────────────────────────────────────────

def list_preordenes(db: Session, state: Optional[str] = None, limit: int = 100) -> List[TortasPreorden]:
    q = db.query(TortasPreorden)
    if state:
        q = q.filter(TortasPreorden.state == state)
    return q.order_by(TortasPreorden.fecha_entrega.desc()).limit(limit).all()


def get_preorden(db: Session, preorden_id: int) -> Optional[TortasPreorden]:
    return db.query(TortasPreorden).filter(TortasPreorden.id == preorden_id).first()


def create_preorden(db: Session, data: PreordenCreate) -> TortasPreorden:
    lineas_data = data.lineas
    preorden_data = data.model_dump(exclude={"lineas"})

    num = db.query(TortasPreorden).count() + 1
    preorden_data["name"] = f"PRE-{num:04d}"

    obj = TortasPreorden(**preorden_data)
    db.add(obj)
    db.flush()

    for ld in lineas_data:
        toppings_data = ld.toppings
        linea_dict = ld.model_dump(exclude={"toppings"})
        linea = TortasPreordenLinea(preorden_id=obj.id, **linea_dict)
        db.add(linea)
        db.flush()
        for t in toppings_data:
            db.add(TortasPreordenLineaTopping(linea_id=linea.id, **t.model_dump()))

    db.commit()
    db.refresh(obj)
    return obj


def update_estado_preorden(db: Session, preorden_id: int, state: str) -> Optional[TortasPreorden]:
    obj = get_preorden(db, preorden_id)
    if not obj:
        return None
    obj.state = state
    if state == "recordatorio_enviado":
        obj.recordatorio_enviado = True
        obj.fecha_recordatorio = datetime.utcnow()
    db.commit()
    db.refresh(obj)
    return obj


def generar_pedido_desde_preorden(db: Session, preorden_id: int) -> Optional[TortasPedido]:
    preorden = get_preorden(db, preorden_id)
    if not preorden or preorden.state != "confirmado":
        return None

    from fastapi_modulo.modulos.tortas.modelos.schemas import PedidoCreate, LineaPedidoCreate, LineaToppingCreate

    lineas = [
        LineaPedidoCreate(
            torta_id=l.torta_id,
            cantidad=l.cantidad,
            precio_unitario=l.precio_unitario,
            notas=l.notas,
            toppings=[
                LineaToppingCreate(topping_id=t.topping_id, cantidad=t.cantidad, precio_unitario=t.precio_unitario)
                for t in l.toppings
            ],
        )
        for l in preorden.lineas
    ]

    pedido_data = PedidoCreate(
        nombre_cliente=preorden.nombre_cliente,
        telefono=preorden.telefono,
        email=preorden.email,
        tipo_pedido=preorden.tipo_pedido,
        zona_entrega_id=preorden.zona_entrega_id,
        costo_envio=preorden.costo_envio,
        direccion_entrega=preorden.direccion_entrega,
        notas=f"Generado de Preorden {preorden.name}. {preorden.notas or ''}".strip(),
        lineas=lineas,
    )

    pedido = create_pedido(db, pedido_data)
    pedido.fecha_entrega_programada = datetime.combine(preorden.fecha_entrega, datetime.strptime(preorden.hora_entrega, "%H:%M").time())
    pedido.estado = "confirmado"
    pedido.fecha_confirmacion = datetime.utcnow()

    preorden.state = "pedido_generado"
    preorden.pedido_id = pedido.id

    db.commit()
    db.refresh(pedido)
    return pedido


# ── Canales de venta ──────────────────────────────────────────────────────────

def list_canales_venta(db: Session, solo_activos: bool = True) -> List[TortasCanalVenta]:
    q = db.query(TortasCanalVenta)
    if solo_activos:
        q = q.filter(TortasCanalVenta.activo == True)
    return q.order_by(TortasCanalVenta.sequence, TortasCanalVenta.name).all()


def get_canal_venta(db: Session, canal_id: int) -> Optional[TortasCanalVenta]:
    return db.query(TortasCanalVenta).filter(TortasCanalVenta.id == canal_id).first()


def create_canal_venta(db: Session, data: CanalVentaCreate) -> TortasCanalVenta:
    obj = TortasCanalVenta(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ── Concepto de restaurante ───────────────────────────────────────────────────

def get_concepto(db: Session) -> Optional[TortasConcepto]:
    return db.query(TortasConcepto).filter(TortasConcepto.activo == True).first()


def create_concepto(db: Session, data: ConceptoCreate) -> TortasConcepto:
    obj = TortasConcepto(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj



# ── Fase 6: Clientes y fidelización ──────────────────────────────────────────

# ---- Helpers de nivel de fidelidad ------------------------------------------
_NIVELES = [
    ("bronce",  0),
    ("plata",   500),
    ("oro",     1500),
    ("platino", 5000),
]

def _calcular_nivel(puntos: int) -> str:
    nivel = "bronce"
    for nombre, minimo in _NIVELES:
        if puntos >= minimo:
            nivel = nombre
    return nivel

# ---- Puntos -----------------------------------------------------------------

def acumular_puntos(db, cliente_id: int, pedido_id, puntos: int,
                    descripcion: str = "", creado_por: str = "") -> dict:
    """Suma puntos al cliente y registra el movimiento."""
    cliente = db.query(TortasCliente).filter(TortasCliente.id == cliente_id).first()
    if not cliente:
        return {"ok": False, "error": "cliente no encontrado"}
    cliente.puntos_acumulados = (cliente.puntos_acumulados or 0) + puntos
    nuevo_nivel = _calcular_nivel(cliente.puntos_acumulados)
    cliente.nivel_fidelidad = nuevo_nivel
    saldo = cliente.puntos_acumulados - (cliente.puntos_canjeados or 0)
    mov = TortasPuntosHistorial(
        cliente_id=cliente_id,
        pedido_id=pedido_id,
        tipo="ganado",
        puntos=puntos,
        saldo_resultante=saldo,
        descripcion=descripcion,
        creado_por=creado_por,
    )
    db.add(mov)
    db.commit()
    db.refresh(cliente)
    return {"ok": True, "puntos_acumulados": cliente.puntos_acumulados,
            "nivel_fidelidad": cliente.nivel_fidelidad}

def ajustar_puntos(db, cliente_id: int, data: AjustePuntosRequest) -> dict:
    """Ajuste manual de puntos (positivo o negativo)."""
    cliente = db.query(TortasCliente).filter(TortasCliente.id == cliente_id).first()
    if not cliente:
        return {"ok": False, "error": "cliente no encontrado"}
    cliente.puntos_acumulados = max(0, (cliente.puntos_acumulados or 0) + data.puntos)
    cliente.nivel_fidelidad = _calcular_nivel(cliente.puntos_acumulados)
    saldo = cliente.puntos_acumulados - (cliente.puntos_canjeados or 0)
    mov = TortasPuntosHistorial(
        cliente_id=cliente_id,
        tipo="ajuste",
        puntos=data.puntos,
        saldo_resultante=max(0, saldo),
        descripcion=data.descripcion,
        creado_por=data.creado_por,
    )
    db.add(mov)
    db.commit()
    db.refresh(cliente)
    return {"ok": True, "puntos_acumulados": cliente.puntos_acumulados,
            "nivel_fidelidad": cliente.nivel_fidelidad}

def get_historial_puntos(db, cliente_id: int, limit: int = 30) -> list:
    return (db.query(TortasPuntosHistorial)
              .filter(TortasPuntosHistorial.cliente_id == cliente_id)
              .order_by(TortasPuntosHistorial.created_at.desc())
              .limit(limit).all())

# ---- Recompensas ------------------------------------------------------------

def list_recompensas(db, solo_activas: bool = True) -> list:
    q = db.query(TortasRecompensa)
    if solo_activas:
        q = q.filter(TortasRecompensa.activa == True)
    return q.order_by(TortasRecompensa.puntos_necesarios).all()

def get_recompensa(db, recompensa_id: int):
    return db.query(TortasRecompensa).filter(TortasRecompensa.id == recompensa_id).first()

def create_recompensa(db, data: RecompensaCreate) -> TortasRecompensa:
    obj = TortasRecompensa(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def canjear_recompensa(db, cliente_id: int, data: CanjearRecompensaRequest) -> dict:
    """Canjea una recompensa descontando los puntos del cliente."""
    cliente = db.query(TortasCliente).filter(TortasCliente.id == cliente_id).first()
    if not cliente:
        return {"ok": False, "error": "cliente no encontrado"}
    recompensa = db.query(TortasRecompensa).filter(
        TortasRecompensa.id == data.recompensa_id,
        TortasRecompensa.activa == True,
    ).first()
    if not recompensa:
        return {"ok": False, "error": "recompensa no encontrada o inactiva"}
    if recompensa.limite_usos > 0 and recompensa.usos_actuales >= recompensa.limite_usos:
        return {"ok": False, "error": "recompensa agotada"}
    disponibles = (cliente.puntos_acumulados or 0) - (cliente.puntos_canjeados or 0)
    if disponibles < recompensa.puntos_necesarios:
        return {"ok": False, "error": "puntos insuficientes",
                "disponibles": disponibles, "requeridos": recompensa.puntos_necesarios}
    cliente.puntos_canjeados = (cliente.puntos_canjeados or 0) + recompensa.puntos_necesarios
    recompensa.usos_actuales = (recompensa.usos_actuales or 0) + 1
    saldo = cliente.puntos_acumulados - cliente.puntos_canjeados
    mov = TortasPuntosHistorial(
        cliente_id=cliente_id,
        pedido_id=data.pedido_id,
        tipo="canjeado",
        puntos=-recompensa.puntos_necesarios,
        saldo_resultante=max(0, saldo),
        descripcion=f"Canje: {recompensa.name}",
    )
    uso = TortasRecompensaUso(
        cliente_id=cliente_id,
        recompensa_id=recompensa.id,
        pedido_id=data.pedido_id,
        puntos_usados=recompensa.puntos_necesarios,
        valor_aplicado=recompensa.valor,
    )
    db.add(mov)
    db.add(uso)
    db.commit()
    db.refresh(cliente)
    return {"ok": True, "saldo_puntos": max(0, saldo),
            "valor_aplicado": recompensa.valor, "tipo": recompensa.tipo}

def get_stats_cliente(db, cliente_id: int) -> dict:
    cliente = db.query(TortasCliente).filter(TortasCliente.id == cliente_id).first()
    if not cliente:
        return {}
    disponibles = (cliente.puntos_acumulados or 0) - (cliente.puntos_canjeados or 0)
    return {
        "cliente_id": cliente.id,
        "nombre": cliente.nombre,
        "nivel_fidelidad": cliente.nivel_fidelidad or "bronce",
        "puntos_acumulados": cliente.puntos_acumulados or 0,
        "puntos_canjeados": cliente.puntos_canjeados or 0,
        "puntos_disponibles": max(0, disponibles),
        "total_historico": cliente.total_historico or 0.0,
        "num_pedidos": cliente.num_pedidos or 0,
        "ultimo_pedido_at": cliente.ultimo_pedido_at,
    }

# ---- Preferencias -----------------------------------------------------------

def list_preferencias_cliente(db, cliente_id: int) -> list:
    return (db.query(TortasPreferenciaCliente)
              .filter(TortasPreferenciaCliente.cliente_id == cliente_id)
              .order_by(TortasPreferenciaCliente.tipo, TortasPreferenciaCliente.nombre)
              .all())

def create_preferencia_cliente(db, cliente_id: int,
                               data: PreferenciaClienteCreate) -> TortasPreferenciaCliente:
    obj = TortasPreferenciaCliente(cliente_id=cliente_id, **data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def delete_preferencia_cliente(db, preferencia_id: int, cliente_id: int) -> dict:
    obj = db.query(TortasPreferenciaCliente).filter(
        TortasPreferenciaCliente.id == preferencia_id,
        TortasPreferenciaCliente.cliente_id == cliente_id,
    ).first()
    if not obj:
        return {"ok": False, "error": "no encontrada"}
    db.delete(obj)
    db.commit()
    return {"ok": True}

# ---- Promociones personales -------------------------------------------------

def list_promociones_cliente(db, cliente_id: int, solo_activas: bool = True) -> list:
    q = (db.query(TortasPromocionCliente)
           .filter(TortasPromocionCliente.cliente_id == cliente_id))
    if solo_activas:
        q = q.filter(TortasPromocionCliente.activa == True)
    return q.all()

def create_promocion_cliente(db, cliente_id: int,
                             data: PromocionClienteCreate) -> TortasPromocionCliente:
    obj = TortasPromocionCliente(cliente_id=cliente_id, **data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def marcar_pedido_completado_fidelidad(db, pedido_id: int,
                                       total: float, puntos_por_peso: float = 1.0) -> None:
    """Llama tras marcar un pedido como entregado/pagado.
    Acumula puntos (1 punto por cada unidad monetaria, configurable)
    y actualiza stats del cliente.
    """
    from .db_models import TortasPedido
    pedido = db.query(TortasPedido).filter(TortasPedido.id == pedido_id).first()
    if not pedido or not pedido.cliente_id:
        return
    cliente = db.query(TortasCliente).filter(TortasCliente.id == pedido.cliente_id).first()
    if not cliente:
        return
    puntos = max(1, int(total * puntos_por_peso))
    cliente.total_historico = (cliente.total_historico or 0.0) + total
    cliente.num_pedidos = (cliente.num_pedidos or 0) + 1
    from datetime import datetime as _dt
    cliente.ultimo_pedido_at = _dt.utcnow()
    acumular_puntos(db, cliente.id, pedido_id, puntos,
                    descripcion=f"Pedido #{pedido_id} – ${total:.2f}")


# ── Fase 7: Entrega y logística ───────────────────────────────────────────────

# ---- Repartidores -----------------------------------------------------------

def list_repartidores(db, solo_activos: bool = True) -> list:
    q = db.query(TortasRepartidor)
    if solo_activos:
        q = q.filter(TortasRepartidor.activo == True)
    return q.order_by(TortasRepartidor.nombre).all()

def get_repartidor(db, repartidor_id: int):
    return db.query(TortasRepartidor).filter(TortasRepartidor.id == repartidor_id).first()

def create_repartidor(db, data: RepartidorCreate) -> TortasRepartidor:
    obj = TortasRepartidor(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_repartidor(db, repartidor_id: int, data: RepartidorCreate) -> dict:
    obj = db.query(TortasRepartidor).filter(TortasRepartidor.id == repartidor_id).first()
    if not obj:
        return {"ok": False, "error": "no encontrado"}
    for k, v in data.model_dump().items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return {"ok": True, "id": obj.id}

def set_disponibilidad_repartidor(db, repartidor_id: int, disponible: bool) -> dict:
    obj = db.query(TortasRepartidor).filter(TortasRepartidor.id == repartidor_id).first()
    if not obj:
        return {"ok": False, "error": "no encontrado"}
    obj.disponible = disponible
    db.commit()
    return {"ok": True, "disponible": disponible}

# ---- Entregas ---------------------------------------------------------------

def get_entregas_pendientes(db) -> list:
    """Entregas en estado pendiente o asignado, ordenadas por creación."""
    return (db.query(TortasEntrega)
              .filter(TortasEntrega.estado.in_(["pendiente", "asignado"]))
              .order_by(TortasEntrega.created_at)
              .all())

def get_entrega_pedido(db, pedido_id: int):
    return db.query(TortasEntrega).filter(TortasEntrega.pedido_id == pedido_id).first()

def get_entregas_repartidor(db, repartidor_id: int, activas: bool = True) -> list:
    q = db.query(TortasEntrega).filter(TortasEntrega.repartidor_id == repartidor_id)
    if activas:
        q = q.filter(TortasEntrega.estado.in_(["asignado", "en_camino"]))
    return q.order_by(TortasEntrega.created_at.desc()).all()

def create_entrega(db, data: EntregaCreate) -> dict:
    """Crea el registro de entrega para un pedido. Solo uno por pedido."""
    existing = db.query(TortasEntrega).filter(TortasEntrega.pedido_id == data.pedido_id).first()
    if existing:
        return {"ok": False, "error": "el pedido ya tiene una entrega registrada", "id": existing.id}
    obj = TortasEntrega(
        pedido_id=data.pedido_id,
        repartidor_id=data.repartidor_id,
        tipo=data.tipo,
        notas=data.notas,
        estado="pendiente" if not data.repartidor_id else "asignado",
    )
    db.add(obj)
    # Si se asigna repartidor, marcarlo como no disponible
    if data.repartidor_id:
        rep = db.query(TortasRepartidor).filter(TortasRepartidor.id == data.repartidor_id).first()
        if rep:
            rep.disponible = False
    db.commit()
    db.refresh(obj)
    return {"ok": True, "id": obj.id}

def asignar_repartidor(db, entrega_id: int, data: AsignarRepartidorRequest) -> dict:
    entrega = db.query(TortasEntrega).filter(TortasEntrega.id == entrega_id).first()
    if not entrega:
        return {"ok": False, "error": "entrega no encontrada"}
    # Liberar repartidor anterior
    if entrega.repartidor_id and entrega.repartidor_id != data.repartidor_id:
        prev = db.query(TortasRepartidor).filter(TortasRepartidor.id == entrega.repartidor_id).first()
        if prev:
            prev.disponible = True
    entrega.repartidor_id = data.repartidor_id
    entrega.estado = "asignado"
    # Ocupar nuevo repartidor
    rep = db.query(TortasRepartidor).filter(TortasRepartidor.id == data.repartidor_id).first()
    if rep:
        rep.disponible = False
    db.commit()
    return {"ok": True}

def actualizar_estado_entrega(db, entrega_id: int, data: ActualizarEstadoEntregaRequest) -> dict:
    from datetime import datetime as _dt
    entrega = db.query(TortasEntrega).filter(TortasEntrega.id == entrega_id).first()
    if not entrega:
        return {"ok": False, "error": "no encontrada"}
    entrega.estado = data.estado
    if data.tiempo_salida:
        entrega.tiempo_salida = data.tiempo_salida
    elif data.estado == "en_camino" and not entrega.tiempo_salida:
        entrega.tiempo_salida = _dt.utcnow()
    if data.tiempo_estimado_llegada:
        entrega.tiempo_estimado_llegada = data.tiempo_estimado_llegada
    if data.tiempo_entrega_real:
        entrega.tiempo_entrega_real = data.tiempo_entrega_real
    elif data.estado == "entregado" and not entrega.tiempo_entrega_real:
        entrega.tiempo_entrega_real = _dt.utcnow()
    if data.distancia_km is not None:
        entrega.distancia_km = data.distancia_km
    if data.motivo_fallo:
        entrega.motivo_fallo = data.motivo_fallo
    if data.notas:
        entrega.notas = data.notas
    if data.cerrado_por:
        entrega.cerrado_por = data.cerrado_por
    # Si entregado o fallido, liberar repartidor
    if data.estado in ("entregado", "fallido", "cancelado") and entrega.repartidor_id:
        rep = db.query(TortasRepartidor).filter(TortasRepartidor.id == entrega.repartidor_id).first()
        if rep:
            rep.disponible = True
    # Propagar estado al pedido
    from .db_models import TortasPedido
    pedido = db.query(TortasPedido).filter(TortasPedido.id == entrega.pedido_id).first()
    if pedido:
        mapa = {
            "en_camino": "en_reparto",
            "entregado": "entregado",
            "fallido": "no_entregado",
            "cancelado": "cancelado",
        }
        if data.estado in mapa:
            pedido.estado = mapa[data.estado]
            if data.estado == "entregado":
                pedido.fecha_entregado = _dt.utcnow()
    db.commit()
    return {"ok": True, "estado": entrega.estado}

def registrar_evidencia_entrega(db, entrega_id: int, data: RegistrarEvidenciaRequest) -> dict:
    entrega = db.query(TortasEntrega).filter(TortasEntrega.id == entrega_id).first()
    if not entrega:
        return {"ok": False, "error": "no encontrada"}
    if data.evidencia_url:
        entrega.evidencia_url = data.evidencia_url
    if data.firma_url:
        entrega.firma_url = data.firma_url
    if data.notas:
        entrega.notas = data.notas
    if data.cerrado_por:
        entrega.cerrado_por = data.cerrado_por
    db.commit()
    return {"ok": True}


# ── Fase 8: Caja y administración ─────────────────────────────────────────────

# ---- Cajas ------------------------------------------------------------------

def list_cajas(db, solo_activas: bool = True) -> list:
    q = db.query(TortasCaja)
    if solo_activas:
        q = q.filter(TortasCaja.activa == True)
    return q.order_by(TortasCaja.name).all()

def get_caja(db, caja_id: int):
    return db.query(TortasCaja).filter(TortasCaja.id == caja_id).first()

def create_caja(db, data: CajaCreate) -> TortasCaja:
    obj = TortasCaja(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_caja(db, caja_id: int, data: CajaCreate) -> dict:
    obj = db.query(TortasCaja).filter(TortasCaja.id == caja_id).first()
    if not obj:
        return {"ok": False, "error": "no encontrada"}
    for k, v in data.model_dump().items():
        setattr(obj, k, v)
    db.commit()
    return {"ok": True}

# ---- Turnos -----------------------------------------------------------------

def get_turno_activo(db, caja_id: int = None):
    """Devuelve el turno abierto (el más reciente) para la caja dada, o cualquiera si es None."""
    q = db.query(TortasTurno).filter(TortasTurno.estado == "abierto")
    if caja_id:
        q = q.filter(TortasTurno.caja_id == caja_id)
    return q.order_by(TortasTurno.hora_inicio.desc()).first()

def list_turnos(db, caja_id: int = None, solo_abiertos: bool = False) -> list:
    q = db.query(TortasTurno)
    if caja_id:
        q = q.filter(TortasTurno.caja_id == caja_id)
    if solo_abiertos:
        q = q.filter(TortasTurno.estado == "abierto")
    return q.order_by(TortasTurno.hora_inicio.desc()).all()

def abrir_turno(db, data: TurnoCreate) -> dict:
    """Abre un nuevo turno; verifica que no haya otro abierto en la misma caja."""
    if data.caja_id:
        existing = get_turno_activo(db, data.caja_id)
        if existing:
            return {"ok": False, "error": "ya hay un turno abierto para esta caja", "turno_id": existing.id}
    obj = TortasTurno(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return {"ok": True, "id": obj.id}

def cerrar_turno(db, turno_id: int, data: CerrarTurnoRequest) -> dict:
    from datetime import datetime as _dt
    turno = db.query(TortasTurno).filter(TortasTurno.id == turno_id).first()
    if not turno:
        return {"ok": False, "error": "turno no encontrado"}
    if turno.estado == "cerrado":
        return {"ok": False, "error": "el turno ya está cerrado"}
    turno.estado = "cerrado"
    turno.hora_fin = _dt.utcnow()
    if data.notas:
        turno.notas = (turno.notas + "\n" + data.notas).strip()
    db.commit()
    return {"ok": True}

# ---- Cortes de caja amplía -------------------------------------------------

def _calcular_kpis_corte(db, corte) -> dict:
    """Calcula y persiste los KPIs del corte a partir de sus pedidos y pagos."""
    from sqlalchemy import func as sqlfunc

    pedidos_ids = [p.id for p in corte.pedidos if p.estado not in ("cancelado",)]
    pagos = corte.pagos  # ya cargados por relationship

    total_ventas = sum(
        sum(l.precio_unitario * l.cantidad for l in p.lineas)
        for p in corte.pedidos if p.estado not in ("cancelado",)
    ) if corte.pedidos else 0.0

    total_descuentos = sum(getattr(p, "descuento", 0.0) for p in corte.pedidos)
    total_cupones = 0.0  # extensible

    efectivo = transferencia = tarjeta = otros = 0.0
    ventas_por_fp: dict = {}
    for pago in pagos:
        fp = getattr(pago.forma_pago, "codigo", "otro") if pago.forma_pago else "otro"
        monto = pago.monto or 0.0
        ventas_por_fp[fp] = ventas_por_fp.get(fp, 0.0) + monto
        if fp in ("efectivo",):
            efectivo += monto
        elif fp in ("transferencia",):
            transferencia += monto
        elif fp in ("tarjeta_debito", "tarjeta_credito"):
            tarjeta += monto
        else:
            otros += monto

    ventas_por_canal: dict = {}
    for p in corte.pedidos:
        canal = getattr(p.canal_venta, "name", "sin canal") if p.canal_venta else "sin canal"
        ventas_por_canal[canal] = ventas_por_canal.get(canal, 0.0) + sum(
            l.precio_unitario * l.cantidad for l in p.lineas
        )

    anulaciones = db.query(TortasAnulacion).filter(
        TortasAnulacion.corte_caja_id == corte.id
    ).all()
    devoluciones = db.query(TortasDevolucion).filter(
        TortasDevolucion.corte_caja_id == corte.id
    ).all()

    corte.total_ventas = total_ventas
    corte.total_efectivo = efectivo
    corte.total_tarjeta = tarjeta
    corte.total_transferencia = transferencia
    corte.total_otros = otros
    corte.total_descuentos = total_descuentos
    corte.total_cupones = total_cupones
    corte.total_anulaciones = sum(a.monto_anulado for a in anulaciones)
    corte.total_devoluciones = sum(d.monto_devuelto for d in devoluciones)
    corte.num_pedidos = len(corte.pedidos)
    corte.num_anulaciones = len(anulaciones)
    corte.num_devoluciones = len(devoluciones)
    db.commit()

    return {
        "corte_id": corte.id,
        "total_ventas": corte.total_ventas,
        "total_efectivo": corte.total_efectivo,
        "total_tarjeta": corte.total_tarjeta,
        "total_transferencia": corte.total_transferencia,
        "total_otros": corte.total_otros,
        "total_descuentos": corte.total_descuentos,
        "total_cupones": corte.total_cupones,
        "total_anulaciones": corte.total_anulaciones,
        "total_devoluciones": corte.total_devoluciones,
        "num_pedidos": corte.num_pedidos,
        "num_anulaciones": corte.num_anulaciones,
        "num_devoluciones": corte.num_devoluciones,
        "ventas_por_canal": ventas_por_canal,
        "ventas_por_forma_pago": ventas_por_fp,
    }

def cerrar_corte(db, corte_id: int, data: CerrarCorteRequest) -> dict:
    from datetime import datetime as _dt
    from .db_models import TortasCorteCaja
    corte = db.query(TortasCorteCaja).filter(TortasCorteCaja.id == corte_id).first()
    if not corte:
        return {"ok": False, "error": "corte no encontrado"}
    if corte.estado == "cerrado":
        return {"ok": False, "error": "el corte ya está cerrado"}
    corte.estado = "cerrado"
    corte.fecha_cierre = _dt.utcnow()
    corte.usuario_cierre = data.usuario_cierre
    corte.efectivo_contado = data.efectivo_contado
    if data.notas:
        corte.notas = (corte.notas + "\n" + data.notas).strip()
    db.commit()
    db.refresh(corte)
    kpis = _calcular_kpis_corte(db, corte)
    kpis["ok"] = True
    return kpis

def get_kpis_corte(db, corte_id: int) -> dict:
    from .db_models import TortasCorteCaja
    corte = db.query(TortasCorteCaja).filter(TortasCorteCaja.id == corte_id).first()
    if not corte:
        return {}
    return _calcular_kpis_corte(db, corte)

# ---- Anulaciones ------------------------------------------------------------

def list_anulaciones(db, corte_id: int = None, pedido_id: int = None) -> list:
    q = db.query(TortasAnulacion)
    if corte_id:
        q = q.filter(TortasAnulacion.corte_caja_id == corte_id)
    if pedido_id:
        q = q.filter(TortasAnulacion.pedido_id == pedido_id)
    return q.order_by(TortasAnulacion.created_at.desc()).all()

def create_anulacion(db, data: AnulacionCreate) -> dict:
    from .db_models import TortasPedido
    pedido = db.query(TortasPedido).filter(TortasPedido.id == data.pedido_id).first()
    if not pedido:
        return {"ok": False, "error": "pedido no encontrado"}
    obj = TortasAnulacion(**data.model_dump())
    db.add(obj)
    # Marcar pedido como cancelado si anulación total
    if data.tipo == "total":
        pedido.estado = "cancelado"
    db.commit()
    db.refresh(obj)
    return {"ok": True, "id": obj.id}

# ---- Devoluciones -----------------------------------------------------------

def list_devoluciones(db, corte_id: int = None, pedido_id: int = None) -> list:
    q = db.query(TortasDevolucion)
    if corte_id:
        q = q.filter(TortasDevolucion.corte_caja_id == corte_id)
    if pedido_id:
        q = q.filter(TortasDevolucion.pedido_id == pedido_id)
    return q.order_by(TortasDevolucion.created_at.desc()).all()

def create_devolucion(db, data: DevolucionCreate) -> dict:
    from .db_models import TortasPedido
    pedido = db.query(TortasPedido).filter(TortasPedido.id == data.pedido_id).first()
    if not pedido:
        return {"ok": False, "error": "pedido no encontrado"}
    obj = TortasDevolucion(**data.model_dump())
    db.add(obj)
    # Si devuelven puntos, sumarlos al cliente
    if data.puntos_devueltos and pedido.cliente_id:
        from .store import acumular_puntos
        acumular_puntos(db, pedido.cliente_id, pedido.id,
                        data.puntos_devueltos, "Devolución reembolso en puntos")
    db.commit()
    db.refresh(obj)
    return {"ok": True, "id": obj.id}


# ── Fase 9: Promociones y combos ─────────────────────────────────────────────

# ---- Promociones (motor automático) -----------------------------------------

def list_promociones(db, solo_activas: bool = True, canal_venta_id: int = None,
                     concepto_id: int = None) -> list:
    q = db.query(TortasPromocion)
    if solo_activas:
        q = q.filter(TortasPromocion.activa == True)
    if canal_venta_id:
        q = q.filter(
            (TortasPromocion.canal_venta_id == canal_venta_id) |
            (TortasPromocion.canal_venta_id == None)
        )
    if concepto_id:
        q = q.filter(
            (TortasPromocion.concepto_id == concepto_id) |
            (TortasPromocion.concepto_id == None)
        )
    return q.order_by(TortasPromocion.prioridad).all()

def get_promocion(db, promocion_id: int):
    return db.query(TortasPromocion).filter(TortasPromocion.id == promocion_id).first()

def create_promocion(db, data: PromocionCreate) -> TortasPromocion:
    obj = TortasPromocion(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_promocion(db, promocion_id: int, data: PromocionCreate) -> dict:
    obj = db.query(TortasPromocion).filter(TortasPromocion.id == promocion_id).first()
    if not obj:
        return {"ok": False, "error": "no encontrada"}
    for k, v in data.model_dump().items():
        setattr(obj, k, v)
    db.commit()
    return {"ok": True}

def evaluar_promociones(db, data: EvaluarPromocionesRequest) -> dict:
    """Evalúa qué promociones automáticas aplican a una cotización/pedido.
    Devuelve lista de promociones aplicables y el descuento total calculado.
    Respeta prioridad, acumulabilidad, horario y condiciones.
    """
    import json
    from datetime import datetime as _dt

    ahora = _dt.utcnow()
    hora_actual = ahora.hour + ahora.minute / 60.0
    dia_actual = str(ahora.weekday())  # 0=Lunes

    promos = list_promociones(db, solo_activas=True,
                              canal_venta_id=data.canal_venta_id,
                              concepto_id=data.concepto_id)

    aplicables = []
    descuento_total = 0.0
    detalle = []
    ya_aplicada_no_acumulable = False

    for p in promos:
        # Verificar fechas
        if p.fecha_inicio and ahora < p.fecha_inicio:
            continue
        if p.fecha_fin and ahora > p.fecha_fin:
            continue
        # Verificar horario
        if p.hora_desde is not None and hora_actual < p.hora_desde:
            continue
        if p.hora_hasta is not None and hora_actual > p.hora_hasta:
            continue
        # Verificar días
        if p.dias_semana:
            try:
                dias = json.loads(p.dias_semana)
                if dia_actual not in dias:
                    continue
            except Exception:
                pass
        # Verificar monto mínimo
        if data.monto_subtotal < p.monto_minimo:
            continue
        # Verificar límite total
        if p.limite_usos_total > 0 and p.usos_actuales >= p.limite_usos_total:
            continue
        # Verificar primera compra
        if p.solo_primera_compra and data.cliente_id:
            num = db.query(TortasPromocionUso).filter(
                TortasPromocionUso.promocion_id == p.id,
                TortasPromocionUso.cliente_id == data.cliente_id,
            ).count()
            if num > 0:
                continue
        # Si ya aplicó una no acumulable, saltamos las no acumulables
        if ya_aplicada_no_acumulable and not p.acumulable:
            continue

        # Calcular descuento
        monto = 0.0
        if p.tipo_accion == "descuento_porcentaje":
            monto = data.monto_subtotal * (p.valor / 100.0)
            if p.descuento_maximo > 0:
                monto = min(monto, p.descuento_maximo)
        elif p.tipo_accion == "descuento_fijo":
            monto = min(p.valor, data.monto_subtotal)
        elif p.tipo_accion in ("envio_gratis", "producto_gratis"):
            monto = 0.0  # el valor se aplica en el pedido, no en el subtotal

        descuento_total += monto
        aplicables.append(p)
        detalle.append({
            "promocion_id": p.id,
            "name": p.name,
            "tipo_accion": p.tipo_accion,
            "monto_descuento": round(monto, 2),
        })
        if not p.acumulable:
            ya_aplicada_no_acumulable = True

    return {
        "promociones_aplicables": aplicables,
        "descuento_total": round(descuento_total, 2),
        "detalle": detalle,
    }

def registrar_promocion_uso(db, promocion_id: int, pedido_id: int = None,
                             cliente_id: int = None, monto_descuento: float = 0.0,
                             descripcion: str = "") -> None:
    promo = db.query(TortasPromocion).filter(TortasPromocion.id == promocion_id).first()
    if promo:
        promo.usos_actuales = (promo.usos_actuales or 0) + 1
    uso = TortasPromocionUso(
        promocion_id=promocion_id,
        pedido_id=pedido_id,
        cliente_id=cliente_id,
        monto_descuento=monto_descuento,
        descripcion=descripcion,
    )
    db.add(uso)
    db.commit()

def list_usos_promocion(db, promocion_id: int, limit: int = 50) -> list:
    return (db.query(TortasPromocionUso)
              .filter(TortasPromocionUso.promocion_id == promocion_id)
              .order_by(TortasPromocionUso.created_at.desc())
              .limit(limit).all())

# ---- Combos ----------------------------------------------------------------

def list_combos(db, solo_activos: bool = True, concepto_id: int = None) -> list:
    q = db.query(TortasCombo)
    if solo_activos:
        q = q.filter(TortasCombo.activo == True, TortasCombo.disponible == True)
    if concepto_id:
        q = q.filter(
            (TortasCombo.concepto_id == concepto_id) |
            (TortasCombo.concepto_id == None)
        )
    return q.order_by(TortasCombo.name).all()

def get_combo(db, combo_id: int):
    return db.query(TortasCombo).filter(TortasCombo.id == combo_id).first()

def create_combo(db, data: ComboCreate) -> TortasCombo:
    lineas_data = data.model_dump().pop("lineas", [])
    datos = data.model_dump(exclude={"lineas"})
    obj = TortasCombo(**datos)
    db.add(obj)
    db.flush()
    for l in lineas_data:
        db.add(TortasComboLinea(combo_id=obj.id, **l))
    db.commit()
    db.refresh(obj)
    return obj

def update_combo(db, combo_id: int, data: ComboCreate) -> dict:
    obj = db.query(TortasCombo).filter(TortasCombo.id == combo_id).first()
    if not obj:
        return {"ok": False, "error": "no encontrado"}
    lineas_data = data.model_dump().pop("lineas", [])
    for k, v in data.model_dump(exclude={"lineas"}).items():
        setattr(obj, k, v)
    # Reemplazar líneas
    db.query(TortasComboLinea).filter(TortasComboLinea.combo_id == combo_id).delete()
    for l in lineas_data:
        db.add(TortasComboLinea(combo_id=combo_id, **l))
    db.commit()
    return {"ok": True}

def set_disponibilidad_combo(db, combo_id: int, disponible: bool) -> dict:
    obj = db.query(TortasCombo).filter(TortasCombo.id == combo_id).first()
    if not obj:
        return {"ok": False, "error": "no encontrado"}
    obj.disponible = disponible
    db.commit()
    return {"ok": True, "disponible": disponible}


# ── Fase 10: Inventario y recetas ─────────────────────────────────────────────

# ---- Insumos ----------------------------------------------------------------

def list_insumos(db, solo_activos: bool = True) -> list:
    q = db.query(TortasInsumo)
    if solo_activos:
        q = q.filter(TortasInsumo.activo == True)
    return q.order_by(TortasInsumo.name).all()

def get_insumo(db, insumo_id: int):
    return db.query(TortasInsumo).filter(TortasInsumo.id == insumo_id).first()

def create_insumo(db, data: InsumoCreate) -> TortasInsumo:
    obj = TortasInsumo(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_insumo(db, insumo_id: int, data: InsumoCreate) -> dict:
    obj = db.query(TortasInsumo).filter(TortasInsumo.id == insumo_id).first()
    if not obj:
        return {"ok": False, "error": "no encontrado"}
    for k, v in data.model_dump().items():
        setattr(obj, k, v)
    db.commit()
    return {"ok": True}

def get_alertas_stock(db) -> list:
    """Devuelve insumos cuyo stock_actual está por debajo del stock_minimo."""
    return (db.query(TortasInsumo)
              .filter(
                  TortasInsumo.activo == True,
                  TortasInsumo.stock_minimo > 0,
                  TortasInsumo.stock_actual < TortasInsumo.stock_minimo,
              )
              .order_by(TortasInsumo.name).all())

# ---- Movimientos de stock ---------------------------------------------------

def registrar_movimiento_insumo(db, data: MovimientoInsumoCreate) -> dict:
    insumo = db.query(TortasInsumo).filter(TortasInsumo.id == data.insumo_id).first()
    if not insumo:
        return {"ok": False, "error": "insumo no encontrado"}
    insumo.stock_actual = round((insumo.stock_actual or 0.0) + data.cantidad, 6)
    mov = TortasMovimientoInsumo(
        insumo_id=data.insumo_id,
        pedido_id=data.pedido_id,
        tipo=data.tipo,
        cantidad=data.cantidad,
        stock_resultante=insumo.stock_actual,
        costo_unitario=data.costo_unitario or insumo.costo_unitario,
        descripcion=data.descripcion,
        creado_por=data.creado_por,
    )
    db.add(mov)
    db.commit()
    return {"ok": True, "stock_actual": insumo.stock_actual}

def ajustar_stock_insumo(db, data: AjusteStockRequest) -> dict:
    """Corrección directa: establece el stock al valor indicado."""
    insumo = db.query(TortasInsumo).filter(TortasInsumo.id == data.insumo_id).first()
    if not insumo:
        return {"ok": False, "error": "no encontrado"}
    diferencia = data.stock_nuevo - (insumo.stock_actual or 0.0)
    insumo.stock_actual = data.stock_nuevo
    mov = TortasMovimientoInsumo(
        insumo_id=data.insumo_id,
        tipo="ajuste",
        cantidad=diferencia,
        stock_resultante=data.stock_nuevo,
        descripcion=data.motivo or "Ajuste manual",
        creado_por=data.creado_por,
    )
    db.add(mov)
    db.commit()
    return {"ok": True, "stock_actual": data.stock_nuevo}

def get_movimientos_insumo(db, insumo_id: int, limit: int = 50) -> list:
    return (db.query(TortasMovimientoInsumo)
              .filter(TortasMovimientoInsumo.insumo_id == insumo_id)
              .order_by(TortasMovimientoInsumo.created_at.desc())
              .limit(limit).all())

# ---- Recetas ----------------------------------------------------------------

def list_recetas(db, producto_id: int = None) -> list:
    q = db.query(TortasReceta).filter(TortasReceta.activa == True)
    if producto_id:
        q = q.filter(TortasReceta.producto_id == producto_id)
    return q.all()

def get_receta(db, receta_id: int):
    return db.query(TortasReceta).filter(TortasReceta.id == receta_id).first()

def create_receta(db, data: RecetaCreate) -> TortasReceta:
    lineas_data = data.model_dump(exclude={"lineas"})
    obj = TortasReceta(**lineas_data)
    db.add(obj)
    db.flush()
    for l in data.lineas:
        db.add(TortasRecetaLinea(receta_id=obj.id, **l.model_dump()))
    db.commit()
    db.refresh(obj)
    return obj

def update_receta(db, receta_id: int, data: RecetaCreate) -> dict:
    obj = db.query(TortasReceta).filter(TortasReceta.id == receta_id).first()
    if not obj:
        return {"ok": False, "error": "no encontrada"}
    for k, v in data.model_dump(exclude={"lineas"}).items():
        setattr(obj, k, v)
    db.query(TortasRecetaLinea).filter(TortasRecetaLinea.receta_id == receta_id).delete()
    for l in data.lineas:
        db.add(TortasRecetaLinea(receta_id=receta_id, **l.model_dump()))
    db.commit()
    return {"ok": True}

# ---- Insumos por opción de modificador -------------------------------------

def list_insumos_opcion(db, opcion_id: int) -> list:
    return (db.query(TortasOpcionModificadorInsumo)
              .filter(TortasOpcionModificadorInsumo.opcion_id == opcion_id).all())

def create_insumo_opcion(db, data: OpcionModificadorInsumoCreate) -> TortasOpcionModificadorInsumo:
    obj = TortasOpcionModificadorInsumo(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def delete_insumo_opcion(db, insumo_opcion_id: int) -> dict:
    obj = db.query(TortasOpcionModificadorInsumo).filter(
        TortasOpcionModificadorInsumo.id == insumo_opcion_id
    ).first()
    if not obj:
        return {"ok": False, "error": "no encontrado"}
    db.delete(obj)
    db.commit()
    return {"ok": True}

# ---- Descuento automático de stock al vender --------------------------------

def descontar_stock_pedido(db, data: DescontarStockPedidoRequest) -> dict:
    """Descuenta del inventario los insumos consumidos por un pedido.
    1. Recorre cada línea del pedido → busca la receta del producto.
    2. Por cada línea de receta × cantidad pedida → registra salida.
    3. Recorre los modificadores del pedido → insumos adicionales por opción.
    Devuelve lista de movimientos generados.
    """
    from .db_models import (
        TortasPedido, TortasPedidoLinea,
        TortasPedidoLineaModificador,
    )
    pedido = db.query(TortasPedido).filter(TortasPedido.id == data.pedido_id).first()
    if not pedido:
        return {"ok": False, "error": "pedido no encontrado"}

    movimientos = []

    for linea in pedido.lineas:
        # Buscar receta activa del producto (sin variante o con la variante de la línea)
        receta = (db.query(TortasReceta)
                    .filter(
                        TortasReceta.producto_id == linea.producto_id,
                        TortasReceta.activa == True,
                    )
                    .first())
        if receta:
            factor = (linea.cantidad or 1) / max(receta.porciones, 1)
            for rl in receta.lineas:
                if not rl.insumo.descuento_automatico:
                    continue
                cantidad_descontar = round(-rl.cantidad * factor, 6)
                mov_data = MovimientoInsumoCreate(
                    insumo_id=rl.insumo_id,
                    pedido_id=pedido.id,
                    tipo="salida",
                    cantidad=cantidad_descontar,
                    descripcion=f"Pedido #{pedido.numero_pedido} – {rl.insumo.name}",
                    creado_por=data.creado_por,
                )
                res = registrar_movimiento_insumo(db, mov_data)
                movimientos.append({"insumo_id": rl.insumo_id, **res})

        # Modificadores del pedido
        mods = (db.query(TortasPedidoLineaModificador)
                  .filter(TortasPedidoLineaModificador.pedido_linea_id == linea.id)
                  .all())
        for mod in mods:
            insumos_opcion = (db.query(TortasOpcionModificadorInsumo)
                                .filter(TortasOpcionModificadorInsumo.opcion_id == mod.opcion_id)
                                .all())
            for oi in insumos_opcion:
                if not oi.insumo.descuento_automatico:
                    continue
                cantidad_descontar = round(-oi.cantidad * (linea.cantidad or 1), 6)
                mov_data = MovimientoInsumoCreate(
                    insumo_id=oi.insumo_id,
                    pedido_id=pedido.id,
                    tipo="salida",
                    cantidad=cantidad_descontar,
                    descripcion=f"Pedido #{pedido.numero_pedido} (modificador) – {oi.insumo.name}",
                    creado_por=data.creado_por,
                )
                res = registrar_movimiento_insumo(db, mov_data)
                movimientos.append({"insumo_id": oi.insumo_id, **res})

    return {"ok": True, "movimientos": len(movimientos), "detalle": movimientos}

# ── Fase 11: Reportes y analítica ─────────────────────────────────────────────

def _pagos_en_rango(db, fecha_inicio, fecha_fin):
    """Devuelve rows (pedido_id, monto, canal_venta_id, cliente_id, created_at) de pagos no cancelados."""
    return (
        db.query(
            TortasPago.pedido_id,
            TortasPago.monto,
            TortasPedido.canal_venta_id,
            TortasPedido.cliente_id,
            TortasPago.created_at,
        )
        .join(TortasPedido, TortasPago.pedido_id == TortasPedido.id)
        .filter(
            TortasPago.cancelado == False,
            TortasPedido.estado.notin_(["cancelado", "borrador"]),
            TortasPago.created_at >= fecha_inicio,
            TortasPago.created_at <= fecha_fin,
        )
        .all()
    )


def get_reporte_ventas_dia(db: Session, fecha_inicio, fecha_fin) -> list:
    from collections import defaultdict
    rows = _pagos_en_rango(db, fecha_inicio, fecha_fin)
    grupos = defaultdict(lambda: {"pedidos": set(), "total": 0.0})
    for r in rows:
        fecha = r.created_at.date() if r.created_at else None
        grupos[fecha]["pedidos"].add(r.pedido_id)
        grupos[fecha]["total"] += r.monto or 0.0
    result = []
    for fecha in sorted(grupos):
        g = grupos[fecha]
        n = len(g["pedidos"])
        t = round(g["total"], 2)
        result.append({"fecha": fecha, "num_pedidos": n, "total_ventas": t,
                        "ticket_promedio": round(t / n, 2) if n else 0.0})
    return result


def get_reporte_ventas_canal(db: Session, fecha_inicio, fecha_fin) -> list:
    from collections import defaultdict
    rows = _pagos_en_rango(db, fecha_inicio, fecha_fin)
    canal_ids = {r.canal_venta_id for r in rows if r.canal_venta_id}
    canales = {}
    if canal_ids:
        canales = {c.id: c.name for c in
                   db.query(TortasCanalVenta).filter(TortasCanalVenta.id.in_(canal_ids)).all()}
    grupos = defaultdict(lambda: {"pedidos": set(), "total": 0.0, "nombre": "Sin canal"})
    for r in rows:
        cid = r.canal_venta_id
        grupos[cid]["pedidos"].add(r.pedido_id)
        grupos[cid]["total"] += r.monto or 0.0
        if cid in canales:
            grupos[cid]["nombre"] = canales[cid]
    result = []
    for cid, g in sorted(grupos.items(), key=lambda x: -x[1]["total"]):
        n = len(g["pedidos"])
        t = round(g["total"], 2)
        result.append({"canal_id": cid, "canal": g["nombre"], "num_pedidos": n,
                        "total_ventas": t, "ticket_promedio": round(t / n, 2) if n else 0.0})
    return result


def get_reporte_productos_top(db: Session, fecha_inicio, fecha_fin, limit: int = 20) -> list:
    from sqlalchemy import func as _f
    rows = (
        db.query(
            TortasPedidoLinea.torta_id,
            TortasBase.name,
            _f.sum(TortasPedidoLinea.cantidad).label("qty"),
            _f.sum(TortasPedidoLinea.cantidad * TortasPedidoLinea.precio_unitario).label("total"),
        )
        .join(TortasPedido, TortasPedidoLinea.pedido_id == TortasPedido.id)
        .join(TortasBase, TortasPedidoLinea.torta_id == TortasBase.id)
        .filter(
            TortasPedido.estado.notin_(["cancelado", "borrador"]),
            TortasPedido.created_at >= fecha_inicio,
            TortasPedido.created_at <= fecha_fin,
        )
        .group_by(TortasPedidoLinea.torta_id, TortasBase.name)
        .order_by(_f.sum(TortasPedidoLinea.cantidad).desc())
        .limit(limit)
        .all()
    )
    return [{"producto_id": r.torta_id, "nombre": r.name,
             "cantidad_vendida": float(r.qty or 0),
             "total_ventas": round(float(r.total or 0), 2)} for r in rows]


def get_reporte_modificadores_top(db: Session, fecha_inicio, fecha_fin, limit: int = 20) -> list:
    from sqlalchemy import func as _f
    rows = (
        db.query(
            TortasPedidoLineaModificador.opcion_id,
            TortasOpcionModificador.name.label("opcion_name"),
            TortasGrupoModificador.name.label("grupo_name"),
            _f.count(TortasPedidoLineaModificador.id).label("veces"),
        )
        .join(TortasPedidoLinea, TortasPedidoLineaModificador.linea_id == TortasPedidoLinea.id)
        .join(TortasPedido, TortasPedidoLinea.pedido_id == TortasPedido.id)
        .join(TortasOpcionModificador, TortasPedidoLineaModificador.opcion_id == TortasOpcionModificador.id)
        .join(TortasGrupoModificador, TortasOpcionModificador.grupo_id == TortasGrupoModificador.id)
        .filter(
            TortasPedido.estado.notin_(["cancelado", "borrador"]),
            TortasPedido.created_at >= fecha_inicio,
            TortasPedido.created_at <= fecha_fin,
        )
        .group_by(TortasPedidoLineaModificador.opcion_id,
                  TortasOpcionModificador.name, TortasGrupoModificador.name)
        .order_by(_f.count(TortasPedidoLineaModificador.id).desc())
        .limit(limit)
        .all()
    )
    return [{"opcion_id": r.opcion_id, "opcion": r.opcion_name,
             "grupo": r.grupo_name, "veces_usado": r.veces} for r in rows]


def get_reporte_clientes_recurrentes(db: Session, fecha_inicio, fecha_fin, limit: int = 20) -> list:
    from sqlalchemy import func as _f
    rows = (
        db.query(
            TortasPedido.cliente_id,
            TortasCliente.nombre,
            TortasCliente.telefono,
            _f.count(TortasPedido.id).label("num_pedidos"),
            _f.max(TortasPedido.created_at).label("ultima_visita"),
        )
        .join(TortasCliente, TortasPedido.cliente_id == TortasCliente.id)
        .filter(
            TortasPedido.cliente_id.isnot(None),
            TortasPedido.estado.notin_(["cancelado", "borrador"]),
            TortasPedido.created_at >= fecha_inicio,
            TortasPedido.created_at <= fecha_fin,
        )
        .group_by(TortasPedido.cliente_id, TortasCliente.nombre, TortasCliente.telefono)
        .order_by(_f.count(TortasPedido.id).desc())
        .limit(limit)
        .all()
    )
    result = []
    for r in rows:
        total = (
            db.query(_f.sum(TortasPago.monto))
            .join(TortasPedido, TortasPago.pedido_id == TortasPedido.id)
            .filter(TortasPedido.cliente_id == r.cliente_id,
                    TortasPago.cancelado == False,
                    TortasPedido.estado.notin_(["cancelado", "borrador"]))
            .scalar() or 0.0
        )
        result.append({"cliente_id": r.cliente_id, "nombre": r.nombre,
                        "telefono": r.telefono, "num_pedidos": r.num_pedidos,
                        "total_gastado": round(float(total), 2),
                        "ultima_visita": r.ultima_visita})
    return result


def get_reporte_promociones_efectivas(db: Session, fecha_inicio, fecha_fin) -> list:
    from sqlalchemy import func as _f
    rows = (
        db.query(
            TortasPromocionUso.promocion_id,
            TortasPromocion.name,
            _f.count(TortasPromocionUso.id).label("veces"),
            _f.sum(TortasPromocionUso.monto_descuento).label("total_dto"),
        )
        .join(TortasPromocion, TortasPromocionUso.promocion_id == TortasPromocion.id)
        .filter(TortasPromocionUso.created_at >= fecha_inicio,
                TortasPromocionUso.created_at <= fecha_fin)
        .group_by(TortasPromocionUso.promocion_id, TortasPromocion.name)
        .order_by(_f.count(TortasPromocionUso.id).desc())
        .all()
    )
    return [{"promocion_id": r.promocion_id, "nombre": r.name,
             "veces_usada": r.veces,
             "descuento_total": round(float(r.total_dto or 0), 2)} for r in rows]


def get_reporte_tiempo_preparacion(db: Session, fecha_inicio, fecha_fin) -> list:
    from collections import defaultdict
    tickets = (
        db.query(TortasTicketCocina)
        .filter(TortasTicketCocina.inicio_preparacion.isnot(None),
                TortasTicketCocina.listo_at.isnot(None),
                TortasTicketCocina.created_at >= fecha_inicio,
                TortasTicketCocina.created_at <= fecha_fin)
        .all()
    )
    grupos = defaultdict(lambda: {"tiempos": [], "nombre": "Sin estación"})
    for t in tickets:
        diff = (t.listo_at - t.inicio_preparacion).total_seconds() / 60
        grupos[t.estacion_id]["tiempos"].append(diff)
    eids = [eid for eid in grupos if eid is not None]
    estaciones = {}
    if eids:
        estaciones = {e.id: e.name for e in
                      db.query(TortasEstacionCocina).filter(TortasEstacionCocina.id.in_(eids)).all()}
    result = []
    for eid, g in grupos.items():
        ts = g["tiempos"]
        result.append({
            "estacion_id": eid,
            "estacion": estaciones.get(eid, "Sin estación") if eid else "Sin estación",
            "tiempo_promedio_min": round(sum(ts) / len(ts), 2) if ts else 0.0,
            "num_tickets": len(ts),
        })
    return sorted(result, key=lambda x: -x["num_tickets"])


def get_reporte_tiempo_entrega(db: Session, fecha_inicio, fecha_fin) -> list:
    from collections import defaultdict
    entregas = (
        db.query(TortasEntrega)
        .filter(TortasEntrega.tiempo_salida.isnot(None),
                TortasEntrega.tiempo_entrega_real.isnot(None),
                TortasEntrega.created_at >= fecha_inicio,
                TortasEntrega.created_at <= fecha_fin)
        .all()
    )
    grupos = defaultdict(list)
    for e in entregas:
        diff = (e.tiempo_entrega_real - e.tiempo_salida).total_seconds() / 60
        grupos[e.created_at.date() if e.created_at else None].append(diff)
    result = []
    for fecha in sorted(grupos):
        ts = grupos[fecha]
        result.append({"fecha": fecha, "num_entregas": len(ts),
                        "tiempo_promedio_min": round(sum(ts) / len(ts), 2) if ts else 0.0})
    return result


def get_dashboard_gerencial(db: Session) -> dict:
    from sqlalchemy import func as _f
    from datetime import datetime as _dt, timedelta as _td
    now = _dt.utcnow()
    hoy0 = now.replace(hour=0, minute=0, second=0, microsecond=0)
    hoy1 = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    sem0 = hoy0 - _td(days=now.weekday())
    mes0 = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def _kpi(desde, hasta):
        row = (
            db.query(_f.count(_f.distinct(TortasPago.pedido_id)),
                     _f.sum(TortasPago.monto))
            .join(TortasPedido, TortasPago.pedido_id == TortasPedido.id)
            .filter(TortasPago.cancelado == False,
                    TortasPedido.estado.notin_(["cancelado", "borrador"]),
                    TortasPago.created_at >= desde,
                    TortasPago.created_at <= hasta)
            .one()
        )
        n, v = row[0] or 0, round(float(row[1] or 0), 2)
        return n, v

    n_hoy, v_hoy = _kpi(hoy0, hoy1)
    n_sem, v_sem = _kpi(sem0, hoy1)
    n_mes, v_mes = _kpi(mes0, hoy1)

    nuevos_mes = (db.query(_f.count(TortasCliente.id))
                  .filter(TortasCliente.created_at >= mes0).scalar() or 0)

    top = (
        db.query(TortasBase.name, _f.sum(TortasPedidoLinea.cantidad).label("qty"))
        .join(TortasPedidoLinea, TortasBase.id == TortasPedidoLinea.torta_id)
        .join(TortasPedido, TortasPedidoLinea.pedido_id == TortasPedido.id)
        .filter(TortasPedido.estado.notin_(["cancelado", "borrador"]),
                TortasPedido.created_at >= hoy0,
                TortasPedido.created_at <= hoy1)
        .group_by(TortasBase.name)
        .order_by(_f.sum(TortasPedidoLinea.cantidad).desc())
        .first()
    )

    alertas = (db.query(_f.count(TortasInsumo.id))
               .filter(TortasInsumo.activo == True,
                       TortasInsumo.stock_actual < TortasInsumo.stock_minimo)
               .scalar() or 0)

    return {
        "ventas_hoy": v_hoy, "pedidos_hoy": n_hoy,
        "ticket_promedio_hoy": round(v_hoy / n_hoy, 2) if n_hoy else 0.0,
        "ventas_semana": v_sem, "pedidos_semana": n_sem,
        "ventas_mes": v_mes, "pedidos_mes": n_mes,
        "ticket_promedio_mes": round(v_mes / n_mes, 2) if n_mes else 0.0,
        "clientes_nuevos_mes": nuevos_mes,
        "top_producto_hoy": top.name if top else "-",
        "alertas_stock": alertas,
    }


def get_dashboard_operativo(db: Session) -> dict:
    from sqlalchemy import func as _f

    def _cnt(estados):
        return (db.query(_f.count(TortasPedido.id))
                .filter(TortasPedido.estado.in_(estados)).scalar() or 0)

    return {
        "pedidos_pendientes": _cnt(["borrador", "confirmado"]),
        "pedidos_en_cocina":  _cnt(["enviado_cocina", "en_preparacion", "en_empaque"]),
        "pedidos_en_camino":  _cnt(["en_reparto"]),
        "pedidos_listos":     _cnt(["listo"]),
        "repartidores_activos": (db.query(_f.count(TortasRepartidor.id))
                                   .filter(TortasRepartidor.activo == True)
                                   .scalar() or 0),
        "alertas_stock": (db.query(_f.count(TortasInsumo.id))
                           .filter(TortasInsumo.activo == True,
                                   TortasInsumo.stock_actual < TortasInsumo.stock_minimo)
                           .scalar() or 0),
        "turnos_abiertos": (db.query(_f.count(TortasTurno.id))
                              .filter(TortasTurno.estado == "abierto").scalar() or 0),
        "cajas_abiertas": (db.query(_f.count(TortasCaja.id))
                             .filter(TortasCaja.activa == True).scalar() or 0),
    }


# ── Fase 12: Automatización e integración ─────────────────────────────────────

import json as _json

# ---- Eventos del sistema -----------------------------------------------------

def registrar_evento(db: Session, tipo_evento: str, entidad: str = "sistema",
                     entidad_id: int = None, payload: dict = None,
                     actor: str = "sistema", resultado: str = "ok",
                     detalle: str = "") -> TortasEventoSistema:
    ev = TortasEventoSistema(
        tipo_evento=tipo_evento,
        entidad=entidad,
        entidad_id=entidad_id,
        payload_json=_json.dumps(payload or {}, default=str),
        actor=actor,
        resultado=resultado,
        detalle=detalle,
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


def list_eventos(db: Session, entidad: str = None, entidad_id: int = None,
                 tipo_evento: str = None, limit: int = 50) -> list:
    q = db.query(TortasEventoSistema).order_by(TortasEventoSistema.created_at.desc())
    if entidad:
        q = q.filter(TortasEventoSistema.entidad == entidad)
    if entidad_id is not None:
        q = q.filter(TortasEventoSistema.entidad_id == entidad_id)
    if tipo_evento:
        q = q.filter(TortasEventoSistema.tipo_evento == tipo_evento)
    return q.limit(limit).all()


# ---- Automatizaciones -------------------------------------------------------

def list_automatizaciones(db: Session, solo_activas: bool = True) -> list:
    q = db.query(TortasAutomatizacion).order_by(
        TortasAutomatizacion.prioridad, TortasAutomatizacion.id)
    if solo_activas:
        q = q.filter(TortasAutomatizacion.activa == True)
    return q.all()


def get_automatizacion(db: Session, automatizacion_id: int):
    return db.query(TortasAutomatizacion).filter(
        TortasAutomatizacion.id == automatizacion_id).first()


def create_automatizacion(db: Session, data: AutomatizacionCreate) -> TortasAutomatizacion:
    obj = TortasAutomatizacion(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_automatizacion(db: Session, automatizacion_id: int,
                          data: AutomatizacionCreate) -> dict:
    obj = get_automatizacion(db, automatizacion_id)
    if not obj:
        return {"ok": False, "error": "No encontrada"}
    for k, v in data.model_dump().items():
        setattr(obj, k, v)
    db.commit()
    return {"ok": True}


def evaluar_automatizaciones(db: Session, pedido_id: int, evento: str,
                              actor: str = "sistema",
                              estado_actual: str = "",
                              payload: dict = None) -> dict:
    """Motor de automatizaciones.
    Busca todas las reglas activas que coincidan con el evento (y estado si aplica)
    y ejecuta su acción correspondiente.
    Devuelve un resumen de las acciones ejecutadas.
    """
    pedido = db.query(TortasPedido).filter(TortasPedido.id == pedido_id).first()
    if not pedido:
        return {"ok": False, "error": "Pedido no encontrado"}

    reglas = (
        db.query(TortasAutomatizacion)
        .filter(
            TortasAutomatizacion.activa == True,
            TortasAutomatizacion.evento_disparador == evento,
        )
        .order_by(TortasAutomatizacion.prioridad)
        .all()
    )

    ejecutadas = []
    for regla in reglas:
        # Filtrar por condición de estado
        if regla.condicion_estado and regla.condicion_estado != estado_actual:
            continue
        # Filtrar por canal
        if regla.canal_venta_id and pedido.canal_venta_id != regla.canal_venta_id:
            continue
        # Filtrar por concepto (si existe en pedido – ignorar si no aplica)
        concepto_pedido = getattr(pedido, "concepto_id", None)
        if regla.concepto_id and concepto_pedido and concepto_pedido != regla.concepto_id:
            continue

        resultado_accion = "ok"
        detalle_accion = ""

        if regla.accion_tipo == "enviar_mensaje" and regla.plantilla_id:
            plantilla = db.query(TortasPlantillaMensaje).filter(
                TortasPlantillaMensaje.id == regla.plantilla_id).first()
            if plantilla:
                # Sustituir variables en el cuerpo
                ctx = {
                    "nombre": pedido.nombre_cliente or "",
                    "numero_pedido": pedido.numero_pedido or "",
                    "estado": estado_actual,
                    "canal": pedido.canal_venta.name if pedido.canal_venta else "",
                }
                cuerpo = plantilla.cuerpo
                for k, v in ctx.items():
                    cuerpo = cuerpo.replace("{" + k + "}", str(v))
                # Registrar el mensaje en TortasMensajePedido
                msg = TortasMensajePedido(
                    pedido_id=pedido_id,
                    direccion="enviado",
                    canal=regla.canal_mensaje or "whatsapp",
                    plantilla_id=regla.plantilla_id,
                    cuerpo=cuerpo,
                    estado="pendiente",
                    enviado_por=actor,
                )
                db.add(msg)
                db.flush()
                detalle_accion = f"Mensaje pendiente registrado (plantilla #{regla.plantilla_id})"
            else:
                resultado_accion = "error"
                detalle_accion = f"Plantilla #{regla.plantilla_id} no encontrada"

        elif regla.accion_tipo == "cambiar_estado" and regla.estado_destino:
            pedido.estado = regla.estado_destino
            db.flush()
            detalle_accion = f"Estado cambiado a '{regla.estado_destino}'"

        elif regla.accion_tipo == "registrar_evento":
            detalle_accion = f"Evento '{evento}' registrado por automatización #{regla.id}"

        # Registrar el evento de ejecución
        registrar_evento(
            db,
            tipo_evento="automatizacion_ejecutada",
            entidad="pedido",
            entidad_id=pedido_id,
            payload={"automatizacion_id": regla.id, "accion": regla.accion_tipo,
                     "evento": evento, **(payload or {})},
            actor=actor,
            resultado=resultado_accion,
            detalle=detalle_accion,
        )

        ejecutadas.append({
            "automatizacion_id": regla.id,
            "name": regla.name,
            "accion": regla.accion_tipo,
            "resultado": resultado_accion,
            "detalle": detalle_accion,
        })

    db.commit()
    return {"ok": True, "ejecutadas": len(ejecutadas), "acciones": ejecutadas}


# ---- Webhooks de salida -----------------------------------------------------

def list_webhooks_salida(db: Session, solo_activos: bool = True) -> list:
    q = db.query(TortasWebhookSalida).order_by(TortasWebhookSalida.name)
    if solo_activos:
        q = q.filter(TortasWebhookSalida.activo == True)
    return q.all()


def get_webhook_salida(db: Session, webhook_id: int):
    return db.query(TortasWebhookSalida).filter(
        TortasWebhookSalida.id == webhook_id).first()


def create_webhook_salida(db: Session, data: WebhookSalidaCreate) -> TortasWebhookSalida:
    obj = TortasWebhookSalida(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_webhook_salida(db: Session, webhook_id: int,
                          data: WebhookSalidaCreate) -> dict:
    obj = get_webhook_salida(db, webhook_id)
    if not obj:
        return {"ok": False, "error": "No encontrado"}
    for k, v in data.model_dump().items():
        setattr(obj, k, v)
    db.commit()
    return {"ok": True}


def disparar_webhook(db: Session, webhook_id: int, payload: dict) -> dict:
    """Simula el envío de un webhook (registra intento sin HTTP real).
    En producción se reemplazaría por httpx/aiohttp + background task.
    """
    from datetime import datetime as _dt
    obj = get_webhook_salida(db, webhook_id)
    if not obj:
        return {"ok": False, "error": "Webhook no encontrado"}
    if not obj.activo:
        return {"ok": False, "error": "Webhook inactivo"}

    # Log del intento
    obj.ultimo_envio_at = _dt.utcnow()
    obj.ultimo_estado = "pendiente"
    obj.ultimo_error = ""
    db.commit()

    # Registrar evento de sistema
    registrar_evento(
        db,
        tipo_evento="webhook_disparado",
        entidad="sistema",
        payload={"webhook_id": webhook_id, "url": obj.url, **payload},
        actor="sistema",
        resultado="pendiente",
        detalle=f"Webhook '{obj.name}' — {obj.url}",
    )

    return {"ok": True, "webhook_id": webhook_id, "estado": "pendiente",
            "url": obj.url, "payload": payload}


# ── Configuración ─────────────────────────────────────────────────────────────

def get_configuracion(db: Session) -> TortasConfiguracion:
    obj = db.query(TortasConfiguracion).filter(TortasConfiguracion.active == True).first()
    if not obj:
        obj = TortasConfiguracion()
        db.add(obj)
        db.commit()
        db.refresh(obj)
    return obj
