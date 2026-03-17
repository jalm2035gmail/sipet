from fastapi_modulo.modulos_sipet.modulo_base.tareas.celery_app import celery_app, get_celery_app
from fastapi_modulo.modulos_sipet.modulo_base.tareas.report_tasks import registry as report_registry, task_queue as report_task_queue
from fastapi_modulo.modulos_sipet.modulo_base.tareas.sync_tasks import registry as sync_registry, task_queue as sync_task_queue

__all__ = [
    "celery_app",
    "get_celery_app",
    "report_registry",
    "report_task_queue",
    "sync_registry",
    "sync_task_queue",
]
