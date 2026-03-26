from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi_modulo.modulos.reservaciones.modelos.db_models import ResCita, ResEjecutivo, ResTipoCita
from fastapi_modulo.modulos.reservaciones.modelos.schemas import (
    CitaCreate, CitaUpdate, EjecutivoCreate, EjecutivoUpdate, TipoCitaCreate
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


def create_cita(db: Session, data: CitaCreate) -> ResCita:
    obj = ResCita(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_cita_state(db: Session, cita_id: int, state: str) -> Optional[ResCita]:
    obj = get_cita(db, cita_id)
    if not obj:
        return None
    obj.state = state
    db.commit()
    db.refresh(obj)
    return obj


# ── Stats ────────────────────────────────────────────────────────────────────

def get_dashboard_stats(db: Session) -> dict:
    total = db.query(ResCita).count()
    by_state = {}
    for state in ("draft", "confirmed", "in_progress", "completed", "cancelled"):
        by_state[state] = db.query(ResCita).filter(ResCita.state == state).count()
    ejecutivos = db.query(ResEjecutivo).filter(ResEjecutivo.active == True).count()
    return {"total": total, "by_state": by_state, "ejecutivos": ejecutivos}


# ── Slots disponibles ────────────────────────────────────────────────────────

def _float_to_hhmm(f: float) -> str:
    h = int(f)
    m = int(round((f - h) * 60))
    return f"{h:02d}:{m:02d}"


DESCANSO_MAP = {
    0: ("descanso_lunes", "hora_inicial_lunes", "hora_final_lunes"),
    1: ("descanso_martes", "hora_inicial_martes", "hora_final_martes"),
    2: ("descanso_miercoles", "hora_inicial_miercoles", "hora_final_miercoles"),
    3: ("descanso_jueves", "hora_inicial_jueves", "hora_final_jueves"),
    4: ("descanso_viernes", "hora_inicial_viernes", "hora_final_viernes"),
    5: ("descanso_sabado", "hora_inicial_sabado", "hora_final_sabado"),
    6: ("descanso_domingo", "hora_inicial_domingo", "hora_final_domingo"),
}


def get_slots_for_day(db: Session, ejecutivo_id: int, fecha_str: str) -> List[dict]:
    ejecutivo = get_ejecutivo(db, ejecutivo_id)
    if not ejecutivo:
        return []

    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except ValueError:
        return []

    dow = fecha.weekday()  # 0=Monday
    descanso_field, hora_ini_field, hora_fin_field = DESCANSO_MAP[dow]

    if getattr(ejecutivo, descanso_field, True):
        return []

    hora_ini = getattr(ejecutivo, hora_ini_field, 9.0) or 9.0
    hora_fin = getattr(ejecutivo, hora_fin_field, 17.0) or 17.0
    bloque_min = (ejecutivo.tiempo_promedio_cita or 30) + (ejecutivo.tiempo_descanso_sesiones or 0)

    # Citas ya existentes ese día para ese ejecutivo
    inicio_dia = datetime.combine(fecha, datetime.min.time())
    fin_dia = inicio_dia + timedelta(days=1)
    citas_dia = db.query(ResCita).filter(
        ResCita.ejecutivo_id == ejecutivo_id,
        ResCita.state.notin_(["cancelled"]),
        ResCita.start_datetime >= inicio_dia,
        ResCita.start_datetime < fin_dia,
    ).all()
    ocupadas = {c.start_datetime.strftime("%H:%M") for c in citas_dia}

    slots = []
    current_float = hora_ini
    while current_float + (bloque_min / 60.0) <= hora_fin + 0.001:
        hora_str = _float_to_hhmm(current_float)
        dt_str = f"{fecha_str}T{hora_str}:00"
        slots.append({
            "datetime_str": dt_str,
            "hora": hora_str,
            "disponible": hora_str not in ocupadas,
        })
        current_float += bloque_min / 60.0

    return slots
