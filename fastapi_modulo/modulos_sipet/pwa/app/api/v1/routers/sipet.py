from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import DBSession, get_current_active_user
from app.models.sipet import Activity, ActivityEvidence, KPI, StrategicObjective, StrategicPlan
from app.schemas.sipet import (
    ActivityCreate,
    ActivityEvidenceRead,
    ActivityRead,
    DashboardSummary,
    KPICreate,
    KPIRead,
    StrategicObjectiveCreate,
    StrategicObjectiveRead,
    StrategicPlanCreate,
    StrategicPlanRead,
)
from app.services import media_service

router = APIRouter()


@router.get('/dashboard', response_model=DashboardSummary)
def dashboard(db: Session = DBSession, current_user=Depends(get_current_active_user)):
    plans = db.query(func.count(StrategicPlan.id)).scalar() or 0
    objectives = db.query(func.count(StrategicObjective.id)).scalar() or 0
    kpis = db.query(func.count(KPI.id)).scalar() or 0
    activities = db.query(func.count(Activity.id)).scalar() or 0
    evidences = db.query(func.count(ActivityEvidence.id)).scalar() or 0
    completed_activities = db.query(func.count(Activity.id)).filter(Activity.status == 'completed').scalar() or 0
    overdue_activities = db.query(func.count(Activity.id)).filter(Activity.planned_end < date.today(), Activity.status != 'completed').scalar() or 0
    average_progress = db.query(func.avg(Activity.progress)).scalar() or 0
    planned_budget = db.query(func.coalesce(func.sum(Activity.budget_planned), 0)).scalar() or 0
    executed_budget = db.query(func.coalesce(func.sum(Activity.budget_executed), 0)).scalar() or 0
    execution_rate = round((executed_budget / planned_budget) * 100, 2) if planned_budget else 0

    return DashboardSummary(
        plans=plans, objectives=objectives, kpis=kpis, activities=activities, evidences=evidences,
        completed_activities=completed_activities, overdue_activities=overdue_activities,
        average_progress=round(float(average_progress), 2), planned_budget=float(planned_budget),
        executed_budget=float(executed_budget), execution_rate=execution_rate,
    )


@router.post('/plans', response_model=StrategicPlanRead, status_code=status.HTTP_201_CREATED)
def create_plan(body: StrategicPlanCreate, db: Session = DBSession, current_user=Depends(get_current_active_user)):
    exists = db.query(StrategicPlan).filter(StrategicPlan.code == body.code).first()
    if exists:
        raise HTTPException(status_code=400, detail='Plan code already exists')
    plan = StrategicPlan(**body.model_dump(), created_by_id=current_user.id)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.get('/plans', response_model=list[StrategicPlanRead])
def list_plans(db: Session = DBSession, current_user=Depends(get_current_active_user)):
    return db.query(StrategicPlan).order_by(StrategicPlan.id.desc()).all()


@router.post('/objectives', response_model=StrategicObjectiveRead, status_code=status.HTTP_201_CREATED)
def create_objective(body: StrategicObjectiveCreate, db: Session = DBSession, current_user=Depends(get_current_active_user)):
    plan = db.query(StrategicPlan).filter(StrategicPlan.id == body.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail='Plan not found')
    objective = StrategicObjective(**body.model_dump())
    db.add(objective)
    db.commit()
    db.refresh(objective)
    return objective


@router.get('/plans/{plan_id}/objectives', response_model=list[StrategicObjectiveRead])
def list_objectives(plan_id: int, db: Session = DBSession, current_user=Depends(get_current_active_user)):
    return db.query(StrategicObjective).filter(StrategicObjective.plan_id == plan_id).order_by(StrategicObjective.priority.asc(), StrategicObjective.id.asc()).all()


@router.post('/kpis', response_model=KPIRead, status_code=status.HTTP_201_CREATED)
def create_kpi(body: KPICreate, db: Session = DBSession, current_user=Depends(get_current_active_user)):
    objective = db.query(StrategicObjective).filter(StrategicObjective.id == body.objective_id).first()
    if not objective:
        raise HTTPException(status_code=404, detail='Objective not found')
    kpi = KPI(**body.model_dump())
    db.add(kpi)
    db.commit()
    db.refresh(kpi)
    return kpi


@router.get('/objectives/{objective_id}/kpis', response_model=list[KPIRead])
def list_kpis(objective_id: int, db: Session = DBSession, current_user=Depends(get_current_active_user)):
    return db.query(KPI).filter(KPI.objective_id == objective_id).order_by(KPI.id.asc()).all()


@router.post('/activities', response_model=ActivityRead, status_code=status.HTTP_201_CREATED)
def create_activity(body: ActivityCreate, db: Session = DBSession, current_user=Depends(get_current_active_user)):
    objective = db.query(StrategicObjective).filter(StrategicObjective.id == body.objective_id).first()
    if not objective:
        raise HTTPException(status_code=404, detail='Objective not found')
    activity = Activity(**body.model_dump())
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


@router.get('/objectives/{objective_id}/activities', response_model=list[ActivityRead])
def list_activities(objective_id: int, db: Session = DBSession, current_user=Depends(get_current_active_user)):
    return db.query(Activity).filter(Activity.objective_id == objective_id).order_by(Activity.id.desc()).all()


@router.post('/activities/{activity_id}/evidence', response_model=ActivityEvidenceRead, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    activity_id: int,
    title: str = Form(...),
    note: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail='Activity not found')

    data = await file.read()
    stored_name = f'sipet_activity_{activity_id}_{file.filename}'
    path = media_service.save_upload(data, stored_name, subfolder='sipet_evidence')
    evidence = ActivityEvidence(activity_id=activity_id, title=title, note=note, file_url=str(path).replace('media', '/media', 1))
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence


@router.get('/activities/{activity_id}/evidence', response_model=list[ActivityEvidenceRead])
def list_evidence(activity_id: int, db: Session = DBSession, current_user=Depends(get_current_active_user)):
    return db.query(ActivityEvidence).filter(ActivityEvidence.activity_id == activity_id).order_by(ActivityEvidence.id.desc()).all()
