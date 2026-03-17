from __future__ import annotations

from fastapi_modulo.modulos_sipet.modulo_base.core.task_queue import build_module_task_registry, create_module_task_queue
from fastapi_modulo.modulos_sipet.modulo_base.tareas.celery_app import celery_app

registry = build_module_task_registry("modulo_base")
registry.register("report_export", queue="modulo_base_reports")
task_queue = create_module_task_queue("modulo_base", celery_app=celery_app, registry=registry)


if celery_app is not None:
    @celery_app.task(name="modulo_base.report_export")
    def report_export_task(task_id: str = "", **kwargs: object) -> dict[str, object]:
        return task_queue.report_task_state(
            "report_export",
            task_id,
            status="completed",
            result={"kind": "report", "payload": kwargs},
        )


__all__ = ["registry", "task_queue"]
