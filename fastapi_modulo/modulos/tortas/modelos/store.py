from __future__ import annotations
from datetime import date, datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from fastapi_modulo.modulos.tortas.modelos.db_models import (
    TortasCategoria, TortasAlergeno, TortasTipoAlimento, TipoPan,
    TortasTopping, TortasBase, TortasZonaEntrega, TortasMetodoEntrega,
    TortasFormaPago, TortasCupon, TortasCuponUso,
    TortasCorteCaja, TortasPedido, TortasPedidoLinea, TortasPedidoLineaTopping,
    TortasPago, TortasPropina,
    TortasPreorden, TortasPreordenLinea, TortasPreordenLineaTopping,
    TortasConfiguracion,
)
from fastapi_modulo.modulos.tortas.modelos.schemas import (
    CategoriaCreate, AlergenoCreate, TipoPanCreate, TipoPanUpdate,
    ToppingCreate, TortaCreate, TortaUpdate,
    ZonaEntregaCreate, ZonaEntregaUpdate, FormaPagoCreate,
    CuponCreate, PedidoCreate, PedidoUpdate, PagoCreate, PropinaCreate,
    CorteCajaCreate, CorteCajaCerrarRequest,
    PreordenCreate,
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


# ── Tipos de pan ──────────────────────────────────────────────────────────────

def list_tipos_pan(db: Session, solo_activos: bool = True) -> List[TipoPan]:
    q = db.query(TipoPan)
    if solo_activos:
        q = q.filter(TipoPan.activo == True)
    return q.order_by(TipoPan.sequence, TipoPan.nombre).all()


def get_tipo_pan(db: Session, tipo_pan_id: int) -> Optional[TipoPan]:
    return db.query(TipoPan).filter(TipoPan.id == tipo_pan_id).first()


def create_tipo_pan(db: Session, data: TipoPanCreate) -> TipoPan:
    obj = TipoPan(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_tipo_pan(db: Session, tipo_pan_id: int, data: TipoPanUpdate) -> Optional[TipoPan]:
    obj = get_tipo_pan(db, tipo_pan_id)
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
        (l.precio_unitario + l.precio_pan + sum(t.precio_unitario * t.cantidad for t in l.toppings)) * l.cantidad
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


# ── Configuración ─────────────────────────────────────────────────────────────

def get_configuracion(db: Session) -> TortasConfiguracion:
    obj = db.query(TortasConfiguracion).filter(TortasConfiguracion.active == True).first()
    if not obj:
        obj = TortasConfiguracion()
        db.add(obj)
        db.commit()
        db.refresh(obj)
    return obj
