from __future__ import annotations

import os

from celery import Celery


def _broker_url() -> str:
    return (
        os.environ.get("APPLICATIONS_CELERY_BROKER_URL")
        or os.environ.get("CELERY_BROKER_URL")
        or os.environ.get("REDIS_URL")
        or "redis://localhost:6379/0"
    ).strip()


def _result_backend() -> str:
    return (
        os.environ.get("APPLICATIONS_CELERY_RESULT_BACKEND")
        or os.environ.get("CELERY_RESULT_BACKEND")
        or _broker_url()
    ).strip()


def get_celery_app() -> Celery:
    app = Celery(
        "sipet_applications",
        broker=_broker_url(),
        backend=_result_backend(),
        include=["fastapi_modulo.modulos.aplicaciones.tareas.app_tasks"],
    )
    app.conf.task_default_queue = (os.environ.get("APPLICATIONS_CELERY_QUEUE") or "applications").strip() or "applications"
    app.conf.task_serializer = "json"
    app.conf.accept_content = ["json"]
    app.conf.result_serializer = "json"
    app.conf.timezone = "UTC"
    return app


celery_app = get_celery_app()


__all__ = ["celery_app", "get_celery_app"]
