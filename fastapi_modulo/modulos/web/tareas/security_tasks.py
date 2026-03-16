from __future__ import annotations

from fastapi_modulo.modulos.web.repositorios.security_maintenance_repository import (
    build_access_risk_report,
    detect_suspicious_login_patterns,
    summarize_active_sessions,
    train_backend_access_risk_model,
)
from fastapi_modulo.modulos.web.tareas.celery_app import celery_app


@celery_app.task(name="web.detect_suspicious_login_patterns")
def detect_suspicious_login_patterns_task() -> dict:
    return {"status": "ok", "suspicious_events": detect_suspicious_login_patterns()}


@celery_app.task(name="web.summarize_active_sessions")
def summarize_active_sessions_task() -> dict:
    return {"status": "ok", "summary": summarize_active_sessions()}


@celery_app.task(name="web.train_backend_access_risk_model")
def train_backend_access_risk_model_task(hours: int = 24 * 30) -> dict:
    return {"status": "ok", "training": train_backend_access_risk_model(hours)}


@celery_app.task(name="web.build_access_risk_report")
def build_access_risk_report_task(hours: int = 24, limit: int = 100) -> dict:
    return {"status": "ok", "report": build_access_risk_report(hours, limit)}
