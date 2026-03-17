from __future__ import annotations

from typing import Any

from fastapi_modulo.modulos_sipet.modulo_base.core.task_queue import DEFAULT_BROKER_URL, DEFAULT_RESULT_BACKEND

try:
    from celery import Celery
except Exception:  # pragma: no cover
    Celery = None  # type: ignore[assignment]


def get_celery_app() -> Any:
    if Celery is None:
        return None
    app = Celery(
        "modulo_base",
        broker=DEFAULT_BROKER_URL,
        backend=DEFAULT_RESULT_BACKEND,
        include=[
            "fastapi_modulo.modulos_sipet.modulo_base.tareas.sync_tasks",
            "fastapi_modulo.modulos_sipet.modulo_base.tareas.report_tasks",
        ],
    )
    app.conf.task_default_queue = "modulo_base"
    app.conf.task_track_started = True
    app.conf.task_serializer = "json"
    app.conf.accept_content = ["json"]
    app.conf.result_serializer = "json"
    return app


celery_app = get_celery_app()

__all__ = ["celery_app", "get_celery_app"]
