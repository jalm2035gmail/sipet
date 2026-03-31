from __future__ import annotations

import random
import re
import string
import unicodedata
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from fastapi_modulo.modulos.referidos.modelos.db_models import (
    RefAmbassadorRequest,
    RefBrandAmbassador,
    RefConfiguracion,
    RefIncentivo,
    RefProgramAssignment,
    RefReferente,
    RefReferido,
    RefRegistro,
    RefTrackingEvent,
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
    if rule.incentive_type == "percent":
        amount = conversion_amount * Decimal(str(rule.percentage_value)) / 100
    elif rule.incentive_type == "absolute":
        amount = Decimal(str(rule.fixed_value or 0))
    else:
        amount = Decimal("0")
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
    if ref.phone:
        dup = (
            db.query(RefReferido)
            .filter(
                RefReferido.id != ref.id,
                RefReferido.phone == ref.phone,
                RefReferido.state != "rejected",
            )
            .first()
        )
        if dup:
            reasons.append(f"Duplicado por teléfono con {dup.nombre_prospecto}")
    if ref.email:
        dup = (
            db.query(RefReferido)
            .filter(
                RefReferido.id != ref.id,
                RefReferido.email == ref.email,
                RefReferido.state != "rejected",
            )
            .first()
        )
        if dup:
            reasons.append(f"Duplicado por email con {dup.nombre_prospecto}")
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
