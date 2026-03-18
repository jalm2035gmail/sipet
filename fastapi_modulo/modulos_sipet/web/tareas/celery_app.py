from __future__ import annotations

import os

from celery import Celery
from celery.schedules import crontab


def _broker_url() -> str:
    return (
        os.environ.get("WEB_CELERY_BROKER_URL")
        or os.environ.get("CELERY_BROKER_URL")
        or os.environ.get("REDIS_URL")
        or "redis://localhost:6379/0"
    ).strip()


def _result_backend() -> str:
    return (
        os.environ.get("WEB_CELERY_RESULT_BACKEND")
        or os.environ.get("CELERY_RESULT_BACKEND")
        or _broker_url()
    ).strip()


def get_celery_app() -> Celery:
    app = Celery(
        "sipet_web_security",
        broker=_broker_url(),
        backend=_result_backend(),
        include=[
            "fastapi_modulo.modulos_sipet.web.tareas.cleanup_tasks",
            "fastapi_modulo.modulos_sipet.web.tareas.security_tasks",
            "fastapi_modulo.modulos_sipet.web.tareas.audit_tasks",
        ],
    )

    # ── Configuración base ────────────────────────────────────────────────────
    app.conf.task_default_queue = (os.environ.get("WEB_CELERY_QUEUE") or "web_security").strip() or "web_security"
    app.conf.task_serializer = "json"
    app.conf.accept_content = ["json"]
    app.conf.result_serializer = "json"
    app.conf.timezone = "UTC"
    app.conf.enable_utc = True

    # ── Reintentos globales por defecto ───────────────────────────────────────
    # Cada tarea puede sobreescribir estos valores con sus propios decoradores.
    app.conf.task_acks_late = True          # ACK solo después de ejecutar exitosamente
    app.conf.task_reject_on_worker_lost = True  # Reencola si el worker muere a mitad

    # ── Beat schedule — tareas periódicas ────────────────────────────────────
    # Requiere correr: celery -A <module>.celery_app beat --loglevel=info
    app.conf.beat_schedule = {

        # Limpieza de sesiones expiradas — cada hora
        "cleanup-expired-sessions-hourly": {
            "task": "web.cleanup_expired_sessions",
            "schedule": 3600,
            "options": {"queue": app.conf.task_default_queue},
        },

        # Limpieza de challenges MFA expirados — cada hora
        "cleanup-expired-mfa-challenges-hourly": {
            "task": "web.cleanup_expired_mfa_challenges",
            "schedule": 3600,
            "options": {"queue": app.conf.task_default_queue},
        },

        # Detección de patrones sospechosos — cada 30 minutos
        "detect-suspicious-login-patterns": {
            "task": "web.detect_suspicious_login_patterns",
            "schedule": 1800,
            "options": {"queue": app.conf.task_default_queue},
        },

        # Resumen de sesiones activas — cada hora
        "summarize-active-sessions-hourly": {
            "task": "web.summarize_active_sessions",
            "schedule": 3600,
            "options": {"queue": app.conf.task_default_queue},
        },

        # Reentrenamiento del modelo ML — cada día a las 02:00 UTC
        "train-access-risk-model-daily": {
            "task": "web.train_backend_access_risk_model",
            "schedule": crontab(hour=2, minute=0),
            "kwargs": {"hours": 24 * 30},
            "options": {"queue": app.conf.task_default_queue},
        },

        # Reporte de acceso — cada día a las 06:00 UTC
        "build-access-report-daily": {
            "task": "web.build_access_report",
            "schedule": crontab(hour=6, minute=0),
            "options": {"queue": app.conf.task_default_queue},
        },

        # Snapshot de cumplimiento — cada día a las 06:05 UTC
        "build-security-compliance-snapshot-daily": {
            "task": "web.build_security_compliance_snapshot",
            "schedule": crontab(hour=6, minute=5),
            "kwargs": {"hours": 24},
            "options": {"queue": app.conf.task_default_queue},
        },
    }

    return app


celery_app = get_celery_app()
