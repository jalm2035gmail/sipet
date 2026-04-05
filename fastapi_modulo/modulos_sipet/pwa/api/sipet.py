"""
api/sipet.py — Router SIPET refactorizado.

Usa los modelos y esquemas raíz (models.sipet, schemas.sipet) con los
campos reforzados de la Fase 6.  Reemplaza app/api/v1/routers/sipet.py
progresivamente.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.deps import DBSession, get_current_active_user, require_admin
from app.services import media_service
from models.sipet import Activity, ActivityEvidence, KPI, StrategicObjective, StrategicPlan
from schemas.sipet import (
    ActivityCreate,
    ActivityEvidenceCreate,
    ActivityEvidenceRead,
    ActivityEvidenceReview,
    ActivityRead,
    DashboardSummary,
    KPICreate,
    KPIRead,
    StrategicObjectiveCreate,
    StrategicObjectiveRead,
    StrategicPlanCreate,
    StrategicPlanRead,
)

router = APIRouter()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=DashboardSummary)
def dashboard(db: Session = DBSession, current_user=Depends(get_current_active_user)):
    plans = db.query(func.count(StrategicPlan.id)).scalar() or 0
    objectives = db.query(func.count(StrategicObjective.id)).scalar() or 0
    kpis = db.query(func.count(KPI.id)).scalar() or 0
    activities = db.query(func.count(Activity.id)).scalar() or 0
    evidences = db.query(func.count(ActivityEvidence.id)).scalar() or 0
    completed = (
        db.query(func.count(Activity.id)).filter(Activity.status == "completed").scalar() or 0
    )
    overdue = (
        db.query(func.count(Activity.id))
        .filter(Activity.planned_end < date.today(), Activity.status != "completed")
        .scalar() or 0
    )
    avg_progress = db.query(func.avg(Activity.progress)).scalar() or 0
    planned_budget = db.query(func.coalesce(func.sum(Activity.budget_planned), 0)).scalar() or 0
    exec_budget = db.query(func.coalesce(func.sum(Activity.budget_executed), 0)).scalar() or 0
    exec_rate = round((exec_budget / planned_budget) * 100, 2) if planned_budget else 0

    return DashboardSummary(
        plans=plans, objectives=objectives, kpis=kpis, activities=activities, evidences=evidences,
        completed_activities=completed, overdue_activities=overdue,
        average_progress=round(float(avg_progress), 2),
        planned_budget=float(planned_budget), executed_budget=float(exec_budget),
        execution_rate=exec_rate,
    )


# ── Planes estratégicos ───────────────────────────────────────────────────────

@router.post("/plans", response_model=StrategicPlanRead, status_code=status.HTTP_201_CREATED)
def create_plan(
    body: StrategicPlanCreate,
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    if db.query(StrategicPlan).filter(StrategicPlan.code == body.code).first():
        raise HTTPException(status_code=400, detail="Código de plan ya existe")
    plan = StrategicPlan(**body.model_dump(), created_by_id=current_user.id)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.get("/plans", response_model=list[StrategicPlanRead])
def list_plans(db: Session = DBSession, current_user=Depends(get_current_active_user)):
    return db.query(StrategicPlan).order_by(StrategicPlan.id.desc()).all()


@router.get("/plans/{plan_id}", response_model=StrategicPlanRead)
def get_plan(plan_id: int, db: Session = DBSession, current_user=Depends(get_current_active_user)):
    plan = db.get(StrategicPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    return plan


# ── Objetivos estratégicos ────────────────────────────────────────────────────

@router.post("/objectives", response_model=StrategicObjectiveRead, status_code=status.HTTP_201_CREATED)
def create_objective(
    body: StrategicObjectiveCreate,
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    if not db.get(StrategicPlan, body.plan_id):
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    obj = StrategicObjective(**body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/plans/{plan_id}/objectives", response_model=list[StrategicObjectiveRead])
def list_objectives(
    plan_id: int, db: Session = DBSession, current_user=Depends(get_current_active_user)
):
    return (
        db.query(StrategicObjective)
        .filter(StrategicObjective.plan_id == plan_id)
        .order_by(StrategicObjective.priority.asc(), StrategicObjective.id.asc())
        .all()
    )


# ── KPIs ──────────────────────────────────────────────────────────────────────

@router.post("/kpis", response_model=KPIRead, status_code=status.HTTP_201_CREATED)
def create_kpi(
    body: KPICreate,
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    if not db.get(StrategicObjective, body.objective_id):
        raise HTTPException(status_code=404, detail="Objetivo no encontrado")
    kpi = KPI(**body.model_dump())
    db.add(kpi)
    db.commit()
    db.refresh(kpi)
    return kpi


@router.get("/objectives/{objective_id}/kpis", response_model=list[KPIRead])
def list_kpis(
    objective_id: int, db: Session = DBSession, current_user=Depends(get_current_active_user)
):
    return db.query(KPI).filter(KPI.objective_id == objective_id).order_by(KPI.id.asc()).all()


@router.patch("/kpis/{kpi_id}/value", response_model=KPIRead)
def update_kpi_value(
    kpi_id: int,
    value: float,
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    kpi = db.get(KPI, kpi_id)
    if not kpi:
        raise HTTPException(status_code=404, detail="KPI no encontrado")
    kpi.current_value = value
    kpi.last_updated_at = _utcnow()
    db.commit()
    db.refresh(kpi)
    return kpi


# ── Actividades ───────────────────────────────────────────────────────────────

@router.post("/activities", response_model=ActivityRead, status_code=status.HTTP_201_CREATED)
def create_activity(
    body: ActivityCreate,
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    if not db.get(StrategicObjective, body.objective_id):
        raise HTTPException(status_code=404, detail="Objetivo no encontrado")
    activity = Activity(**body.model_dump())
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


@router.get("/objectives/{objective_id}/activities", response_model=list[ActivityRead])
def list_activities(
    objective_id: int, db: Session = DBSession, current_user=Depends(get_current_active_user)
):
    return (
        db.query(Activity)
        .filter(Activity.objective_id == objective_id)
        .order_by(Activity.id.desc())
        .all()
    )


@router.patch("/activities/{activity_id}/approve", response_model=ActivityRead)
def approve_activity(
    activity_id: int,
    db: Session = DBSession,
    current_user=Depends(require_admin),
):
    activity = db.get(Activity, activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    activity.approved_by_id = current_user.id
    activity.approved_at = _utcnow()
    activity.status = "approved"
    db.commit()
    db.refresh(activity)
    return activity


# ── Evidencias ────────────────────────────────────────────────────────────────

@router.post(
    "/activities/{activity_id}/evidence",
    response_model=ActivityEvidenceRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_evidence(
    activity_id: int,
    title: str = Form(...),
    note: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    if not db.get(Activity, activity_id):
        raise HTTPException(status_code=404, detail="Actividad no encontrada")

    data = await file.read()
    stored_name = f"sipet_activity_{activity_id}_{file.filename}"
    path = media_service.save_upload(data, stored_name, subfolder="sipet_evidence")
    evidence = ActivityEvidence(
        activity_id=activity_id,
        title=title,
        note=note,
        file_url=str(path).replace("media", "/media", 1),
        uploaded_by_id=current_user.id,
        status="pending",
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence


@router.get("/activities/{activity_id}/evidence", response_model=list[ActivityEvidenceRead])
def list_evidence(
    activity_id: int, db: Session = DBSession, current_user=Depends(get_current_active_user)
):
    return (
        db.query(ActivityEvidence)
        .filter(ActivityEvidence.activity_id == activity_id)
        .order_by(ActivityEvidence.id.desc())
        .all()
    )


@router.patch("/evidence/{evidence_id}/review", response_model=ActivityEvidenceRead)
def review_evidence(
    evidence_id: int,
    body: ActivityEvidenceReview,
    db: Session = DBSession,
    current_user=Depends(require_admin),
):
    evidence = db.get(ActivityEvidence, evidence_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")
    evidence.status = body.status
    evidence.review_note = body.review_note
    evidence.reviewed_by_id = current_user.id
    evidence.reviewed_at = _utcnow()
    db.commit()
    db.refresh(evidence)
    return evidence
