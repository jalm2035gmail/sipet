from __future__ import annotations

import json
import os
from typing import Any

from celery import Celery
from redis import Redis


def _broker_url() -> str:
    return (
        os.environ.get("DASHBOARD_CELERY_BROKER_URL")
        or os.environ.get("CELERY_BROKER_URL")
        or os.environ.get("REDIS_URL")
        or "redis://localhost:6379/0"
    ).strip()


def _result_backend() -> str:
    return (
        os.environ.get("DASHBOARD_CELERY_RESULT_BACKEND")
        or os.environ.get("CELERY_RESULT_BACKEND")
        or _broker_url()
    ).strip()


def get_dashboard_redis() -> Redis:
    return Redis.from_url(
        (os.environ.get("DASHBOARD_REDIS_URL") or os.environ.get("REDIS_URL") or "redis://localhost:6379/0").strip(),
        decode_responses=True,
    )


def get_celery_app() -> Celery:
    app = Celery(
        "sipet_dashboard",
        broker=_broker_url(),
        backend=_result_backend(),
        include=["fastapi_modulo.modulos.mi_tablero.tareas.dashboard_tasks"],
    )
    app.conf.task_default_queue = (os.environ.get("DASHBOARD_CELERY_QUEUE") or "dashboard").strip() or "dashboard"
    app.conf.task_serializer = "json"
    app.conf.accept_content = ["json"]
    app.conf.result_serializer = "json"
    app.conf.timezone = "UTC"
    return app


celery_app = get_celery_app()


def _cache_key(user_id: str) -> str:
    return f"user_stats:{user_id}"


def get_cached_dashboard_stats(user_id: str) -> dict[str, Any] | None:
    try:
        payload = get_dashboard_redis().get(_cache_key(user_id))
    except Exception:
        return None
    if not payload:
        return None
    try:
        return json.loads(payload)
    except Exception:
        return None


@celery_app.task(name="mi_tablero.compute_user_dashboard_stats")
def compute_user_dashboard_stats(user_id: str, modules: list[dict]) -> dict[str, Any]:
    from fastapi_modulo.modulos.mi_tablero.servicios.analytics_service import compute_usage

    stats = compute_usage(user_id, modules)
    try:
        get_dashboard_redis().set(_cache_key(user_id), json.dumps(stats))
    except Exception:
        pass
    return stats


def enqueue_dashboard_stats(user_id: str, modules: list[dict]) -> dict[str, Any]:
    try:
        task = compute_user_dashboard_stats.delay(user_id, modules)
        return {"status": "queued", "task_id": task.id}
    except Exception:
        return {"status": "unavailable", "task_id": None}


def refresh_dashboard_cache() -> dict:
    return {"status": "ok"}
