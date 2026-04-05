from __future__ import annotations
import os
import secrets
import smtplib
from datetime import datetime, date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from fastapi_modulo.modulos.reservaciones.modelos.db_models import (
    ResCita, ResEjecutivo, ResTipoCita,
    ResBloqueoAgenda, ResExcepcionFecha, ResHorarioSemanal,
)
from fastapi_modulo.modulos.reservaciones.modelos.schemas import (
    BloqueoCreate, CitaCreate, CitaUpdate, EjecutivoCreate, EjecutivoUpdate,
    ExcepcionCreate, FranjaCreate, ReprogramarCita, TipoCitaCreate,
)


# ── Ejecutivos ───────────────────────────────────────────────────────────────

def list_ejecutivos(db: Session, solo_activos: bool = True) -> List[ResEjecutivo]:
    q = db.query(ResEjecutivo)
    if solo_activos:
        q = q.filter(ResEjecutivo.active == True)
    return q.order_by(ResEjecutivo.name).all()


def get_ejecutivo(db: Session, ejecutivo_id: int) -> Optional[ResEjecutivo]:
    return db.query(ResEjecutivo).filter(ResEjecutivo.id == ejecutivo_id).first()


def create_ejecutivo(db: Session, data: EjecutivoCreate) -> ResEjecutivo:
    obj = ResEjecutivo(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_ejecutivo(db: Session, ejecutivo_id: int, data: EjecutivoUpdate) -> Optional[ResEjecutivo]:
    obj = get_ejecutivo(db, ejecutivo_id)
    if not obj:
        return None
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


# ── Tipos de Cita ────────────────────────────────────────────────────────────

def list_tipos(db: Session) -> List[ResTipoCita]:
    return db.query(ResTipoCita).filter(ResTipoCita.active == True).order_by(ResTipoCita.name).all()


def create_tipo(db: Session, data: TipoCitaCreate) -> ResTipoCita:
    obj = ResTipoCita(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ── Constantes de negocio ─────────────────────────────────────────────────────

DESCANSO_MAP = {
    0: ("descanso_lunes",    "hora_inicial_lunes",    "hora_final_lunes"),
    1: ("descanso_martes",   "hora_inicial_martes",   "hora_final_martes"),
    2: ("descanso_miercoles","hora_inicial_miercoles","hora_final_miercoles"),
    3: ("descanso_jueves",   "hora_inicial_jueves",   "hora_final_jueves"),
    4: ("descanso_viernes",  "hora_inicial_viernes",  "hora_final_viernes"),
    5: ("descanso_sabado",   "hora_inicial_sabado",   "hora_final_sabado"),
    6: ("descanso_domingo",  "hora_inicial_domingo",  "hora_final_domingo"),
}

# Transiciones de estado permitidas
VALID_TRANSITIONS: dict[str, set] = {
    "draft":       {"confirmed", "cancelled"},
    "confirmed":   {"in_progress", "cancelled"},
    "in_progress": {"completed", "no_show"},
    "completed":   set(),
    "cancelled":   set(),
    "no_show":     set(),
}


def _float_to_hhmm(f: float) -> str:
    h = int(f)
    m = int(round((f - h) * 60))
    return f"{h:02d}:{m:02d}"


def _get_duracion_minutos(ejecutivo: Optional[ResEjecutivo], tipo: Optional[ResTipoCita]) -> int:
    """Determina la duración de una cita en minutos según el tipo o el ejecutivo."""
    if tipo and tipo.duracion_minutos:
        return tipo.duracion_minutos
    if ejecutivo:
        return (ejecutivo.tiempo_promedio_cita or 30)
    return 30


# ── Citas ────────────────────────────────────────────────────────────────────

def list_citas(db: Session, limit: int = 100, ejecutivo_id: Optional[int] = None, state: Optional[str] = None) -> List[ResCita]:
    q = db.query(ResCita)
    if ejecutivo_id:
        q = q.filter(ResCita.ejecutivo_id == ejecutivo_id)
    if state:
        q = q.filter(ResCita.state == state)
    return q.order_by(ResCita.start_datetime.desc()).limit(limit).all()


def get_cita(db: Session, cita_id: int) -> Optional[ResCita]:
    return db.query(ResCita).filter(ResCita.id == cita_id).first()


def create_cita(db: Session, data: CitaCreate, source: str = "admin") -> ResCita:
    """Crea una cita con validación completa de disponibilidad y horario."""
    # a) Ejecutivo existe y está activo
    ejecutivo: Optional[ResEjecutivo] = None
    if data.ejecutivo_id:
        ejecutivo = get_ejecutivo(db, data.ejecutivo_id)
        if not ejecutivo:
            raise ValueError("Ejecutivo no encontrado")
        if not ejecutivo.active:
            raise ValueError("El ejecutivo no está activo")

    # b) Tipo de cita existe y está activo
    tipo: Optional[ResTipoCita] = None
    if data.tipo_id:
        tipo = db.query(ResTipoCita).filter(
            ResTipoCita.id == data.tipo_id,
            ResTipoCita.active == True,
        ).first()
        if not tipo:
            raise ValueError("Tipo de cita no encontrado o inactivo")

    # c, d) Validar horario del ejecutivo
    if ejecutivo:
        dow = data.start_datetime.weekday()
        descanso_field, hora_ini_field, hora_fin_field = DESCANSO_MAP[dow]
        if getattr(ejecutivo, descanso_field, True):
            raise ValueError("El ejecutivo no atiende ese día de la semana")
        hora_ini = getattr(ejecutivo, hora_ini_field, 9.0) or 9.0
        hora_fin = getattr(ejecutivo, hora_fin_field, 17.0) or 17.0
        hora_cita_float = data.start_datetime.hour + data.start_datetime.minute / 60.0
        if hora_cita_float < hora_ini or hora_cita_float >= hora_fin:
            raise ValueError(
                f"El horario seleccionado ({data.start_datetime.strftime('%H:%M')}) "
                f"está fuera de la jornada del ejecutivo "
                f"({_float_to_hhmm(hora_ini)}–{_float_to_hhmm(hora_fin)})"
            )

    # Calcular end_datetime
    duracion_min = _get_duracion_minutos(ejecutivo, tipo)
    end_dt = data.start_datetime + timedelta(minutes=duracion_min)

    # f) Validar solapamiento con citas existentes
    if data.ejecutivo_id:
        # Citas nuevas con end_datetime: cruce de intervalos
        solapamiento = db.query(ResCita).filter(
            ResCita.ejecutivo_id == data.ejecutivo_id,
            ResCita.state.notin_(["cancelled", "no_show"]),
            ResCita.end_datetime.isnot(None),
            ResCita.start_datetime < end_dt,
            ResCita.end_datetime > data.start_datetime,
        ).first()
        if not solapamiento:
            # Fallback: citas antiguas sin end_datetime (comparación exacta)
            solapamiento = db.query(ResCita).filter(
                ResCita.ejecutivo_id == data.ejecutivo_id,
                ResCita.state.notin_(["cancelled", "no_show"]),
                ResCita.end_datetime.is_(None),
                ResCita.start_datetime == data.start_datetime,
            ).first()
        if solapamiento:
            raise ValueError(
                f"El horario se solapa con una cita existente a las "
                f"{solapamiento.start_datetime.strftime('%H:%M')}"
            )

    obj = ResCita(**data.model_dump(), end_datetime=end_dt, source=source)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_cita_state(
    db: Session,
    cita_id: int,
    state: str,
    motivo: Optional[str] = None,
) -> Optional[ResCita]:
    """Cambia el estado de una cita respetando las transiciones válidas."""
    obj = get_cita(db, cita_id)
    if not obj:
        return None

    allowed = VALID_TRANSITIONS.get(obj.state, set())
    if state not in allowed:
        allowed_list = sorted(allowed) if allowed else ["ninguno (estado terminal)"]
        raise ValueError(
            f"No se puede pasar de '{obj.state}' a '{state}'. "
            f"Transiciones permitidas: {', '.join(allowed_list)}"
        )

    now = datetime.now()
    obj.state = state

    if state == "confirmed":
        obj.confirmed_at = now
    elif state in ("cancelled", "no_show"):
        obj.cancelled_at = now
        if motivo:
            obj.cancellation_reason = motivo

    db.commit()
    db.refresh(obj)
    return obj


# ── Stats ────────────────────────────────────────────────────────────────────

def get_dashboard_stats(db: Session) -> dict:
    total = db.query(ResCita).count()
    by_state = {}
    for state in ("draft", "confirmed", "in_progress", "completed", "cancelled", "no_show"):
        by_state[state] = db.query(ResCita).filter(ResCita.state == state).count()
    ejecutivos = db.query(ResEjecutivo).filter(ResEjecutivo.active == True).count()
    return {"total": total, "by_state": by_state, "ejecutivos": ejecutivos}


# ── Slots disponibles ────────────────────────────────────────────────────────

def get_slots_for_day(db: Session, ejecutivo_id: int, fecha_str: str) -> List[dict]:
    ejecutivo = get_ejecutivo(db, ejecutivo_id)
    if not ejecutivo:
        return []

    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except ValueError:
        return []

    # Verificar excepción de fecha (global o de este ejecutivo)
    excepcion = db.query(ResExcepcionFecha).filter(
        ResExcepcionFecha.active == True,
        ResExcepcionFecha.fecha == fecha,
        (ResExcepcionFecha.ejecutivo_id == ejecutivo_id) | (ResExcepcionFecha.ejecutivo_id.is_(None)),
    ).first()
    if excepcion:
        return []

    dow = fecha.weekday()
    descanso_field, hora_ini_field, hora_fin_field = DESCANSO_MAP[dow]

    # Franjas múltiples (override de horario)
    franjas = db.query(ResHorarioSemanal).filter(
        ResHorarioSemanal.ejecutivo_id == ejecutivo_id,
        ResHorarioSemanal.dia_semana == dow,
        ResHorarioSemanal.active == True,
    ).order_by(ResHorarioSemanal.hora_ini).all()

    if franjas:
        rangos_horario = [(f.hora_ini, f.hora_fin) for f in franjas]
    else:
        # Fallback: columnas clásicas del ejecutivo
        if getattr(ejecutivo, descanso_field, True):
            return []
        hora_ini = getattr(ejecutivo, hora_ini_field, 9.0) or 9.0
        hora_fin = getattr(ejecutivo, hora_fin_field, 17.0) or 17.0
        rangos_horario = [(hora_ini, hora_fin)]

    bloque_min = (ejecutivo.tiempo_promedio_cita or 30) + (ejecutivo.tiempo_descanso_sesiones or 0)

    inicio_dia = datetime.combine(fecha, datetime.min.time())
    fin_dia = inicio_dia + timedelta(days=1)

    # Citas del día
    citas_dia = db.query(ResCita).filter(
        ResCita.ejecutivo_id == ejecutivo_id,
        ResCita.state.notin_(["cancelled", "no_show"]),
        ResCita.start_datetime >= inicio_dia,
        ResCita.start_datetime < fin_dia,
    ).all()

    # Bloqueos del día
    bloqueos_dia = db.query(ResBloqueoAgenda).filter(
        ResBloqueoAgenda.ejecutivo_id == ejecutivo_id,
        ResBloqueoAgenda.active == True,
        ResBloqueoAgenda.start_datetime < fin_dia,
        ResBloqueoAgenda.end_datetime > inicio_dia,
    ).all()

    def _to_min(dt: datetime) -> float:
        return dt.hour * 60.0 + dt.minute + dt.second / 60.0

    occupied: list[tuple[float, float]] = []
    for c in citas_dia:
        c_start = _to_min(c.start_datetime)
        if c.end_datetime and c.end_datetime.date() == fecha:
            c_end = _to_min(c.end_datetime)
        else:
            c_end = c_start + bloque_min
        occupied.append((c_start, c_end))
    for b in bloqueos_dia:
        b_start = _to_min(b.start_datetime) if b.start_datetime.date() == fecha else 0.0
        b_end = _to_min(b.end_datetime) if b.end_datetime.date() == fecha else 1440.0
        occupied.append((b_start, b_end))

    slots = []
    for hora_ini, hora_fin in rangos_horario:
        current_float = hora_ini
        while current_float + (bloque_min / 60.0) <= hora_fin + 0.001:
            hora_str = _float_to_hhmm(current_float)
            dt_str = f"{fecha_str}T{hora_str}:00"
            slot_start_min = current_float * 60.0
            slot_end_min = slot_start_min + bloque_min
            ocupado = any(s < slot_end_min and e > slot_start_min for s, e in occupied)
            slots.append({
                "datetime_str": dt_str,
                "hora": hora_str,
                "disponible": not ocupado,
            })
            current_float += bloque_min / 60.0

    return slots


# ── Reprogramar cita ──────────────────────────────────────────────────────────

def reprogramar_cita(db: Session, cita_id: int, data: ReprogramarCita) -> ResCita:
    """Cambia la fecha/hora de una cita validando disponibilidad."""
    obj = get_cita(db, cita_id)
    if not obj:
        raise ValueError("Cita no encontrada")
    if obj.state in ("completed", "cancelled", "no_show"):
        raise ValueError(f"No se puede reprogramar una cita en estado '{obj.state}'")

    nueva_start = data.new_start_datetime
    if nueva_start < datetime.now():
        raise ValueError("La nueva fecha no puede ser en el pasado")

    # Mismo ejecutivo y tipo
    ejecutivo: Optional[ResEjecutivo] = None
    if obj.ejecutivo_id:
        ejecutivo = get_ejecutivo(db, obj.ejecutivo_id)

    tipo: Optional[ResTipoCita] = None
    if obj.tipo_id:
        tipo = db.query(ResTipoCita).filter(ResTipoCita.id == obj.tipo_id).first()

    # Validar horario ejecutivo con nueva fecha
    if ejecutivo:
        dow = nueva_start.weekday()
        descanso_field, hora_ini_field, hora_fin_field = DESCANSO_MAP[dow]
        if getattr(ejecutivo, descanso_field, True):
            raise ValueError("El ejecutivo no atiende ese día de la semana")
        hora_ini = getattr(ejecutivo, hora_ini_field, 9.0) or 9.0
        hora_fin = getattr(ejecutivo, hora_fin_field, 17.0) or 17.0
        hora_float = nueva_start.hour + nueva_start.minute / 60.0
        if hora_float < hora_ini or hora_float >= hora_fin:
            raise ValueError(
                f"El horario seleccionado ({nueva_start.strftime('%H:%M')}) "
                f"está fuera de la jornada del ejecutivo "
                f"({_float_to_hhmm(hora_ini)}–{_float_to_hhmm(hora_fin)})"
            )

    duracion_min = _get_duracion_minutos(ejecutivo, tipo)
    nueva_end = nueva_start + timedelta(minutes=duracion_min)

    # Solapamiento excluyendo la misma cita
    if obj.ejecutivo_id:
        solapamiento = db.query(ResCita).filter(
            ResCita.id != cita_id,
            ResCita.ejecutivo_id == obj.ejecutivo_id,
            ResCita.state.notin_(["cancelled", "no_show"]),
            ResCita.end_datetime.isnot(None),
            ResCita.start_datetime < nueva_end,
            ResCita.end_datetime > nueva_start,
        ).first()
        if solapamiento:
            raise ValueError(
                f"El nuevo horario se solapa con una cita a las "
                f"{solapamiento.start_datetime.strftime('%H:%M')}"
            )

    if data.motivo and obj.notes:
        obj.notes = obj.notes + f"\n[Reprogramada desde {obj.start_datetime.strftime('%Y-%m-%d %H:%M')}]: {data.motivo}"
    elif data.motivo:
        obj.notes = f"[Reprogramada desde {obj.start_datetime.strftime('%Y-%m-%d %H:%M')}]: {data.motivo}"

    obj.start_datetime = nueva_start
    obj.end_datetime = nueva_end
    db.commit()
    db.refresh(obj)
    return obj


# ── Cancelar cita ─────────────────────────────────────────────────────────────

def cancelar_cita(db: Session, cita_id: int, motivo: Optional[str] = None) -> ResCita:
    return update_cita_state(db, cita_id, "cancelled", motivo=motivo)


# ── Agenda del ejecutivo por rango ────────────────────────────────────────────

def get_agenda_ejecutivo(
    db: Session,
    ejecutivo_id: int,
    fecha_ini: str,
    fecha_fin: str,
) -> Dict[str, List[dict]]:
    """Devuelve citas agrupadas por día para un ejecutivo en un rango de fechas."""
    try:
        inicio = datetime.strptime(fecha_ini, "%Y-%m-%d")
        fin = datetime.strptime(fecha_fin, "%Y-%m-%d") + timedelta(days=1)
    except ValueError:
        raise ValueError("Formato de fecha inválido, use YYYY-MM-DD")

    citas = db.query(ResCita).filter(
        ResCita.ejecutivo_id == ejecutivo_id,
        ResCita.start_datetime >= inicio,
        ResCita.start_datetime < fin,
    ).order_by(ResCita.start_datetime).all()

    agenda: Dict[str, List[dict]] = {}
    for c in citas:
        dia_key = c.start_datetime.strftime("%Y-%m-%d")
        if dia_key not in agenda:
            agenda[dia_key] = []
        agenda[dia_key].append({
            "id": c.id,
            "name": c.name,
            "nombre_persona": c.nombre_persona,
            "celular_persona": c.celular_persona,
            "start_datetime": c.start_datetime.isoformat(),
            "end_datetime": c.end_datetime.isoformat() if c.end_datetime else None,
            "state": c.state,
            "tipo_id": c.tipo_id,
            "notes": c.notes,
        })
    return agenda


# ── Disponibilidad por rango ──────────────────────────────────────────────────

def get_disponibilidad_rango(
    db: Session,
    ejecutivo_id: int,
    fecha_ini: str,
    fecha_fin: str,
) -> List[dict]:
    """Devuelve qué días en el rango tienen al menos un slot libre."""
    try:
        inicio = datetime.strptime(fecha_ini, "%Y-%m-%d").date()
        fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Formato de fecha inválido, use YYYY-MM-DD")

    ejecutivo = get_ejecutivo(db, ejecutivo_id)
    if not ejecutivo:
        return []

    resultado = []
    current = inicio
    while current <= fin:
        dow = current.weekday()
        descanso_field, _, _ = DESCANSO_MAP[dow]

        # Excepción de fecha
        excepcion = db.query(ResExcepcionFecha).filter(
            ResExcepcionFecha.active == True,
            ResExcepcionFecha.fecha == current,
            (ResExcepcionFecha.ejecutivo_id == ejecutivo_id) | (ResExcepcionFecha.ejecutivo_id.is_(None)),
        ).first()
        if excepcion:
            resultado.append({"fecha": current.strftime("%Y-%m-%d"), "disponible": False, "slots_libres": 0})
            current += timedelta(days=1)
            continue

        # Franjas múltiples o día de descanso clásico
        franjas = db.query(ResHorarioSemanal).filter(
            ResHorarioSemanal.ejecutivo_id == ejecutivo_id,
            ResHorarioSemanal.dia_semana == dow,
            ResHorarioSemanal.active == True,
        ).count()
        if not franjas and getattr(ejecutivo, descanso_field, True):
            resultado.append({"fecha": current.strftime("%Y-%m-%d"), "disponible": False, "slots_libres": 0})
            current += timedelta(days=1)
            continue

        slots = get_slots_for_day(db, ejecutivo_id, current.strftime("%Y-%m-%d"))
        libres = sum(1 for s in slots if s["disponible"])
        resultado.append({
            "fecha": current.strftime("%Y-%m-%d"),
            "disponible": libres > 0,
            "slots_libres": libres,
        })
        current += timedelta(days=1)
    return resultado


# ── Stats avanzados ───────────────────────────────────────────────────────────

def get_dashboard_stats_avanzado(db: Session) -> dict:
    """KPIs extendidos: totales, tasa cancelación/no-show, citas por ejecutivo."""
    total = db.query(ResCita).count()
    by_state: Dict[str, int] = {}
    for state in ("draft", "confirmed", "in_progress", "completed", "cancelled", "no_show"):
        by_state[state] = db.query(ResCita).filter(ResCita.state == state).count()

    terminales = by_state["completed"] + by_state["cancelled"] + by_state["no_show"]
    tasa_cancelacion = round(by_state["cancelled"] / terminales * 100, 1) if terminales else 0
    tasa_no_show = round(by_state["no_show"] / terminales * 100, 1) if terminales else 0

    # Últimos 30 días
    hace_30 = datetime.now() - timedelta(days=30)
    por_dia_30: Dict[str, int] = {}
    citas_30 = db.query(ResCita).filter(ResCita.start_datetime >= hace_30).all()
    for c in citas_30:
        dia = c.start_datetime.strftime("%Y-%m-%d")
        por_dia_30[dia] = por_dia_30.get(dia, 0) + 1

    # Citas por ejecutivo
    ejecutivos = db.query(ResEjecutivo).filter(ResEjecutivo.active == True).all()
    por_ejecutivo = []
    for ej in ejecutivos:
        cnt = db.query(ResCita).filter(ResCita.ejecutivo_id == ej.id).count()
        cnt_activas = db.query(ResCita).filter(
            ResCita.ejecutivo_id == ej.id,
            ResCita.state.notin_(["cancelled", "no_show"]),
        ).count()
        por_ejecutivo.append({
            "id": ej.id,
            "name": ej.name,
            "total": cnt,
            "activas": cnt_activas,
        })

    return {
        "total": total,
        "by_state": by_state,
        "tasa_cancelacion_pct": tasa_cancelacion,
        "tasa_no_show_pct": tasa_no_show,
        "citas_ultimos_30_dias": por_dia_30,
        "por_ejecutivo": por_ejecutivo,
        "ejecutivos_activos": len(ejecutivos),
    }


# ── Bloqueos de agenda ────────────────────────────────────────────────────────

def list_bloqueos(db: Session, ejecutivo_id: int) -> List[ResBloqueoAgenda]:
    return (
        db.query(ResBloqueoAgenda)
        .filter(ResBloqueoAgenda.ejecutivo_id == ejecutivo_id, ResBloqueoAgenda.active == True)
        .order_by(ResBloqueoAgenda.start_datetime)
        .all()
    )


def create_bloqueo(db: Session, data: BloqueoCreate) -> ResBloqueoAgenda:
    obj = ResBloqueoAgenda(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def delete_bloqueo(db: Session, bloqueo_id: int) -> bool:
    obj = db.query(ResBloqueoAgenda).filter(ResBloqueoAgenda.id == bloqueo_id).first()
    if not obj:
        return False
    obj.active = False
    db.commit()
    return True


# ── Excepciones por fecha ─────────────────────────────────────────────────────

def list_excepciones(db: Session, ejecutivo_id: Optional[int] = None) -> List[ResExcepcionFecha]:
    q = db.query(ResExcepcionFecha).filter(ResExcepcionFecha.active == True)
    if ejecutivo_id is not None:
        q = q.filter(
            (ResExcepcionFecha.ejecutivo_id == ejecutivo_id) | (ResExcepcionFecha.ejecutivo_id.is_(None))
        )
    return q.order_by(ResExcepcionFecha.fecha).all()


def create_excepcion(db: Session, data: ExcepcionCreate) -> ResExcepcionFecha:
    from datetime import date as date_type
    fecha_obj = datetime.strptime(data.fecha, "%Y-%m-%d").date()
    obj = ResExcepcionFecha(
        ejecutivo_id=data.ejecutivo_id,
        fecha=fecha_obj,
        motivo=data.motivo,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def delete_excepcion(db: Session, excepcion_id: int) -> bool:
    obj = db.query(ResExcepcionFecha).filter(ResExcepcionFecha.id == excepcion_id).first()
    if not obj:
        return False
    obj.active = False
    db.commit()
    return True


# ── Franjas horarias semanales ────────────────────────────────────────────────

def list_franjas(db: Session, ejecutivo_id: int) -> List[ResHorarioSemanal]:
    return (
        db.query(ResHorarioSemanal)
        .filter(ResHorarioSemanal.ejecutivo_id == ejecutivo_id, ResHorarioSemanal.active == True)
        .order_by(ResHorarioSemanal.dia_semana, ResHorarioSemanal.hora_ini)
        .all()
    )


def create_franja(db: Session, ejecutivo_id: int, data: FranjaCreate) -> ResHorarioSemanal:
    obj = ResHorarioSemanal(ejecutivo_id=ejecutivo_id, **data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def delete_franja(db: Session, franja_id: int) -> bool:
    obj = db.query(ResHorarioSemanal).filter(ResHorarioSemanal.id == franja_id).first()
    if not obj:
        return False
    obj.active = False
    db.commit()
    return True


# ── Token de cancelación ──────────────────────────────────────────────────────

def generar_token_cancelacion(db: Session, cita_id: int) -> Optional[str]:
    """Genera y almacena un token único de cancelación para la cita."""
    obj = get_cita(db, cita_id)
    if not obj:
        return None
    if obj.state in ("completed", "cancelled", "no_show"):
        raise ValueError(f"No se puede generar token para una cita en estado '{obj.state}'")
    token = secrets.token_urlsafe(32)
    obj.cancel_token = token
    db.commit()
    return token


def cancelar_por_token(db: Session, token: str) -> Optional[ResCita]:
    """Cancela la cita correspondiente al token. Retorna None si no existe."""
    obj = db.query(ResCita).filter(ResCita.cancel_token == token).first()
    if not obj:
        return None
    if obj.state in ("completed", "cancelled", "no_show"):
        raise ValueError(f"La cita ya está en estado '{obj.state}'")
    obj.state = "cancelled"
    obj.cancelled_at = datetime.now()
    obj.cancellation_reason = "Cancelada por el cliente vía enlace"
    obj.cancel_token = None  # invalidar el token
    db.commit()
    db.refresh(obj)
    return obj


# ── Email ─────────────────────────────────────────────────────────────────────

def _build_email_confirmacion(cita: ResCita, ejecutivo: ResEjecutivo, tipo: Optional[ResTipoCita]) -> str:
    tipo_name = tipo.name if tipo else "Sin especificar"
    hora = cita.start_datetime.strftime("%H:%M")
    fecha = cita.start_datetime.strftime("%d/%m/%Y")
    return f"""
<html><body style="font-family:sans-serif;color:#333">
<h2 style="color:#1a6b3c">Confirmación de cita</h2>
<p>Hola <strong>{cita.nombre_persona}</strong>,</p>
<p>Su cita ha sido confirmada con los siguientes datos:</p>
<table cellpadding="8" style="border-collapse:collapse">
  <tr><td><strong>Ejecutivo:</strong></td><td>{ejecutivo.name}</td></tr>
  <tr><td><strong>Tipo de cita:</strong></td><td>{tipo_name}</td></tr>
  <tr><td><strong>Fecha:</strong></td><td>{fecha}</td></tr>
  <tr><td><strong>Hora:</strong></td><td>{hora}</td></tr>
</table>
<p style="margin-top:20px;color:#555;font-size:12px">
  Si necesita cancelar o reprogramar, contáctenos con anticipación.
</p>
</body></html>
"""


def enviar_email_cita(to: str, subject: str, html: str) -> None:
    """Envía un correo usando las variables de entorno SMTP del sistema."""
    host = os.environ.get("SMTP_HOST", "")
    port = int(os.environ.get("SMTP_PORT", 587))
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASSWORD", "")
    from_addr = os.environ.get("EMAIL_FROM", user)

    if not host or not user:
        return  # SMTP no configurado — silencio

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP(host, port, timeout=10) as s:
            s.starttls()
            s.login(user, password)
            s.sendmail(from_addr, [to], msg.as_string())
    except Exception:
        pass  # No interrumpir flujo principal si falla email


def enviar_confirmacion_en_background(cita_id: int, db_factory) -> None:
    """Función pensada para ejecutarse en BackgroundTasks."""
    db = db_factory()
    try:
        obj = get_cita(db, cita_id)
        if not obj or not obj.email_persona:
            return
        ej = obj.ejecutivo
        tipo = obj.tipo
        html = _build_email_confirmacion(obj, ej, tipo)
        enviar_email_cita(
            to=obj.email_persona,
            subject="Confirmación de su cita",
            html=html,
        )
    finally:
        db.close()


# ── Exportar CSV ──────────────────────────────────────────────────────────────

def get_citas_csv_rows(
    db: Session,
    ejecutivo_id: Optional[int] = None,
    fecha_ini: Optional[str] = None,
    fecha_fin: Optional[str] = None,
) -> List[dict]:
    q = db.query(ResCita)
    if ejecutivo_id:
        q = q.filter(ResCita.ejecutivo_id == ejecutivo_id)
    if fecha_ini:
        inicio = datetime.strptime(fecha_ini, "%Y-%m-%d")
        q = q.filter(ResCita.start_datetime >= inicio)
    if fecha_fin:
        fin = datetime.strptime(fecha_fin, "%Y-%m-%d") + timedelta(days=1)
        q = q.filter(ResCita.start_datetime < fin)
    citas = q.order_by(ResCita.start_datetime).all()
    rows = []
    for c in citas:
        rows.append({
            "id": c.id,
            "name": c.name,
            "nombre_persona": c.nombre_persona,
            "celular_persona": c.celular_persona,
            "email_persona": c.email_persona,
            "ejecutivo": c.ejecutivo.name if c.ejecutivo else "",
            "tipo": c.tipo.name if c.tipo else "",
            "start_datetime": c.start_datetime.isoformat() if c.start_datetime else "",
            "end_datetime": c.end_datetime.isoformat() if c.end_datetime else "",
            "state": c.state,
            "source": c.source,
            "notes": c.notes or "",
            "created_at": c.created_at.isoformat() if c.created_at else "",
        })
    return rows
