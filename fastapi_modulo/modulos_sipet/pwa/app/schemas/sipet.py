from datetime import date, datetime

from pydantic import BaseModel, Field


class StrategicPlanCreate(BaseModel):
    name: str
    code: str
    organization: str
    description: str | None = None
    period_start: date
    period_end: date
    status: str = "draft"


class StrategicPlanRead(StrategicPlanCreate):
    id: int
    created_by_id: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class StrategicObjectiveCreate(BaseModel):
    plan_id: int
    code: str
    title: str
    description: str | None = None
    axis: str | None = None
    owner_area: str | None = None
    priority: int = Field(default=3, ge=1, le=5)
    due_date: date | None = None
    status: str = "draft"


class StrategicObjectiveRead(StrategicObjectiveCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class KPICreate(BaseModel):
    objective_id: int
    name: str
    formula: str | None = None
    unit: str = "%"
    baseline: float = 0
    target: float = 0
    current_value: float = 0
    frequency: str = "monthly"
    status: str = "on_track"


class KPIRead(KPICreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ActivityCreate(BaseModel):
    objective_id: int
    name: str
    description: str | None = None
    responsible: str | None = None
    planned_start: date | None = None
    planned_end: date | None = None
    progress: int = Field(default=0, ge=0, le=100)
    budget_planned: float = 0
    budget_executed: float = 0
    status: str = "pending"
    is_recurring: bool = False


class ActivityRead(ActivityCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ActivityEvidenceCreate(BaseModel):
    activity_id: int
    title: str
    note: str | None = None


class ActivityEvidenceRead(ActivityEvidenceCreate):
    id: int
    file_url: str | None = None
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class DashboardSummary(BaseModel):
    plans: int
    objectives: int
    kpis: int
    activities: int
    evidences: int
    completed_activities: int
    overdue_activities: int
    average_progress: float
    planned_budget: float
    executed_budget: float
    execution_rate: float
