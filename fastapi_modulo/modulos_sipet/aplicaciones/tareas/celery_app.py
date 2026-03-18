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


def _task_queue() -> str:
    return (os.environ.get("APPLICATIONS_CELERY_QUEUE") or "applications").strip() or "applications"


def get_celery_app() -> Celery:
    app = Celery(
        "sipet_applications",
        broker=_broker_url(),
        backend=_result_backend(),
        include=["fastapi_modulo.modulos_sipet.aplicaciones.tareas.app_tasks"],
    )
    queue = _task_queue()
    app.conf.task_default_queue = queue
    app.conf.task_serializer = "json"
    app.conf.accept_content = ["json"]
    app.conf.result_serializer = "json"
    app.conf.timezone = "UTC"
    app.conf.enable_utc = True

    # Evita que tareas queden en estado PENDING indefinidamente si el worker muere
    app.conf.task_acks_late = True
    app.conf.task_reject_on_worker_lost = True

    # Visibilidad de resultados en Redis: 24 horas
    app.conf.result_expires = 86400

    # Reintentos de conexión al broker al arrancar (no falla si Redis tarda en levantar)
    app.conf.broker_connection_retry_on_startup = True

    return app


celery_app = get_celery_app()


__all__ = ["celery_app", "get_celery_app"]
