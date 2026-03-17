from __future__ import annotations

import os

from celery import Celery


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
    app.conf.task_default_queue = (os.environ.get("WEB_CELERY_QUEUE") or "web_security").strip() or "web_security"
    app.conf.task_serializer = "json"
    app.conf.accept_content = ["json"]
    app.conf.result_serializer = "json"
    app.conf.timezone = "UTC"
    return app


celery_app = get_celery_app()
