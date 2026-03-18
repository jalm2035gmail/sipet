from __future__ import annotations

import logging

from celery.exceptions import MaxRetriesExceededError

from fastapi_modulo.modulos_sipet.web.repositorios.security_maintenance_repository import (
    build_access_risk_report,
    detect_suspicious_login_patterns,
    summarize_active_sessions,
    train_backend_access_risk_model,
)
from fastapi_modulo.modulos_sipet.web.tareas.celery_app import celery_app

logger = logging.getLogger(__name__)

# ── Configuración de reintentos ───────────────────────────────────────────────
# El entrenamiento ML usa reintentos más conservadores porque es una operación
# larga y costosa en DB. Las tareas de detección/reporte son más agresivas.
_RETRY_LIGHT = {
    "autoretry_for": (Exception,),
    "max_retries": 3,
    "default_retry_delay": 30,
    "retry_backoff": True,
    "retry_backoff_max": 300,
    "retry_jitter": True,
}

_RETRY_HEAVY = {
    "autoretry_for": (Exception,),
    "max_retries": 2,           # menos reintentos — operación costosa
    "default_retry_delay": 60,  # espera inicial más larga
    "retry_backoff": True,
    "retry_backoff_max": 600,   # hasta 10 minutos entre reintentos
    "retry_jitter": True,
}


@celery_app.task(name="web.detect_suspicious_login_patterns", **_RETRY_LIGHT)
def detect_suspicious_login_patterns_task() -> dict:
    try:
        return {"status": "ok", "suspicious_events": detect_suspicious_login_patterns()}
    except MaxRetriesExceededError:
        logger.error("detect_suspicious_login_patterns_task: máximo de reintentos alcanzado")
        return {"status": "error", "suspicious_events": []}


@celery_app.task(name="web.summarize_active_sessions", **_RETRY_LIGHT)
def summarize_active_sessions_task() -> dict:
    try:
        return {"status": "ok", "summary": summarize_active_sessions()}
    except MaxRetriesExceededError:
        logger.error("summarize_active_sessions_task: máximo de reintentos alcanzado")
        return {"status": "error", "summary": None}


@celery_app.task(name="web.train_backend_access_risk_model", **_RETRY_HEAVY)
def train_backend_access_risk_model_task(hours: int = 24 * 30) -> dict:
    """
    Reentrena el modelo RandomForest con los eventos de los últimos `hours`.
    Usa _RETRY_HEAVY: máximo 2 reintentos con espera mayor porque la operación
    involucra consultas pesadas a DB, construcción de features y escritura
    del modelo a disco con joblib.
    """
    try:
        result = train_backend_access_risk_model(hours)
        logger.info(
            "train_backend_access_risk_model_task: status=%s samples=%s cv_accuracy=%s",
            result.get("status"),
            result.get("samples"),
            result.get("cv_accuracy"),
        )
        return {"status": "ok", "training": result}
    except MaxRetriesExceededError:
        logger.error(
            "train_backend_access_risk_model_task: máximo de reintentos alcanzado, hours=%s", hours
        )
        return {"status": "error", "training": None}


@celery_app.task(name="web.build_access_risk_report", **_RETRY_LIGHT)
def build_access_risk_report_task(hours: int = 24, limit: int = 100) -> dict:
    try:
        return {"status": "ok", "report": build_access_risk_report(hours, limit)}
    except MaxRetriesExceededError:
        logger.error(
            "build_access_risk_report_task: máximo de reintentos alcanzado, hours=%s limit=%s",
            hours, limit,
        )
        return {"status": "error", "report": None}
    