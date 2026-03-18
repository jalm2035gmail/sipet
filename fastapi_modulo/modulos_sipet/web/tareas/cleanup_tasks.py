from __future__ import annotations

import logging

from celery.exceptions import MaxRetriesExceededError

from fastapi_modulo.modulos_sipet.web.repositorios.security_maintenance_repository import (
    cleanup_expired_mfa_challenges,
    cleanup_expired_sessions,
)
from fastapi_modulo.modulos_sipet.web.tareas.celery_app import celery_app

logger = logging.getLogger(__name__)

_RETRY_KWARGS = {
    "autoretry_for": (Exception,),
    "max_retries": 3,
    "default_retry_delay": 30,
    "retry_backoff": True,
    "retry_backoff_max": 300,
    "retry_jitter": True,
}


@celery_app.task(name="web.cleanup_expired_sessions", **_RETRY_KWARGS)
def cleanup_expired_sessions_task() -> dict:
    try:
        deleted = cleanup_expired_sessions()
        logger.info("cleanup_expired_sessions_task: deleted=%s", deleted)
        return {"status": "ok", "deleted_sessions": deleted}
    except MaxRetriesExceededError:
        logger.error("cleanup_expired_sessions_task: máximo de reintentos alcanzado")
        return {"status": "error", "deleted_sessions": 0}


@celery_app.task(name="web.cleanup_expired_mfa_challenges", **_RETRY_KWARGS)
def cleanup_expired_mfa_challenges_task() -> dict:
    try:
        deleted = cleanup_expired_mfa_challenges()
        logger.info("cleanup_expired_mfa_challenges_task: deleted=%s", deleted)
        return {"status": "ok", "deleted_challenges": deleted}
    except MaxRetriesExceededError:
        logger.error("cleanup_expired_mfa_challenges_task: máximo de reintentos alcanzado")
        return {"status": "error", "deleted_challenges": 0}
    