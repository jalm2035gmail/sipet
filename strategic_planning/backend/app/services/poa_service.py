from datetime import date

from sqlalchemy.orm import Session

from app.models.operational import POA, Activity, DepartmentObjective
from app.models.strategic.plan import StrategicPlan
from app.schemas.operational import (
    ActivityCreate,
    ActivityResponse,
    DepartmentObjectiveCreate,
    DepartmentObjectiveResponse,
)
from app.services.poa_generator import POAGenerator
from app.crud.operational.poa import poa_crud
from app.api.deps import get_db
from fastapi import Depends


class POAService:
    def __init__(self, db: Session):
        self.db = db

    async def create_activity(self, poa_id: int, activity: ActivityCreate) -> ActivityResponse:
        poa = self.db.query(POA).get(poa_id)
        if not poa:
            raise ValueError("POA no encontrado")
        activity_obj = Activity(
            poa_id=poa_id,
            department_id=activity.department_id,
            strategic_objective_id=activity.strategic_objective_id,
            code=activity.code,
            name=activity.name,
            description=activity.description,
            start_date=activity.start_date,
            end_date=activity.end_date,
            budget=activity.budget,
        )
        self.db.add(activity_obj)
        self.db.commit()
        self.db.refresh(activity_obj)
        return ActivityResponse.from_orm(activity_obj)

    async def create_department_objective(
        self, poa_id: int, objective: DepartmentObjectiveCreate
    ) -> DepartmentObjectiveResponse:
        poa = self.db.query(POA).get(poa_id)
        if not poa:
            raise ValueError("POA no encontrado")
        dept_obj = DepartmentObjective(
            poa_id=poa_id,
            department_id=objective.department_id,
            strategic_objective_id=objective.strategic_objective_id,
            name=objective.name,
            description=objective.description,
            budget=objective.budget,
            start_date=objective.start_date,
            end_date=objective.end_date,
        )
        self.db.add(dept_obj)
        self.db.commit()
        self.db.refresh(dept_obj)
        return DepartmentObjectiveResponse.from_orm(dept_obj)

    async def get_gantt_data(self, poa_id: int) -> dict:
        activities = (
            self.db.query(Activity)
            .filter(Activity.poa_id == poa_id)
            .order_by(Activity.start_date)
            .all()
        )
        return [
            {
                "id": act.id,
                "name": act.name,
                "start": act.start_date,
                "end": act.end_date,
                "status": act.status,
            }
            for act in activities
        ]

    async def update_progress(self, activity_id: int, progress: float) -> dict:
        activity = self.db.query(Activity).get(activity_id)
        if not activity:
            raise ValueError("Actividad no encontrada")
        activity.progress = max(0.0, min(100.0, progress))
        self.db.add(activity)
        self.db.commit()
        return {"id": activity.id, "progress": activity.progress}

    def generate_poa_from_plan(self, strategic_plan: StrategicPlan, year: int) -> POA:
        if strategic_plan.start_date and strategic_plan.end_date:
            start_year = strategic_plan.start_date.year
            end_year = strategic_plan.end_date.year
            if year < start_year or year > end_year:
                raise ValueError("El año fiscal debe estar dentro del periodo del plan")
        generator = POAGenerator()
        poa = generator.generate_from_strategic_plan(strategic_plan, year)
        self.db.add(poa)
        self.db.commit()
        self.db.refresh(poa)
        return poa


def get_poa_service(db: Session = Depends(get_db)) -> POAService:
    return POAService(db)
