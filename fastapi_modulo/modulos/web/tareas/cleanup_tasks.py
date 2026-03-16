from __future__ import annotations

from fastapi_modulo.modulos.web.repositorios.security_maintenance_repository import (
    cleanup_expired_mfa_challenges,
    cleanup_expired_sessions,
)
from fastapi_modulo.modulos.web.tareas.celery_app import celery_app


@celery_app.task(name="web.cleanup_expired_sessions")
def cleanup_expired_sessions_task() -> dict:
    deleted = cleanup_expired_sessions()
    return {"status": "ok", "deleted_sessions": deleted}


@celery_app.task(name="web.cleanup_expired_mfa_challenges")
def cleanup_expired_mfa_challenges_task() -> dict:
    deleted = cleanup_expired_mfa_challenges()
    return {"status": "ok", "deleted_challenges": deleted}
