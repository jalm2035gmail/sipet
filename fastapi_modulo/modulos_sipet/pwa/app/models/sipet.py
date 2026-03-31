from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class StrategicPlan(Base):
    __tablename__ = "sipet_strategic_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=False)
    organization = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    status = Column(String(30), default="draft", nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    objectives = relationship("StrategicObjective", back_populates="plan", cascade="all, delete-orphan")


class StrategicObjective(Base):
    __tablename__ = "sipet_objectives"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("sipet_strategic_plans.id"), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    axis = Column(String(120), nullable=True)
    owner_area = Column(String(120), nullable=True)
    status = Column(String(30), default="draft", nullable=False)
    priority = Column(Integer, default=3, nullable=False)
    due_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    plan = relationship("StrategicPlan", back_populates="objectives")
    kpis = relationship("KPI", back_populates="objective", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="objective", cascade="all, delete-orphan")


class KPI(Base):
    __tablename__ = "sipet_kpis"

    id = Column(Integer, primary_key=True, index=True)
    objective_id = Column(Integer, ForeignKey("sipet_objectives.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    formula = Column(Text, nullable=True)
    unit = Column(String(30), default="%", nullable=False)
    baseline = Column(Float, default=0, nullable=False)
    target = Column(Float, default=0, nullable=False)
    current_value = Column(Float, default=0, nullable=False)
    frequency = Column(String(30), default="monthly", nullable=False)
    status = Column(String(30), default="on_track", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    objective = relationship("StrategicObjective", back_populates="kpis")


class Activity(Base):
    __tablename__ = "sipet_activities"

    id = Column(Integer, primary_key=True, index=True)
    objective_id = Column(Integer, ForeignKey("sipet_objectives.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    responsible = Column(String(120), nullable=True)
    planned_start = Column(Date, nullable=True)
    planned_end = Column(Date, nullable=True)
    progress = Column(Integer, default=0, nullable=False)
    budget_planned = Column(Float, default=0, nullable=False)
    budget_executed = Column(Float, default=0, nullable=False)
    status = Column(String(30), default="pending", nullable=False)
    is_recurring = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    objective = relationship("StrategicObjective", back_populates="activities")
    evidences = relationship("ActivityEvidence", back_populates="activity", cascade="all, delete-orphan")


class ActivityEvidence(Base):
    __tablename__ = "sipet_activity_evidences"

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("sipet_activities.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=True)
    note = Column(Text, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), default=utcnow)

    activity = relationship("Activity", back_populates="evidences")
