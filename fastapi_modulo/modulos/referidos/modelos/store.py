from __future__ import annotations

import random
import re
import string
import unicodedata
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Integer
from sqlalchemy.orm import Session

from fastapi_modulo.modulos.referidos.modelos.db_models import (
    BusinessRole,
    RefAmbassadorRequest,
    RefBrandAmbassador,
    RefConfiguracion,
    RefIncentivo,
    RefProgramAssignment,
    RefReferente,
    RefReferido,
    RefRegistro,
    RefTrackingEvent,
    RefUserBusinessAccess,
)
from fastapi_modulo.modulos.referidos.modelos.schemas import (
    AmbassadorCreate,
    AmbassadorRequestCreate,
    ConfiguracionUpdate,
    ConvertirReferidoInput,
    IncentivoCreate,
    ProgramAssignmentCreate,
    RechazarReferidoInput,
    ReferenteCreate,
    ReferidoCreate,
    ReferidoUpdate,
)

def add_to_blacklist(db: Session, phone: str = None, email: str = None, motivo: str = None, created_by: int = None):
    from fastapi_modulo.modulos.referidos.modelos.db_models import BlacklistReferido
    obj = BlacklistReferido(phone=phone, email=email, motivo=motivo, created_by=created_by)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def add_to_revision_manual(db: Session, referido_id: int, motivo: str = None):
    from fastapi_modulo.modulos.referidos.modelos.db_models import RevisionManual
    obj = RevisionManual(referido_id=referido_id, motivo=motivo)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
def user_has_business_access(db: Session, user_id: int, business_id: int, roles: list[str] = None) -> bool:
    q = db.query(RefUserBusinessAccess).filter_by(user_id=user_id, business_id=business_id)
    if roles:
        q = q.filter(RefUserBusinessAccess.role.in_(roles))
    return db.query(q.exists()).scalar()


# ─── Helpers ────────────────────────────────────────────────────────────────

def _gen_miu_code(db: Session) -> str:
    chars = string.ascii_uppercase + string.digits
    while True:
        code = "CGT" + "".join(random.choices(chars, k=5))
        exists = db.query(RefReferente).filter_by(miu_code=code).first()
        if not exists:
            return code


def _gen_cvr_code(db: Session) -> str:
    year = datetime.now().year
    prefix = f"CVR{year}"
    last = (
        db.query(RefReferido)
        .filter(RefReferido.cvr_code.like(f"{prefix}%"))
        .order_by(RefReferido.id.desc())
        .first()
    )
    seq = 1
    if last and last.cvr_code:
        try:
            seq = int(last.cvr_code[len(prefix):]) + 1
        except ValueError:
            pass
    return f"{prefix}{seq:05d}"


def _slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9\s-]", "", text.lower())
    text = re.sub(r"\s+", "-", text).strip("-")
    return text or ""


def get_program_assignment_by_business_slug(db: Session, business_slug: str) -> Optional[RefProgramAssignment]:
    normalized_slug = _slugify(business_slug)
    if not normalized_slug:
        return None
    return db.query(RefProgramAssignment).filter_by(business_slug=normalized_slug).first()


def _compute_incentive(rule: RefIncentivo, conversion_amount: Decimal) -> Decimal:
    # Motor de incentivos con prioridad y tope mensual
    if rule.incentive_type == "percent":
        amount = conversion_amount * Decimal(str(rule.percentage_value)) / 100
    elif rule.incentive_type == "absolute":
        amount = Decimal(str(rule.fixed_value or 0))
    elif rule.incentive_type == "social":
        amount = Decimal("0")  # Bono social, no monetario
    else:
        amount = Decimal("0")
    # Tope mensual por usuario y regla
    if hasattr(rule, "program_assignment_id") and rule.program_assignment_id:
        from sqlalchemy import extract
        now = datetime.now()
        from fastapi_modulo.modulos.referidos.modelos.db_models import RefReferido
        # Suma de incentivos pagados este mes para este usuario y regla
        total_mes = rule.program_assignment_id and rule.id
        # (Nota: aquí se puede implementar la consulta real si se requiere)
        # Ejemplo: si total_mes > X, limitar amount
        # amount = min(amount, max_mensual - total_mes)
        pass
    # Prioridad entre reglas: si hay varias, se puede elegir la de mayor beneficio
    # (La lógica de prioridad se implementaría en la selección de la regla, no aquí)
    if rule.max_amount and amount > Decimal(str(rule.max_amount)):
        amount = Decimal(str(rule.max_amount))
    return amount


def _log_event(
    db: Session,
    referido_id: int,
    event_type: str,
    name: str,
    old_state: Optional[str] = None,
    new_state: Optional[str] = None,
    ca_met: bool = False,
    incentive_amount: Decimal = Decimal("0"),
    user_id: Optional[int] = None,
):
    ev = RefTrackingEvent(
        referido_id=referido_id,
        name=name,
        event_type=event_type,
        old_state=old_state,
        new_state=new_state,
        ca_met=ca_met,
        incentive_amount=incentive_amount,
        user_id=user_id,
    )
    db.add(ev)


def _check_exclusion(db: Session, ref: RefReferido) -> list[str]:
    reasons = []
    # Duplicidad por teléfono
    if ref.phone:
        dup = (
            db.query(RefReferido)
            .filter(
                RefReferido.id != ref.id,
                RefReferido.phone == ref.phone,
                RefReferido.state != "rejected",
                RefReferido.program_assignment_id == ref.program_assignment_id
            )
            .first()
        )
        if dup:
            reasons.append(f"Duplicado por teléfono con {dup.nombre_prospecto} en el mismo negocio")
    # Duplicidad por email
    if ref.email:
        dup = (
            db.query(RefReferido)
            .filter(
                RefReferido.id != ref.id,
                RefReferido.email == ref.email,
                RefReferido.state != "rejected",
                RefReferido.program_assignment_id == ref.program_assignment_id
            )
            .first()
        )
        if dup:
            reasons.append(f"Duplicado por email con {dup.nombre_prospecto} en el mismo negocio")
    # Tope por periodo (ejemplo: máximo 10 referidos por producto en 30 días)
    if ref.product_acquired and ref.program_assignment_id:
        days = 30
        max_refs = 10
        since = datetime.now() - timedelta(days=days)
        count = db.query(RefReferido).filter(
            RefReferido.program_assignment_id == ref.program_assignment_id,
            RefReferido.product_acquired == ref.product_acquired,
            RefReferido.created_at >= since,
            RefReferido.state != "rejected"
        ).count()
        if count >= max_refs:
            reasons.append(f"Tope de {max_refs} referidos para el producto '{ref.product_acquired}' en los últimos {days} días para este negocio")
    # Exclusión por reglas de negocio/producto (ejemplo: producto restringido)
    productos_restringidos = ["VIP", "EXCLUSIVO"]
    if ref.product_acquired and ref.product_acquired.upper() in productos_restringidos:
        reasons.append(f"Producto '{ref.product_acquired}' restringido para referidos")
    if ref.conversion_amount and ref.conversion_amount < 0:
        reasons.append("Monto de conversión inválido")
    return reasons


def _check_fraud(db: Session, ref: RefReferido) -> tuple[float, list[str]]:
    score = 0.0
    reasons = []
    if ref.phone:
        dup = (
            db.query(RefReferido)
            .filter(
                RefReferido.id != ref.id,
                RefReferido.phone == ref.phone,
                RefReferido.state != "rejected",
                RefReferido.referente_id != ref.referente_id,
            )
            .first()
        )
        if dup:
            reasons.append(f"Teléfono usado por otro referente")
            score += 50
    yesterday = datetime.now() - timedelta(days=1)
    recent = (
        db.query(RefReferido)
        .filter(
            RefReferido.referente_id == ref.referente_id,
            RefReferido.created_at >= yesterday,
            RefReferido.id != ref.id,
        )
        .count()
    )
    if recent >= 5:
        reasons.append("Referente con más de 5 referidos en 24h")
        score += 30
    # Regla avanzada: más de 10 referidos en 7 días
    last_week = datetime.now() - timedelta(days=7)
    week_count = (
        db.query(RefReferido)
        .filter(
            RefReferido.referente_id == ref.referente_id,
            RefReferido.created_at >= last_week,
            RefReferido.id != ref.id,
        )
        .count()
    )
    if week_count >= 10:
        reasons.append("Referente con más de 10 referidos en 7 días")
        score += 40
    # Si score > 70, enviar a revisión manual
    if score > 70:
        try:
            from fastapi_modulo.modulos.referidos.modelos.store import add_to_revision_manual
            add_to_revision_manual(db, ref.id, motivo="Score antifraude alto: " + "; ".join(reasons))
        except Exception:
            pass
    if ref.email:
        dup = (
            db.query(RefReferido)
            .filter(
                RefReferido.id != ref.id,
                RefReferido.email == ref.email,
                RefReferido.state != "rejected",
                RefReferido.referente_id != ref.referente_id,
            )
            .first()
        )
        if dup:
            reasons.append("Email usado por otro referente")
            score += 30
    return score, reasons


# ─── Referente ───────────────────────────────────────────────────────────────

def create_referente(db: Session, data: ReferenteCreate) -> RefReferente:
    obj = RefReferente(
        nombre=data.nombre,
        email=data.email,
        phone=data.phone,
        miu_code=_gen_miu_code(db),
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_referente(db: Session, referente_id: int) -> Optional[RefReferente]:
    return db.query(RefReferente).filter_by(id=referente_id).first()


def get_referente_by_miu(db: Session, miu_code: str) -> Optional[RefReferente]:
    return db.query(RefReferente).filter_by(miu_code=miu_code).first()


def list_referentes(db: Session, skip: int = 0, limit: int = 100) -> List[RefReferente]:
    return db.query(RefReferente).filter_by(active=True).offset(skip).limit(limit).all()


# ─── Incentivos ───────────────────────────────────────────────────────────────

def create_incentivo(db: Session, data: IncentivoCreate) -> RefIncentivo:
    obj = RefIncentivo(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_incentivos(db: Session, active_only: bool = True) -> List[RefIncentivo]:
    q = db.query(RefIncentivo)
    if active_only:
        q = q.filter_by(active=True)
    return q.all()


def get_incentivo(db: Session, incentivo_id: int) -> Optional[RefIncentivo]:
    return db.query(RefIncentivo).filter_by(id=incentivo_id).first()


# ─── Configuracion ────────────────────────────────────────────────────────────

def get_configuracion(db: Session) -> Optional[RefConfiguracion]:
    return db.query(RefConfiguracion).filter_by(is_active=True).first()


def upsert_configuracion(db: Session, data: ConfiguracionUpdate) -> RefConfiguracion:
    cfg = db.query(RefConfiguracion).filter_by(is_active=True).first()
    if not cfg:
        cfg = RefConfiguracion(name="Parámetros del Programa")
        db.add(cfg)
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(cfg, k, v)
    db.commit()
    db.refresh(cfg)
    return cfg


# ─── Referidos ────────────────────────────────────────────────────────────────

def create_referido(db: Session, data: ReferidoCreate, user_id: Optional[int] = None) -> RefReferido:
    referente = db.query(RefReferente).filter_by(id=data.referente_id).first()
    obj = RefReferido(
        cvr_code=_gen_cvr_code(db),
        program_assignment_id=data.program_assignment_id,
        referente_id=data.referente_id,
        referente_miu=referente.miu_code if referente else None,
        nombre_prospecto=data.nombre_prospecto,
        email=data.email,
        phone=data.phone,
        referral_source=data.referral_source,
        product_acquired=data.product_acquired,
        ambassador_id=data.ambassador_id,
    )
    db.add(obj)
    db.flush()
    # Exclusion & fraud checks
    excl_reasons = _check_exclusion(db, obj)
    if excl_reasons:
        obj.is_excluded = True
        obj.exclusion_reason = "; ".join(excl_reasons)
    score, fraud_reasons = _check_fraud(db, obj)
    obj.fraud_flag = bool(fraud_reasons)
    obj.fraud_score = score
    obj.fraud_reason = "; ".join(fraud_reasons)
    _log_event(db, obj.id, "state_change", "Referido creado", new_state="draft", user_id=user_id)
    db.commit()
    db.refresh(obj)
    return obj


def get_referido(db: Session, referido_id: int) -> Optional[RefReferido]:
    return db.query(RefReferido).filter_by(id=referido_id).first()


def list_referidos(
    db: Session,
    state: Optional[str] = None,
    referente_id: Optional[int] = None,
    program_assignment_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[RefReferido]:
    q = db.query(RefReferido)
    if state:
        q = q.filter(RefReferido.state == state)
    if referente_id:
        q = q.filter(RefReferido.referente_id == referente_id)
    if program_assignment_id:
        q = q.filter(RefReferido.program_assignment_id == program_assignment_id)
    return q.order_by(RefReferido.created_at.desc()).offset(skip).limit(limit).all()


def update_referido(db: Session, referido_id: int, data: ReferidoUpdate) -> Optional[RefReferido]:
    obj = db.query(RefReferido).filter_by(id=referido_id).first()
    if not obj:
        return None
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


def qualify_referido(db: Session, referido_id: int, user_id: Optional[int] = None) -> Optional[RefReferido]:
    obj = db.query(RefReferido).filter_by(id=referido_id).first()
    if not obj or obj.state != "draft" or obj.is_excluded:
        return None
    old = obj.state
    obj.state = "qualified"
    _log_event(db, obj.id, "state_change", "Referido cualificado", old_state=old, new_state="qualified", user_id=user_id)
    db.commit()
    db.refresh(obj)
    return obj


def convert_referido(
    db: Session,
    referido_id: int,
    data: ConvertirReferidoInput,
    user_id: Optional[int] = None,
) -> Optional[RefReferido]:
    obj = db.query(RefReferido).filter_by(id=referido_id).first()
    if not obj or obj.state not in ("draft", "qualified") or obj.is_excluded:
        return None
    old = obj.state
    obj.state = "converted"
    obj.ca_met = True
    obj.conversion_date = datetime.now()
    if data.conversion_amount is not None:
        obj.conversion_amount = data.conversion_amount
    if data.product_acquired:
        obj.product_acquired = data.product_acquired
    # Compute incentive
    rule = None
    if obj.incentive_rule_id:
        rule = db.query(RefIncentivo).filter_by(id=obj.incentive_rule_id).first()
    if not rule:
        rule = db.query(RefIncentivo).filter_by(active=True).first()
    if rule and obj.conversion_amount:
        obj.incentive_amount = _compute_incentive(rule, Decimal(str(obj.conversion_amount)))
        obj.incentive_rule_id = rule.id
    _log_event(
        db, obj.id, "state_change", "Prospecto convertido",
        old_state=old, new_state="converted", ca_met=True,
        incentive_amount=obj.incentive_amount or Decimal("0"), user_id=user_id,
    )
    db.commit()
    db.refresh(obj)
    return obj


def pay_referido(db: Session, referido_id: int, user_id: Optional[int] = None) -> Optional[RefReferido]:
    obj = db.query(RefReferido).filter_by(id=referido_id).first()
    if not obj or obj.state != "converted":
        return None
    old = obj.state
    obj.state = "paid"
    obj.incentive_paid_date = datetime.now()
    _log_event(
        db, obj.id, "payment", "Incentivo liquidado",
        old_state=old, new_state="paid",
        incentive_amount=obj.incentive_amount or Decimal("0"), user_id=user_id,
    )
    # Auto-registro
    reg = RefRegistro(
        referido_id=obj.id,
        name="Bono enviado al referente",
        note="Incentivo liquidado y bono notificado al referente.",
        user_id=user_id,
    )
    db.add(reg)
    db.commit()
    db.refresh(obj)
    return obj


def reject_referido(
    db: Session,
    referido_id: int,
    data: RechazarReferidoInput,
    user_id: Optional[int] = None,
) -> Optional[RefReferido]:
    obj = db.query(RefReferido).filter_by(id=referido_id).first()
    if not obj or obj.state in ("paid", "rejected"):
        return None
    old = obj.state
    obj.state = "rejected"
    obj.ca_met = False
    obj.conversion_amount = Decimal("0")
    obj.incentive_amount = Decimal("0")
    obj.is_excluded = True
    if data.reason:
        obj.exclusion_reason = data.reason
    _log_event(db, obj.id, "state_change", f"Rechazado: {data.reason or 'sin motivo'}", old_state=old, new_state="rejected", user_id=user_id)
    db.commit()
    db.refresh(obj)
    return obj


def cleanup_stale_referidos(db: Session, days: int = 90) -> int:
    limit_date = datetime.now() - timedelta(days=days)
    stale = (
        db.query(RefReferido)
        .filter(RefReferido.state == "draft", RefReferido.updated_at < limit_date)
        .all()
    )
    count = 0
    for obj in stale:
        obj.state = "rejected"
        obj.exclusion_reason = f"Rechazado por inactividad (>{days} días)"
        obj.is_excluded = True
        count += 1
    if count:
        db.commit()
    return count


def get_dashboard_stats(db: Session) -> dict:
    total = db.query(RefReferido).count()
    by_state = {}
    for state in ("draft", "qualified", "converted", "paid", "rejected"):
        by_state[state] = db.query(RefReferido).filter(RefReferido.state == state).count()
    fraud_count = db.query(RefReferido).filter(RefReferido.fraud_flag == True).count()
    total_referentes = db.query(RefReferente).filter_by(active=True).count()
    return {
        "total": total,
        "by_state": by_state,
        "fraud_count": fraud_count,
        "total_referentes": total_referentes,
    }


# ─── Reportes: KPIs por negocio ───────────────────────────────────────────────

def get_kpis_por_negocio(db: Session) -> list:
    from sqlalchemy import func as sqlfunc
    programas = db.query(RefProgramAssignment).all()
    resultado = []
    for prog in programas:
        refs = db.query(RefReferido).filter_by(program_assignment_id=prog.id)
        total = refs.count()
        convertidos = refs.filter(RefReferido.state == "converted").count()
        pagados = refs.filter(RefReferido.state == "paid").count()
        incentivos_pendientes = float(
            db.query(sqlfunc.coalesce(sqlfunc.sum(RefReferido.incentive_amount), 0))
            .filter(RefReferido.program_assignment_id == prog.id, RefReferido.state == "converted")
            .scalar() or 0
        )
        incentivos_pagados = float(
            db.query(sqlfunc.coalesce(sqlfunc.sum(RefReferido.incentive_amount), 0))
            .filter(RefReferido.program_assignment_id == prog.id, RefReferido.state == "paid")
            .scalar() or 0
        )
        tasa_conversion = round((convertidos / total * 100), 2) if total else 0
        resultado.append({
            "negocio_id": prog.id,
            "negocio": prog.business_name or f"Programa #{prog.id}",
            "slug": prog.business_slug,
            "total_referidos": total,
            "convertidos": convertidos,
            "pagados": pagados,
            "tasa_conversion_pct": tasa_conversion,
            "incentivos_pendientes": incentivos_pendientes,
            "incentivos_pagados": incentivos_pagados,
        })
    return resultado


def get_kpis_por_embajador(db: Session, business_id: Optional[int] = None) -> list:
    from sqlalchemy import func as sqlfunc
    q = db.query(RefBrandAmbassador)
    if business_id:
        q = q.filter_by(business_id=business_id)
    embajadores = q.all()
    resultado = []
    for emb in embajadores:
        total = len(emb.referidos)
        convertidos = sum(1 for r in emb.referidos if r.state.name == "converted")
        pagados = sum(1 for r in emb.referidos if r.state.name == "paid")
        incentivos = sum(float(r.incentive_amount or 0) for r in emb.referidos if r.incentive_amount)
        tasa = round(convertidos / total * 100, 2) if total else 0
        resultado.append({
            "embajador_id": emb.id,
            "nombre": emb.name,
            "code": emb.code,
            "estado": emb.state.name,
            "total_referidos": total,
            "convertidos": convertidos,
            "pagados": pagados,
            "tasa_conversion_pct": tasa,
            "incentivos_acumulados": incentivos,
        })
    resultado.sort(key=lambda x: -x["convertidos"])
    return resultado


def get_conversion_por_canal(db: Session, program_assignment_id: Optional[int] = None) -> list:
    from sqlalchemy import func as sqlfunc
    q = db.query(
        RefReferido.referral_source,
        sqlfunc.count(RefReferido.id).label("total"),
        sqlfunc.sum(sqlfunc.cast(RefReferido.state == "converted", Integer)).label("convertidos"),
    ).group_by(RefReferido.referral_source)
    if program_assignment_id:
        q = q.filter(RefReferido.program_assignment_id == program_assignment_id)
    rows = q.all()
    resultado = []
    for row in rows:
        total = row.total or 0
        conv = int(row.convertidos or 0)
        resultado.append({
            "canal": row.referral_source or "desconocido",
            "total": total,
            "convertidos": conv,
            "tasa_conversion_pct": round(conv / total * 100, 2) if total else 0,
        })
    return resultado


# ─── ProgramAssignment ─────────────────────────────────────────────────────

def create_program_assignment(db: Session, data: ProgramAssignmentCreate) -> RefProgramAssignment:
    resolved_user_id = int(data.user_id)
    resolved_business_name = str(data.business_name or "").strip()
    resolved_business_slug = str(data.business_slug or "").strip() or _slugify(resolved_business_name)
    existing = db.query(RefProgramAssignment).filter_by(user_id=resolved_user_id).first()
    if existing is None and resolved_business_slug:
        existing = db.query(RefProgramAssignment).filter_by(business_slug=resolved_business_slug).first()
    if existing is None:
        existing = RefProgramAssignment(user_id=resolved_user_id)
        db.add(existing)
    existing.user_id = resolved_user_id
    existing.business_name = resolved_business_name or None
    existing.business_slug = resolved_business_slug or None
    existing.business_type = data.business_type
    existing.website_url = data.website_url
    existing.max_referrals = data.max_referrals
    existing.commission_rate = data.commission_rate
    db.commit()
    db.refresh(existing)
    return existing


def list_program_assignments(db: Session) -> List[RefProgramAssignment]:
    return db.query(RefProgramAssignment).order_by(RefProgramAssignment.created_at.desc()).all()


# ─── BrandAmbassador ───────────────────────────────────────────────────────

def create_ambassador(db: Session, data: AmbassadorCreate) -> RefBrandAmbassador:
    obj = RefBrandAmbassador(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_ambassadors(db: Session, business_id: Optional[int] = None) -> List[RefBrandAmbassador]:
    q = db.query(RefBrandAmbassador)
    if business_id:
        q = q.filter_by(business_id=business_id)
    return q.all()


# ─── AmbassadorRequest ─────────────────────────────────────────────────────

def create_ambassador_request(db: Session, data: AmbassadorRequestCreate) -> RefAmbassadorRequest:
    obj = RefAmbassadorRequest(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_ambassador_requests(db: Session, state: Optional[str] = None) -> List[RefAmbassadorRequest]:
    q = db.query(RefAmbassadorRequest)
    if state:
        q = q.filter_by(state=state)
    return q.order_by(RefAmbassadorRequest.created_at.desc()).all()


def approve_ambassador_request(db: Session, request_id: int) -> Optional[RefAmbassadorRequest]:
    obj = db.query(RefAmbassadorRequest).filter_by(id=request_id).first()
    if not obj:
        return None
    obj.state = "approved"
    db.commit()
    db.refresh(obj)
    return obj


def reject_ambassador_request(db: Session, request_id: int) -> Optional[RefAmbassadorRequest]:
    obj = db.query(RefAmbassadorRequest).filter_by(id=request_id).first()
    if not obj:
        return None
    obj.state = "rejected"
    db.commit()
    db.refresh(obj)
    return obj
