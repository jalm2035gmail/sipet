from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from fastapi_modulo.modulos.repartidores.modelos.db_models import (
    RepEntrega,
    RepEntregaLog,
    RepIncidencia,
    RepLiquidacion,
    RepLiquidacionLinea,
    RepRepartidor,
    RepRepartidorPosicion,
    RepVehiculo,
    RepZona,
)
from fastapi_modulo.modulos.repartidores.modelos.schemas import (
    ActualizarEstadoEntregaInput,
    ActualizarLiquidacionEstadoInput,
    AsignarEntregaInput,
    EntregaCreate,
    GenerarLiquidacionInput,
    IncidenciaCreate,
    PosicionUpdate,
    RepartidorCreate,
    RepartidorUpdate,
    VehiculoCreate,
    ZonaCreate,
)

ALLOWED_REPARTIDOR_STATES = {'available', 'busy', 'offline', 'suspended'}
ALLOWED_ENTREGA_STATES = {'draft', 'assigned', 'picked_up', 'in_transit', 'delivered', 'cancelled', 'failed'}
ALLOWED_PRIORIDADES = {'baja', 'normal', 'alta', 'urgente'}
TRANSITIONS = {
    'draft': {'assigned', 'cancelled'},
    'assigned': {'picked_up', 'cancelled', 'failed'},
    'picked_up': {'in_transit', 'failed'},
    'in_transit': {'delivered', 'failed'},
    'failed': {'assigned', 'cancelled'},
    'delivered': set(),
    'cancelled': set(),
}


def _to_decimal(value: object) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal('0.01'))


def _gen_folio(db: Session) -> str:
    prefix = f'REP{datetime.now():%Y%m}'
    last = db.query(RepEntrega).filter(RepEntrega.folio.like(f'{prefix}%')).order_by(RepEntrega.id.desc()).first()
    seq = 1
    if last and last.folio:
        try:
            seq = int(last.folio.replace(prefix, '')) + 1
        except ValueError:
            pass
    return f'{prefix}{seq:05d}'


def serialize_zona(obj: RepZona) -> dict:
    return {
        'id': obj.id,
        'name': obj.name,
        'code': obj.code,
        'description': obj.description,
        'ciudad': obj.ciudad,
        'radio_km': obj.radio_km,
        'active': obj.active,
    }


def serialize_vehiculo(obj: RepVehiculo) -> dict:
    return {
        'id': obj.id,
        'name': obj.name,
        'tipo': obj.tipo,
        'placa': obj.placa,
        'capacidad_kg': obj.capacidad_kg,
        'capacidad_pedidos': obj.capacidad_pedidos,
        'activo': obj.activo,
    }


def serialize_repartidor(obj: RepRepartidor) -> dict:
    return {
        'id': obj.id,
        'name': obj.name,
        'codigo': obj.codigo,
        'telefono': obj.telefono,
        'email': obj.email,
        'tipo': obj.tipo,
        'state': obj.state,
        'activo': obj.activo,
        'zona_id': obj.zona_id,
        'zona_name': obj.zona.name if obj.zona else None,
        'vehiculo_id': obj.vehiculo_id,
        'vehiculo_name': obj.vehiculo.name if obj.vehiculo else None,
        'negocio': obj.negocio,
        'sucursal': obj.sucursal,
        'sipet_username': obj.sipet_username or '',
        'tarifa_base': float(obj.tarifa_base or 0),
        'bono_por_entrega': float(obj.bono_por_entrega or 0),
        'meta_entregas_diarias': obj.meta_entregas_diarias,
        'max_entregas_simultaneas': obj.max_entregas_simultaneas,
        'notas': obj.notas,
    }


def serialize_entrega(obj: RepEntrega) -> dict:
    return {
        'id': obj.id,
        'folio': obj.folio,
        'referencia_externa': obj.referencia_externa,
        'cliente_nombre': obj.cliente_nombre,
        'cliente_telefono': obj.cliente_telefono,
        'origen': obj.origen,
        'destino': obj.destino,
        'descripcion': obj.descripcion,
        'prioridad': obj.prioridad,
        'state': obj.state,
        'costo_envio': float(obj.costo_envio or 0),
        'distancia_km': obj.distancia_km,
        'tiempo_estimado_min': obj.tiempo_estimado_min,
        'tiempo_real_min': obj.tiempo_real_min,
        'fecha_programada': obj.fecha_programada.isoformat() if obj.fecha_programada else None,
        'fecha_asignacion': obj.fecha_asignacion.isoformat() if obj.fecha_asignacion else None,
        'fecha_recoleccion': obj.fecha_recoleccion.isoformat() if obj.fecha_recoleccion else None,
        'fecha_entrega': obj.fecha_entrega.isoformat() if obj.fecha_entrega else None,
        'evidencia_entrega': obj.evidencia_entrega,
        'motivo_cancelacion': obj.motivo_cancelacion,
        'zona_id': obj.zona_id,
        'zona_name': obj.zona.name if obj.zona else None,
        'repartidor_id': obj.repartidor_id,
        'repartidor_name': obj.repartidor.name if obj.repartidor else None,
        'liquidable': obj.liquidable,
    }


def serialize_incidencia(obj: RepIncidencia) -> dict:
    return {
        'id': obj.id,
        'entrega_id': obj.entrega_id,
        'repartidor_id': obj.repartidor_id,
        'tipo': obj.tipo,
        'severidad': obj.severidad,
        'descripcion': obj.descripcion,
        'resolucion': obj.resolucion,
        'state': obj.state,
    }


def serialize_entrega_log(obj: RepEntregaLog) -> dict:
    return {
        'id': obj.id,
        'entrega_id': obj.entrega_id,
        'tipo': obj.tipo,
        'estado_anterior': obj.estado_anterior,
        'estado_nuevo': obj.estado_nuevo,
        'repartidor_id': obj.repartidor_id,
        'notas': obj.notas,
        'created_at': obj.created_at.isoformat() if obj.created_at else None,
    }


def serialize_liquidacion(obj: RepLiquidacion) -> dict:
    return {
        'id': obj.id,
        'repartidor_id': obj.repartidor_id,
        'repartidor_name': obj.repartidor.name if obj.repartidor else None,
        'fecha_inicio': obj.fecha_inicio.isoformat() if obj.fecha_inicio else None,
        'fecha_fin': obj.fecha_fin.isoformat() if obj.fecha_fin else None,
        'total_entregas': obj.total_entregas,
        'total_base': float(obj.total_base or 0),
        'total_bonos': float(obj.total_bonos or 0),
        'total_descuentos': float(obj.total_descuentos or 0),
        'total_pagar': float(obj.total_pagar or 0),
        'state': obj.state,
        'notas': obj.notas,
        'fecha_aprobacion': obj.fecha_aprobacion.isoformat() if obj.fecha_aprobacion else None,
        'fecha_pago': obj.fecha_pago.isoformat() if obj.fecha_pago else None,
        'lineas': [
            {
                'id': line.id,
                'entrega_id': line.entrega_id,
                'monto_base': float(line.monto_base or 0),
                'bono': float(line.bono or 0),
                'descuento': float(line.descuento or 0),
                'total': float(line.total or 0),
            }
            for line in obj.lineas
        ],
    }


def list_zonas(db: Session, solo_activas: bool = True) -> List[RepZona]:
    q = db.query(RepZona)
    if solo_activas:
        q = q.filter(RepZona.active == True)
    return q.order_by(RepZona.name).all()


def create_zona(db: Session, data: ZonaCreate) -> RepZona:
    existing = db.query(RepZona).filter(RepZona.code == data.code).first()
    if existing:
        raise ValueError('Ya existe una zona con ese código')
    obj = RepZona(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_vehiculos(db: Session, solo_activos: bool = True) -> List[RepVehiculo]:
    q = db.query(RepVehiculo)
    if solo_activos:
        q = q.filter(RepVehiculo.activo == True)
    return q.order_by(RepVehiculo.name).all()


def create_vehiculo(db: Session, data: VehiculoCreate) -> RepVehiculo:
    obj = RepVehiculo(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_repartidores(db: Session, solo_activos: bool = True, zona_id: Optional[int] = None, state: Optional[str] = None) -> List[RepRepartidor]:
    q = db.query(RepRepartidor)
    if solo_activos:
        q = q.filter(RepRepartidor.activo == True)
    if zona_id:
        q = q.filter(RepRepartidor.zona_id == zona_id)
    if state:
        q = q.filter(RepRepartidor.state == state)
    return q.order_by(RepRepartidor.name).all()


def get_repartidor(db: Session, repartidor_id: int) -> Optional[RepRepartidor]:
    return db.query(RepRepartidor).filter(RepRepartidor.id == repartidor_id).first()


def create_repartidor(db: Session, data: RepartidorCreate) -> RepRepartidor:
    if data.state not in ALLOWED_REPARTIDOR_STATES:
        raise ValueError('Estado de repartidor inválido')
    if db.query(RepRepartidor).filter(RepRepartidor.codigo == data.codigo).first():
        raise ValueError('Ya existe un repartidor con ese código')
    obj = RepRepartidor(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_repartidor(db: Session, repartidor_id: int, data: RepartidorUpdate) -> Optional[RepRepartidor]:
    obj = get_repartidor(db, repartidor_id)
    if not obj:
        return None
    payload = data.model_dump(exclude_none=True)
    if 'state' in payload and payload['state'] not in ALLOWED_REPARTIDOR_STATES:
        raise ValueError('Estado de repartidor inválido')
    for field, value in payload.items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def list_entregas(db: Session, repartidor_id: Optional[int] = None, state: Optional[str] = None, prioridad: Optional[str] = None, limit: int = 100) -> List[RepEntrega]:
    q = db.query(RepEntrega)
    if repartidor_id:
        q = q.filter(RepEntrega.repartidor_id == repartidor_id)
    if state:
        q = q.filter(RepEntrega.state == state)
    if prioridad:
        q = q.filter(RepEntrega.prioridad == prioridad)
    return q.order_by(RepEntrega.fecha_programada.asc()).limit(limit).all()


def get_entrega(db: Session, entrega_id: int) -> Optional[RepEntrega]:
    return db.query(RepEntrega).filter(RepEntrega.id == entrega_id).first()


def create_entrega(db: Session, data: EntregaCreate) -> RepEntrega:
    if data.prioridad not in ALLOWED_PRIORIDADES:
        raise ValueError('Prioridad inválida')
    obj = RepEntrega(
        folio=_gen_folio(db),
        referencia_externa=data.referencia_externa,
        cliente_nombre=data.cliente_nombre,
        cliente_telefono=data.cliente_telefono,
        origen=data.origen,
        destino=data.destino,
        descripcion=data.descripcion,
        prioridad=data.prioridad,
        state='draft',
        costo_envio=data.costo_envio,
        distancia_km=data.distancia_km,
        tiempo_estimado_min=data.tiempo_estimado_min,
        fecha_programada=data.fecha_programada,
        zona_id=data.zona_id,
        repartidor_id=None,
        liquidable=data.liquidable,
    )
    db.add(obj)
    db.flush()
    if data.repartidor_id is not None:
        assign_entrega(db, obj.id, AsignarEntregaInput(repartidor_id=data.repartidor_id), auto_commit=False)
    db.commit()
    db.refresh(obj)
    return obj


def assign_entrega(db: Session, entrega_id: int, data: AsignarEntregaInput, auto_commit: bool = True) -> Optional[RepEntrega]:
    obj = get_entrega(db, entrega_id)
    if not obj:
        return None
    repartidor = get_repartidor(db, data.repartidor_id)
    if not repartidor or not repartidor.activo:
        raise ValueError('Repartidor no disponible')
    if repartidor.state in {'offline', 'suspended'}:
        raise ValueError(
            f'El repartidor está {repartidor.state} y no puede recibir entregas'
        )
    if obj.state not in {'draft', 'failed'}:
        raise ValueError('La entrega no puede asignarse en su estado actual')

    # Límite de entregas simultáneas
    active_count = (
        db.query(RepEntrega)
        .filter(
            RepEntrega.repartidor_id == repartidor.id,
            RepEntrega.state.in_({'assigned', 'picked_up', 'in_transit'}),
        )
        .count()
    )
    max_sim = repartidor.max_entregas_simultaneas or 5
    if active_count >= max_sim:
        raise ValueError(
            f'El repartidor ya tiene {active_count} entregas activas '
            f'(límite: {max_sim}). Libera capacidad antes de asignar.'
        )

    prev_state = obj.state
    obj.repartidor_id = repartidor.id
    obj.fecha_asignacion = datetime.now()
    obj.state = 'assigned'
    if repartidor.state == 'available':
        repartidor.state = 'busy'

    # Advertencia de zona (no bloquea)
    zona_warning = None
    if obj.zona_id and repartidor.zona_id and obj.zona_id != repartidor.zona_id:
        zona_warning = 'La entrega es de una zona diferente a la del repartidor'

    log = RepEntregaLog(
        entrega_id=obj.id,
        tipo='asignacion',
        estado_anterior=prev_state,
        estado_nuevo='assigned',
        repartidor_id=repartidor.id,
        notas=zona_warning or '',
    )
    db.add(log)

    if auto_commit:
        db.commit()
        db.refresh(obj)
        # Notificaciones post-asignación (no bloquean si fallan)
        try:
            from fastapi_modulo.modulos.repartidores.servicios.notificaciones import (
                notif_entrega_asignada,
                notif_nueva_asignacion_repartidor,
            )
            notif_entrega_asignada(db, obj, repartidor)
            notif_nueva_asignacion_repartidor(db, obj, repartidor)
            db.commit()
        except Exception as _notif_exc:
            import logging as _lg
            _lg.getLogger(__name__).warning('notif assign_entrega: %s', _notif_exc)
    return obj


def update_entrega_state(db: Session, entrega_id: int, data: ActualizarEstadoEntregaInput) -> Optional[RepEntrega]:
    obj = get_entrega(db, entrega_id)
    if not obj:
        return None
    if data.state not in ALLOWED_ENTREGA_STATES:
        raise ValueError('Estado de entrega inválido')
    if data.state not in TRANSITIONS.get(obj.state, set()):
        raise ValueError('Transición de estado no permitida')
    if data.state == 'delivered':
        evidencia = (data.evidencia_entrega or '').strip()
        if len(evidencia) < 5:
            raise ValueError(
                'La evidencia de entrega es obligatoria y debe tener al menos 5 caracteres'
            )
    if data.state in {'cancelled', 'failed'}:
        motivo = (data.motivo_cancelacion or '').strip()
        if len(motivo) < 5:
            raise ValueError('Debes indicar el motivo (mínimo 5 caracteres)')
    prev_state = obj.state
    obj.state = data.state
    if data.tiempo_real_min is not None:
        obj.tiempo_real_min = data.tiempo_real_min
    if data.evidencia_entrega:
        obj.evidencia_entrega = data.evidencia_entrega
    if data.motivo_cancelacion:
        obj.motivo_cancelacion = data.motivo_cancelacion
    now = datetime.now()
    if data.state == 'picked_up':
        obj.fecha_recoleccion = now
    elif data.state == 'delivered':
        obj.fecha_entrega = now
        if obj.repartidor:
            obj.repartidor.state = 'available'
    elif data.state in {'cancelled', 'failed'}:
        if obj.repartidor:
            obj.repartidor.state = 'available'
    log = RepEntregaLog(
        entrega_id=obj.id,
        tipo='estado',
        estado_anterior=prev_state,
        estado_nuevo=data.state,
        repartidor_id=obj.repartidor_id,
        notas='',
    )
    db.add(log)
    db.commit()
    db.refresh(obj)
    # Notificaciones post-cambio de estado (no bloquean si fallan)
    try:
        from fastapi_modulo.modulos.repartidores.servicios.notificaciones import (
            notif_entrega_confirmada,
            notif_repartidor_en_camino,
        )
        if data.state == 'in_transit' and obj.repartidor:
            notif_repartidor_en_camino(db, obj, obj.repartidor)
            db.commit()
        elif data.state == 'delivered':
            notif_entrega_confirmada(db, obj)
            db.commit()
    except Exception as _notif_exc:
        import logging as _lg
        _lg.getLogger(__name__).warning('notif update_entrega_state: %s', _notif_exc)
    return obj


def create_incidencia(db: Session, data: IncidenciaCreate) -> RepIncidencia:
    entrega = get_entrega(db, data.entrega_id)
    if not entrega:
        raise ValueError('La entrega no existe')
    if data.repartidor_id is not None:
        repartidor = get_repartidor(db, data.repartidor_id)
        if not repartidor:
            raise ValueError('El repartidor no existe')
    obj = RepIncidencia(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_liquidaciones(db: Session, repartidor_id: Optional[int] = None, state: Optional[str] = None) -> List[RepLiquidacion]:
    q = db.query(RepLiquidacion)
    if repartidor_id:
        q = q.filter(RepLiquidacion.repartidor_id == repartidor_id)
    if state:
        q = q.filter(RepLiquidacion.state == state)
    return q.order_by(RepLiquidacion.id.desc()).all()


def generate_liquidacion(db: Session, data: GenerarLiquidacionInput) -> RepLiquidacion:
    repartidor = get_repartidor(db, data.repartidor_id)
    if not repartidor:
        raise ValueError('Repartidor no encontrado')

    # Bloqueo de reliquidación: no permitir si ya existe liquidación aprobada en el mismo periodo
    conflicto = (
        db.query(RepLiquidacion)
        .filter(
            RepLiquidacion.repartidor_id == data.repartidor_id,
            RepLiquidacion.state.in_({'approved', 'paid'}),
            RepLiquidacion.fecha_inicio <= data.fecha_fin,
            RepLiquidacion.fecha_fin >= data.fecha_inicio,
        )
        .first()
    )
    if conflicto:
        raise ValueError(
            f'Ya existe una liquidación {conflicto.state} (#{conflicto.id}) '
            f'que cubre el periodo indicado'
        )

    start_dt = datetime.combine(data.fecha_inicio, datetime.min.time())
    end_dt = datetime.combine(data.fecha_fin, datetime.max.time())
    entregas = (
        db.query(RepEntrega)
        .filter(
            RepEntrega.repartidor_id == data.repartidor_id,
            RepEntrega.state == 'delivered',
            RepEntrega.fecha_entrega >= start_dt,
            RepEntrega.fecha_entrega <= end_dt,
            RepEntrega.liquidable == True,
        )
        .all()
    )
    if not entregas:
        raise ValueError('No hay entregas liquidables en el periodo indicado')
    liquidacion = RepLiquidacion(
        repartidor_id=data.repartidor_id,
        fecha_inicio=data.fecha_inicio,
        fecha_fin=data.fecha_fin,
        state='draft',
        notas=data.notas,
    )
    db.add(liquidacion)
    db.flush()

    total_base = Decimal('0.00')
    total_bonos = Decimal('0.00')
    for entrega in entregas:
        monto_base = _to_decimal(repartidor.tarifa_base)
        bono = _to_decimal(repartidor.bono_por_entrega)
        total = monto_base + bono
        line = RepLiquidacionLinea(
            liquidacion_id=liquidacion.id,
            entrega_id=entrega.id,
            monto_base=monto_base,
            bono=bono,
            descuento=Decimal('0.00'),
            total=total,
        )
        db.add(line)
        total_base += monto_base
        total_bonos += bono
    descuentos = _to_decimal(data.descuentos)
    liquidacion.total_entregas = len(entregas)
    liquidacion.total_base = total_base
    liquidacion.total_bonos = total_bonos
    liquidacion.total_descuentos = descuentos
    liquidacion.total_pagar = total_base + total_bonos - descuentos
    db.commit()
    db.refresh(liquidacion)
    return liquidacion


def list_incidencias(db: Session, state: Optional[str] = None, entrega_id: Optional[int] = None) -> List[RepIncidencia]:
    q = db.query(RepIncidencia)
    if state:
        q = q.filter(RepIncidencia.state == state)
    if entrega_id:
        q = q.filter(RepIncidencia.entrega_id == entrega_id)
    return q.order_by(RepIncidencia.id.desc()).all()


def get_dashboard_stats(db: Session) -> dict:
    total_repartidores = db.query(RepRepartidor).filter(RepRepartidor.activo == True).count()
    total_entregas = db.query(RepEntrega).count()
    by_state = {state: db.query(RepEntrega).filter(RepEntrega.state == state).count() for state in ALLOWED_ENTREGA_STATES}
    incidencias_abiertas = db.query(RepIncidencia).filter(RepIncidencia.state == 'open').count()
    liquidaciones_borrador = db.query(RepLiquidacion).filter(RepLiquidacion.state == 'draft').count()
    disponibles = db.query(RepRepartidor).filter(RepRepartidor.activo == True, RepRepartidor.state == 'available').count()
    ocupados = db.query(RepRepartidor).filter(RepRepartidor.activo == True, RepRepartidor.state == 'busy').count()
    return {
        'repartidores': total_repartidores,
        'disponibles': disponibles,
        'ocupados': ocupados,
        'entregas': total_entregas,
        'by_state': by_state,
        'incidencias_abiertas': incidencias_abiertas,
        'liquidaciones_borrador': liquidaciones_borrador,
    }


def get_liquidacion(db: Session, liquidacion_id: int) -> Optional[RepLiquidacion]:
    return db.query(RepLiquidacion).filter(RepLiquidacion.id == liquidacion_id).first()


def update_liquidacion_state(db: Session, liquidacion_id: int, data: ActualizarLiquidacionEstadoInput) -> RepLiquidacion:
    liq = get_liquidacion(db, liquidacion_id)
    if not liq:
        raise ValueError('Liquidación no encontrada')
    transitions = {
        'draft': {'approved'},
        'approved': {'paid'},
    }
    if data.state not in transitions.get(liq.state, set()):
        raise ValueError(
            f'No se puede pasar de "{liq.state}" a "{data.state}"'
        )
    liq.state = data.state
    now = datetime.now()
    if data.state == 'approved':
        liq.fecha_aprobacion = now
    elif data.state == 'paid':
        liq.fecha_pago = now
    if data.notas:
        liq.notas = (liq.notas + '\n' + data.notas).strip()
    db.commit()
    db.refresh(liq)
    return liq


def get_entrega_log(db: Session, entrega_id: int) -> List[RepEntregaLog]:
    return (
        db.query(RepEntregaLog)
        .filter(RepEntregaLog.entrega_id == entrega_id)
        .order_by(RepEntregaLog.id.asc())
        .all()
    )


# ---------------------------------------------------------------------------
# FASE 6 — ANALÍTICA E INTELIGENCIA OPERATIVA
# ---------------------------------------------------------------------------

def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ('%Y-%m-%d', '%Y-%m'):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def get_kpis_periodo(
    db: Session,
    fecha_inicio: str | None = None,
    fecha_fin: str | None = None,
    repartidor_id: int | None = None,
) -> dict:
    """KPIs por periodo: totales, tasa de éxito/cancelación, tiempo promedio."""
    from sqlalchemy import func as sqlfunc

    q = db.query(RepEntrega)
    dt_ini = _parse_date(fecha_inicio)
    dt_fin = _parse_date(fecha_fin)
    if dt_ini:
        q = q.filter(RepEntrega.created_at >= dt_ini)
    if dt_fin:
        q = q.filter(RepEntrega.created_at <= dt_fin)
    if repartidor_id:
        q = q.filter(RepEntrega.repartidor_id == repartidor_id)

    total = q.count()
    entregadas = q.filter(RepEntrega.state == 'delivered').count()
    canceladas = q.filter(RepEntrega.state == 'cancelled').count()
    fallidas = q.filter(RepEntrega.state == 'failed').count()

    # Tiempo promedio real en minutos (solo entregas con tiempo_real_min > 0)
    q2 = db.query(sqlfunc.avg(RepEntrega.tiempo_real_min)).filter(
        RepEntrega.tiempo_real_min > 0,
    )
    if dt_ini:
        q2 = q2.filter(RepEntrega.created_at >= dt_ini)
    if dt_fin:
        q2 = q2.filter(RepEntrega.created_at <= dt_fin)
    if repartidor_id:
        q2 = q2.filter(RepEntrega.repartidor_id == repartidor_id)
    tiempo_promedio = float(q2.scalar() or 0)

    tasa_exito = round(entregadas / total * 100, 1) if total else 0.0
    tasa_cancelacion = round(canceladas / total * 100, 1) if total else 0.0

    return {
        'periodo': {'inicio': fecha_inicio or '', 'fin': fecha_fin or ''},
        'total': total,
        'entregadas': entregadas,
        'canceladas': canceladas,
        'fallidas': fallidas,
        'en_curso': total - entregadas - canceladas - fallidas,
        'tasa_exito_pct': tasa_exito,
        'tasa_cancelacion_pct': tasa_cancelacion,
        'tiempo_promedio_min': round(tiempo_promedio, 1),
        'repartidor_id': repartidor_id,
    }


def get_productividad_repartidores(
    db: Session,
    fecha_inicio: str | None = None,
    fecha_fin: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """Comparativo de productividad entre repartidores."""
    from sqlalchemy import func as sqlfunc

    dt_ini = _parse_date(fecha_inicio)
    dt_fin = _parse_date(fecha_fin)

    repartidores = (
        db.query(RepRepartidor)
        .filter(RepRepartidor.activo == True)
        .order_by(RepRepartidor.name)
        .limit(limit)
        .all()
    )

    resultado = []
    for rep in repartidores:
        q = db.query(RepEntrega).filter(RepEntrega.repartidor_id == rep.id)
        if dt_ini:
            q = q.filter(RepEntrega.created_at >= dt_ini)
        if dt_fin:
            q = q.filter(RepEntrega.created_at <= dt_fin)

        total = q.count()
        entregadas = q.filter(RepEntrega.state == 'delivered').count()
        canceladas = q.filter(RepEntrega.state == 'cancelled').count()
        incidencias = (
            db.query(RepIncidencia)
            .filter(RepIncidencia.repartidor_id == rep.id)
            .count()
        )

        t_prom = (
            db.query(sqlfunc.avg(RepEntrega.tiempo_real_min))
            .filter(
                RepEntrega.repartidor_id == rep.id,
                RepEntrega.tiempo_real_min > 0,
            )
            .scalar()
        )

        resultado.append({
            'repartidor_id': rep.id,
            'nombre': rep.name,
            'codigo': rep.codigo,
            'zona': rep.zona.name if rep.zona else '',
            'total_entregas': total,
            'entregadas': entregadas,
            'canceladas': canceladas,
            'tasa_exito_pct': round(entregadas / total * 100, 1) if total else 0.0,
            'tiempo_promedio_min': round(float(t_prom or 0), 1),
            'incidencias': incidencias,
        })

    # Ordenar por efectividad descendente
    resultado.sort(key=lambda r: (r['entregadas'], r['tasa_exito_pct']), reverse=True)
    return resultado


def get_entregas_por_zona(
    db: Session,
    fecha_inicio: str | None = None,
    fecha_fin: str | None = None,
) -> list[dict]:
    """Distribución de entregas por zona con conteos por estado."""
    dt_ini = _parse_date(fecha_inicio)
    dt_fin = _parse_date(fecha_fin)

    zonas = db.query(RepZona).filter(RepZona.active == True).order_by(RepZona.name).all()
    resultado = []
    for zona in zonas:
        q = db.query(RepEntrega).filter(RepEntrega.zona_id == zona.id)
        if dt_ini:
            q = q.filter(RepEntrega.created_at >= dt_ini)
        if dt_fin:
            q = q.filter(RepEntrega.created_at <= dt_fin)

        total = q.count()
        if total == 0:
            continue

        resultado.append({
            'zona_id': zona.id,
            'zona_code': zona.code,
            'zona_name': zona.name,
            'total': total,
            'entregadas': q.filter(RepEntrega.state == 'delivered').count(),
            'canceladas': q.filter(RepEntrega.state == 'cancelled').count(),
            'en_curso': q.filter(RepEntrega.state.in_(['assigned', 'picked_up', 'in_transit'])).count(),
        })

    resultado.sort(key=lambda z: z['total'], reverse=True)
    return resultado


def get_margen_logistico(
    db: Session,
    fecha_inicio: str | None = None,
    fecha_fin: str | None = None,
    repartidor_id: int | None = None,
) -> dict:
    """Costo vs ingreso por entrega — margen logístico."""
    from sqlalchemy import func as sqlfunc

    dt_ini = _parse_date(fecha_inicio)
    dt_fin = _parse_date(fecha_fin)

    q_entregas = db.query(RepEntrega).filter(RepEntrega.state == 'delivered')
    if dt_ini:
        q_entregas = q_entregas.filter(RepEntrega.created_at >= dt_ini)
    if dt_fin:
        q_entregas = q_entregas.filter(RepEntrega.created_at <= dt_fin)
    if repartidor_id:
        q_entregas = q_entregas.filter(RepEntrega.repartidor_id == repartidor_id)

    entregas = q_entregas.all()
    total_ingreso = sum(float(e.costo_envio or 0) for e in entregas)

    # Costo = lo que se paga al repartidor (desde líneas de liquidación)
    q_lineas = (
        db.query(sqlfunc.sum(RepLiquidacionLinea.total))
        .join(RepLiquidacion, RepLiquidacionLinea.liquidacion_id == RepLiquidacion.id)
        .join(RepEntrega, RepLiquidacionLinea.entrega_id == RepEntrega.id)
    )
    if dt_ini:
        q_lineas = q_lineas.filter(RepEntrega.created_at >= dt_ini)
    if dt_fin:
        q_lineas = q_lineas.filter(RepEntrega.created_at <= dt_fin)
    if repartidor_id:
        q_lineas = q_lineas.filter(RepLiquidacion.repartidor_id == repartidor_id)

    total_costo = float(q_lineas.scalar() or 0)
    margen = total_ingreso - total_costo
    margen_pct = round(margen / total_ingreso * 100, 1) if total_ingreso else 0.0
    n = len(entregas)

    return {
        'periodo': {'inicio': fecha_inicio or '', 'fin': fecha_fin or ''},
        'entregas_entregadas': n,
        'ingreso_total': round(total_ingreso, 2),
        'costo_total': round(total_costo, 2),
        'margen_total': round(margen, 2),
        'margen_pct': margen_pct,
        'ingreso_promedio': round(total_ingreso / n, 2) if n else 0.0,
        'costo_promedio': round(total_costo / n, 2) if n else 0.0,
    }


def get_tendencia(
    db: Session,
    agrupacion: str = 'semana',
    semanas: int = 12,
) -> list[dict]:
    """Tendencia semanal o mensual del volumen de entregas.

    agrupacion: 'semana' | 'mes'
    semanas: cuántas semanas/meses hacia atrás mostrar
    """
    from datetime import timedelta

    now = datetime.utcnow()
    resultado = []

    if agrupacion == 'mes':
        # Últimos N meses
        for i in range(semanas - 1, -1, -1):
            # Primer día del mes hace i meses
            year = now.year
            month = now.month - i
            while month <= 0:
                month += 12
                year -= 1
            inicio = datetime(year, month, 1)
            if month == 12:
                fin = datetime(year + 1, 1, 1)
            else:
                fin = datetime(year, month + 1, 1)

            total = (
                db.query(RepEntrega)
                .filter(RepEntrega.created_at >= inicio, RepEntrega.created_at < fin)
                .count()
            )
            entregadas = (
                db.query(RepEntrega)
                .filter(
                    RepEntrega.created_at >= inicio,
                    RepEntrega.created_at < fin,
                    RepEntrega.state == 'delivered',
                )
                .count()
            )
            resultado.append({
                'periodo': inicio.strftime('%Y-%m'),
                'inicio': inicio.isoformat(),
                'fin': fin.isoformat(),
                'total': total,
                'entregadas': entregadas,
            })
    else:
        # Últimas N semanas
        for i in range(semanas - 1, -1, -1):
            inicio = now - timedelta(weeks=i + 1)
            fin = now - timedelta(weeks=i)
            # Normalizar a inicio de día lunes
            inicio = inicio - timedelta(days=inicio.weekday())
            inicio = inicio.replace(hour=0, minute=0, second=0, microsecond=0)
            fin = inicio + timedelta(weeks=1)

            total = (
                db.query(RepEntrega)
                .filter(RepEntrega.created_at >= inicio, RepEntrega.created_at < fin)
                .count()
            )
            entregadas = (
                db.query(RepEntrega)
                .filter(
                    RepEntrega.created_at >= inicio,
                    RepEntrega.created_at < fin,
                    RepEntrega.state == 'delivered',
                )
                .count()
            )
            resultado.append({
                'periodo': inicio.strftime('Sem %W/%Y'),
                'inicio': inicio.isoformat(),
                'fin': fin.isoformat(),
                'total': total,
                'entregadas': entregadas,
            })

    return resultado


def get_reporte_incidencias(
    db: Session,
    fecha_inicio: str | None = None,
    fecha_fin: str | None = None,
    repartidor_id: int | None = None,
) -> dict:
    """Reporte de incidencias por tipo, severidad y repartidor."""
    dt_ini = _parse_date(fecha_inicio)
    dt_fin = _parse_date(fecha_fin)

    q = db.query(RepIncidencia)
    if dt_ini:
        q = q.filter(RepIncidencia.created_at >= dt_ini)
    if dt_fin:
        q = q.filter(RepIncidencia.created_at <= dt_fin)
    if repartidor_id:
        q = q.filter(RepIncidencia.repartidor_id == repartidor_id)

    incidencias = q.all()

    por_tipo: dict[str, int] = {}
    por_severidad: dict[str, int] = {}
    por_rep: dict[int, dict] = {}

    for inc in incidencias:
        por_tipo[inc.tipo] = por_tipo.get(inc.tipo, 0) + 1
        por_severidad[inc.severidad] = por_severidad.get(inc.severidad, 0) + 1
        if inc.repartidor_id:
            if inc.repartidor_id not in por_rep:
                nombre = inc.repartidor.name if inc.repartidor else str(inc.repartidor_id)
                por_rep[inc.repartidor_id] = {'repartidor_id': inc.repartidor_id, 'nombre': nombre, 'total': 0}
            por_rep[inc.repartidor_id]['total'] += 1

    return {
        'periodo': {'inicio': fecha_inicio or '', 'fin': fecha_fin or ''},
        'total': len(incidencias),
        'abiertas': sum(1 for i in incidencias if i.state == 'open'),
        'resueltas': sum(1 for i in incidencias if i.state == 'resolved'),
        'por_tipo': por_tipo,
        'por_severidad': por_severidad,
        'por_repartidor': sorted(por_rep.values(), key=lambda r: r['total'], reverse=True),
    }


def exportar_entregas_csv(
    db: Session,
    fecha_inicio: str | None = None,
    fecha_fin: str | None = None,
    repartidor_id: int | None = None,
    state: str | None = None,
) -> str:
    """Retorna contenido CSV con el listado de entregas filtrado."""
    import csv
    import io

    dt_ini = _parse_date(fecha_inicio)
    dt_fin = _parse_date(fecha_fin)

    q = db.query(RepEntrega)
    if dt_ini:
        q = q.filter(RepEntrega.created_at >= dt_ini)
    if dt_fin:
        q = q.filter(RepEntrega.created_at <= dt_fin)
    if repartidor_id:
        q = q.filter(RepEntrega.repartidor_id == repartidor_id)
    if state:
        q = q.filter(RepEntrega.state == state)
    q = q.order_by(RepEntrega.created_at.desc())

    campos = [
        'folio', 'estado', 'prioridad', 'cliente_nombre', 'cliente_telefono',
        'origen', 'destino', 'repartidor', 'zona',
        'costo_envio', 'tiempo_real_min',
        'fecha_programada', 'fecha_asignacion', 'fecha_recoleccion', 'fecha_entrega',
        'evidencia_entrega', 'motivo_cancelacion', 'created_at',
    ]

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=campos)
    writer.writeheader()

    for e in q.all():
        writer.writerow({
            'folio': e.folio,
            'estado': e.state,
            'prioridad': e.prioridad,
            'cliente_nombre': e.cliente_nombre,
            'cliente_telefono': e.cliente_telefono or '',
            'origen': e.origen or '',
            'destino': e.destino,
            'repartidor': e.repartidor.name if e.repartidor else '',
            'zona': e.zona.name if e.zona else '',
            'costo_envio': str(e.costo_envio or 0),
            'tiempo_real_min': str(e.tiempo_real_min or 0),
            'fecha_programada': e.fecha_programada.isoformat() if e.fecha_programada else '',
            'fecha_asignacion': e.fecha_asignacion.isoformat() if e.fecha_asignacion else '',
            'fecha_recoleccion': e.fecha_recoleccion.isoformat() if e.fecha_recoleccion else '',
            'fecha_entrega': e.fecha_entrega.isoformat() if e.fecha_entrega else '',
            'evidencia_entrega': (e.evidencia_entrega or '').replace('\n', ' '),
            'motivo_cancelacion': (e.motivo_cancelacion or '').replace('\n', ' '),
            'created_at': e.created_at.isoformat() if e.created_at else '',
        })

    return output.getvalue()


# ---------------------------------------------------------------------------
# FASE 7 — GEOLOCALIZACIÓN Y SEGUIMIENTO
# ---------------------------------------------------------------------------

import math as _math


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distancia en km entre dos puntos usando la fórmula de Haversine."""
    R = 6371.0
    lat1, lng1, lat2, lng2 = map(_math.radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = _math.sin(dlat / 2) ** 2 + _math.cos(lat1) * _math.cos(lat2) * _math.sin(dlng / 2) ** 2
    return R * 2 * _math.asin(_math.sqrt(a))


def update_repartidor_posicion(db: Session, repartidor_id: int, data: PosicionUpdate) -> RepRepartidorPosicion:
    """Upsert de la posición actual del repartidor."""
    pos = (
        db.query(RepRepartidorPosicion)
        .filter(RepRepartidorPosicion.repartidor_id == repartidor_id)
        .first()
    )
    if pos:
        pos.lat = data.lat
        pos.lng = data.lng
        pos.precision_m = data.precision_m
        pos.updated_at = datetime.utcnow()
    else:
        pos = RepRepartidorPosicion(
            repartidor_id=repartidor_id,
            lat=data.lat,
            lng=data.lng,
            precision_m=data.precision_m,
        )
        db.add(pos)
    db.commit()
    db.refresh(pos)
    return pos


def calcular_distancia_entrega(db: Session, entrega_id: int) -> Optional[RepEntrega]:
    """Calcula distancia_km y tiempo_estimado_min a partir de las coords de la entrega."""
    entrega = get_entrega(db, entrega_id)
    if not entrega:
        return None
    lat_o = entrega.lat_origen
    lng_o = entrega.lng_origen
    lat_d = entrega.lat_destino
    lng_d = entrega.lng_destino
    if None in (lat_o, lng_o, lat_d, lng_d):
        return entrega  # sin coordenadas, no se hace nada

    distancia = round(_haversine(lat_o, lng_o, lat_d, lng_d), 3)
    entrega.distancia_km = distancia
    # Estimado simple: 30 km/h promedio en ciudad
    entrega.tiempo_estimado_min = max(1, int(distancia / 30 * 60))
    db.commit()
    db.refresh(entrega)
    return entrega


def get_repartidores_cercanos(
    db: Session,
    lat: float,
    lng: float,
    radio_km: float = 5.0,
    solo_disponibles: bool = True,
) -> list[dict]:
    """Retorna repartidores ordenados por distancia al punto dado."""
    q = db.query(RepRepartidor).filter(RepRepartidor.activo == True)
    if solo_disponibles:
        q = q.filter(RepRepartidor.state == 'available')

    resultado = []
    for rep in q.all():
        pos = rep.posicion
        if not pos:
            continue
        dist = _haversine(lat, lng, pos.lat, pos.lng)
        if dist <= radio_km:
            resultado.append({
                'repartidor_id': rep.id,
                'nombre': rep.name,
                'codigo': rep.codigo,
                'state': rep.state,
                'zona_id': rep.zona_id,
                'zona_name': rep.zona.name if rep.zona else '',
                'lat': pos.lat,
                'lng': pos.lng,
                'distancia_km': round(dist, 3),
                'precision_m': pos.precision_m,
                'posicion_updated_at': pos.updated_at.isoformat() if pos.updated_at else '',
            })

    resultado.sort(key=lambda r: r['distancia_km'])
    return resultado


def get_mapa_entregas(
    db: Session,
    state: Optional[str] = None,
    solo_con_coords: bool = False,
) -> list[dict]:
    """Datos de entregas para capa de mapa (solo las que tienen coords)."""
    q = db.query(RepEntrega)
    if state:
        q = q.filter(RepEntrega.state == state)
    if solo_con_coords:
        q = q.filter(
            RepEntrega.lat_destino.isnot(None),
            RepEntrega.lng_destino.isnot(None),
        )
    q = q.order_by(RepEntrega.fecha_programada)

    resultado = []
    for e in q.all():
        resultado.append({
            'id': e.id,
            'folio': e.folio,
            'state': e.state,
            'prioridad': e.prioridad,
            'cliente_nombre': e.cliente_nombre,
            'destino': e.destino,
            'lat_origen': e.lat_origen,
            'lng_origen': e.lng_origen,
            'lat_destino': e.lat_destino,
            'lng_destino': e.lng_destino,
            'distancia_km': float(e.distancia_km or 0),
            'repartidor_id': e.repartidor_id,
            'repartidor_nombre': e.repartidor.name if e.repartidor else None,
            'zona_id': e.zona_id,
            'zona_name': e.zona.name if e.zona else None,
        })
    return resultado


def get_mapa_repartidores(db: Session) -> list[dict]:
    """Posiciones actuales de repartidores activos para capa de mapa."""
    repartidores = (
        db.query(RepRepartidor)
        .filter(RepRepartidor.activo == True)
        .order_by(RepRepartidor.name)
        .all()
    )
    resultado = []
    for rep in repartidores:
        pos = rep.posicion
        activas = (
            db.query(RepEntrega)
            .filter(
                RepEntrega.repartidor_id == rep.id,
                RepEntrega.state.in_(['assigned', 'picked_up', 'in_transit']),
            )
            .count()
        )
        resultado.append({
            'id': rep.id,
            'nombre': rep.name,
            'codigo': rep.codigo,
            'state': rep.state,
            'lat': pos.lat if pos else None,
            'lng': pos.lng if pos else None,
            'precision_m': pos.precision_m if pos else None,
            'posicion_updated_at': pos.updated_at.isoformat() if (pos and pos.updated_at) else None,
            'zona_id': rep.zona_id,
            'zona_name': rep.zona.name if rep.zona else None,
            'entregas_activas': activas,
        })
    return resultado


def get_zonas_mapa(db: Session) -> list[dict]:
    """Retorna zonas con datos suficientes para dibujar círculos en mapa."""
    zonas = db.query(RepZona).filter(RepZona.active == True).order_by(RepZona.name).all()
    return [
        {
            'id': z.id,
            'name': z.name,
            'code': z.code,
            'ciudad': z.ciudad,
            'radio_km': z.radio_km,
            'lat_centro': z.lat_centro,
            'lng_centro': z.lng_centro,
        }
        for z in zonas
    ]
