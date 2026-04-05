from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


# ── Plan estratégico ──────────────────────────────────────────────────────────

class StrategicPlanCreate(BaseModel):
    name: str
    code: str
    organization: str
    description: Optional[str] = None
    period_start: date
    period_end: date
    status: str = "draft"


class StrategicPlanRead(StrategicPlanCreate):
    id: int
    created_by_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Objetivo estratégico ──────────────────────────────────────────────────────

class StrategicObjectiveCreate(BaseModel):
    plan_id: int
    code: str
    title: str
    description: Optional[str] = None
    axis: Optional[str] = None
    owner_area: Optional[str] = None
    priority: int = Field(default=3, ge=1, le=5)
    due_date: Optional[date] = None
    status: str = "draft"


class StrategicObjectiveRead(StrategicObjectiveCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── KPI ───────────────────────────────────────────────────────────────────────

class KPICreate(BaseModel):
    objective_id: int
    name: str
    formula: Optional[str] = None
    unit: str = "%"
    baseline: float = 0.0
    target: float = 0.0
    current_value: float = 0.0
    frequency: str = "monthly"
    status: str = "on_track"
    responsible_user_id: Optional[int] = None


class KPIRead(KPICreate):
    id: int
    last_updated_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Actividad ─────────────────────────────────────────────────────────────────

class ActivityCreate(BaseModel):
    objective_id: int
    name: str
    description: Optional[str] = None
    responsible: Optional[str] = None
    responsible_user_id: Optional[int] = None
    area: Optional[str] = None
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    progress: int = Field(default=0, ge=0, le=100)
    budget_planned: float = 0.0
    budget_executed: float = 0.0
    status: str = "pending"
    is_recurring: bool = False


class ActivityRead(ActivityCreate):
    id: int
    approved_by_id: Optional[int] = None
    approved_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Evidencia de actividad ────────────────────────────────────────────────────

EvidenceStatus = Literal["pending", "approved", "rejected"]


class ActivityEvidenceCreate(BaseModel):
    activity_id: Optional[int] = None
    title: str
    note: Optional[str] = None
    ref_type: Optional[str] = None   # "delivery" | "activity" | …
    ref_id: Optional[int] = None


class ActivityEvidenceRead(ActivityEvidenceCreate):
    id: int
    file_url: Optional[str] = None
    uploaded_by_id: Optional[int] = None
    status: EvidenceStatus = "pending"
    reviewed_by_id: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    review_note: Optional[str] = None
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class ActivityEvidenceReview(BaseModel):
    status: EvidenceStatus
    review_note: Optional[str] = None


# ── Dashboard ─────────────────────────────────────────────────────────────────

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
