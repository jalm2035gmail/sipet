from __future__ import annotations

import os
from typing import Any, Dict, Optional

import redis as redis_lib
from celery import Celery


def _broker_url() -> str:
    return (
        os.environ.get("ENCUESTAS_CELERY_BROKER_URL")
        or os.environ.get("CELERY_BROKER_URL")
        or os.environ.get("REDIS_URL")
        or "redis://localhost:6379/0"
    ).strip()


def _result_backend() -> str:
    return (
        os.environ.get("ENCUESTAS_CELERY_RESULT_BACKEND")
        or os.environ.get("CELERY_RESULT_BACKEND")
        or _broker_url()
    ).strip()


def get_celery_app() -> Celery:
    app = Celery(
        "sipet_encuestas",
        broker=_broker_url(),
        backend=_result_backend(),
        include=["fastapi_modulo.modulos.encuestas.modelos.encuestas_tasks"],
    )
    app.conf.task_default_queue = (os.environ.get("ENCUESTAS_CELERY_QUEUE") or "encuestas_automation").strip() or "encuestas_automation"
    app.conf.task_serializer = "json"
    app.conf.accept_content = ["json"]
    app.conf.result_serializer = "json"
    app.conf.timezone = "UTC"
    return app


celery_app = get_celery_app()

# TTL en segundos para archivos de exportación almacenados en Redis
_EXPORT_TTL = int(os.environ.get("ENCUESTAS_EXPORT_TTL", "300"))


def _redis_client() -> redis_lib.Redis:
    return redis_lib.from_url(_broker_url(), decode_responses=False)


def get_export_result(job_key: str) -> Optional[bytes]:
    """Recupera el contenido de un export desde Redis. Retorna None si expiró o no existe."""
    return _redis_client().get(job_key)


def store_export_result(job_key: str, content: bytes) -> None:
    """Almacena el contenido de un export en Redis con TTL."""
    _redis_client().setex(job_key, _EXPORT_TTL, content)


@celery_app.task(name="encuestas.run_automation_jobs")
def run_automation_jobs_task(tenant_id: str, instance_id: Optional[int] = None) -> Dict[str, Any]:
    from fastapi_modulo.modulos.encuestas.modelos.encuestas_automation import run_automation_jobs

    return run_automation_jobs(tenant_id, instance_id=instance_id)


@celery_app.task(name="encuestas.dispatch_backendhook")
def dispatch_backendhook_task(
    tenant_id: str,
    instance_id: int,
    event_name: str,
    payload: Dict[str, Any],
    assignment_id: Optional[int] = None,
) -> Dict[str, Any]:
    from fastapi_modulo.modulos.encuestas.modelos.encuestas_automation import dispatch_backendhook_event

    return dispatch_backendhook_event(
        tenant_id=tenant_id,
        instance_id=instance_id,
        event_name=event_name,
        payload=payload,
        assignment_id=assignment_id,
    )


@celery_app.task(name="encuestas.export_csv")
def export_csv_task(instance_id: int, tenant_id: str, filters: Dict[str, str], job_key: str) -> str:
    from fastapi_modulo.modulos.encuestas.modelos.encuestas_analytics import get_results_dashboard
    from fastapi_modulo.modulos.encuestas.modelos.encuestas_exports import export_results_csv

    dashboard = get_results_dashboard(instance_id, tenant_id, filters=filters or None)
    content = export_results_csv(instance_id, tenant_id, dashboard=dashboard)
    store_export_result(job_key, content if isinstance(content, bytes) else content.encode("utf-8"))
    return job_key


@celery_app.task(name="encuestas.export_excel")
def export_excel_task(instance_id: int, tenant_id: str, filters: Dict[str, str], job_key: str) -> str:
    from fastapi_modulo.modulos.encuestas.modelos.encuestas_analytics import get_results_dashboard
    from fastapi_modulo.modulos.encuestas.modelos.encuestas_exports import export_results_excel

    dashboard = get_results_dashboard(instance_id, tenant_id, filters=filters or None)
    content = export_results_excel(instance_id, tenant_id, dashboard=dashboard)
    store_export_result(job_key, content)
    return job_key


@celery_app.task(name="encuestas.export_pdf")
def export_pdf_task(instance_id: int, tenant_id: str, filters: Dict[str, str], job_key: str) -> str:
    from fastapi_modulo.modulos.encuestas.modelos.encuestas_analytics import get_results_dashboard
    from fastapi_modulo.modulos.encuestas.modelos.encuestas_exports import export_results_pdf

    dashboard = get_results_dashboard(instance_id, tenant_id, filters=filters or None)
    content = export_results_pdf(instance_id, tenant_id, dashboard=dashboard)
    store_export_result(job_key, content)
    return job_key
