from fastapi_modulo.modulos_sipet.modulo_base.core.task_queue import (
    DEFAULT_BROKER_URL,
    DEFAULT_QUEUE,
    DEFAULT_RESULT_BACKEND,
    ModuleTaskQueue,
    ModuleTaskRegistry,
    TASKS_ENABLED,
    build_module_task_registry,
    create_module_task_queue,
)
from fastapi_modulo.modulos_sipet.modulo_base.tareas.celery_app import celery_app

task_registry = build_module_task_registry("modulo_base")
task_queue = create_module_task_queue("modulo_base", celery_app=celery_app, registry=task_registry)

__all__ = [
    "DEFAULT_BROKER_URL",
    "DEFAULT_QUEUE",
    "DEFAULT_RESULT_BACKEND",
    "ModuleTaskQueue",
    "ModuleTaskRegistry",
    "TASKS_ENABLED",
    "build_module_task_registry",
    "celery_app",
    "create_module_task_queue",
    "task_queue",
    "task_registry",
]
