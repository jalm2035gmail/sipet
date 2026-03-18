from __future__ import annotations

import os
import secrets
from datetime import datetime, timezone
from typing import Any

from fastapi_modulo.modulos_sipet.aplicaciones.servicios.redis_service import get_task_state, store_task_state

try:
    from fastapi_modulo.modulos_sipet.aplicaciones.tareas.celery_app import celery_app
except Exception:  # pragma: no cover
    celery_app = None


TASKS_ENABLED = (os.environ.get("APPLICATIONS_CELERY_ENABLED") or "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
TASK_QUEUE = (os.environ.get("APPLICATIONS_CELERY_QUEUE") or "applications").strip() or "applications"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def queue_task(task_name: str, kwargs: dict[str, Any]) -> dict[str, Any]:
    task_id = secrets.token_hex(16)
    payload = {
        "task_id": task_id,
        "task_name": task_name,
        "status": "queued",
        "updated_at": _utc_now(),
        "result": {},
        "error": "",
    }
    store_task_state(task_name, task_id, payload)
    if TASKS_ENABLED and celery_app is not None:
        try:
            celery_app.send_task(
                f"applications.{task_name}",
                kwargs={**kwargs, "task_id": task_id},
                task_id=task_id,
                queue=TASK_QUEUE,
            )
            return payload
        except Exception as exc:
            # Celery no disponible — actualizar estado a error y ejecutar inline
            error_payload = {**payload, "status": "inline", "updated_at": _utc_now(), "error": str(exc)}
            store_task_state(task_name, task_id, error_payload)
    return {"task_id": task_id, "task_name": task_name, "status": "inline", "updated_at": _utc_now(), "result": {}, "error": ""}


def update_task_state(
    task_name: str,
    task_id: str,
    *,
    status: str,
    result: dict[str, Any] | None = None,
    error: str = "",
) -> None:
    """Actualiza el estado de una tarea en Redis.

    Debe llamarse desde el worker Celery:
      - Al iniciar la tarea:   update_task_state(name, id, status="running")
      - Al completar con éxito: update_task_state(name, id, status="success", result={...})
      - Al fallar:             update_task_state(name, id, status="error", error=str(exc))

    Si Redis no está disponible la operación se descarta silenciosamente,
    ya que store_task_state tiene el mismo comportamiento gracioso.
    """
    existing = get_task_state(task_name, task_id) or {}
    payload = {
        "task_id": str(task_id or "").strip(),
        "task_name": str(task_name or "").strip(),
        "status": str(status or "").strip(),
        "updated_at": _utc_now(),
        "result": result if result is not None else existing.get("result", {}),
        "error": str(error or "").strip(),
    }
    store_task_state(task_name, task_id, payload)


def get_async_task_state(task_name: str, task_id: str) -> dict[str, Any]:
    payload = get_task_state(task_name, task_id)
    if payload is None:
        return {
            "task_id": str(task_id or "").strip(),
            "task_name": str(task_name or "").strip(),
            "status": "unknown",
            "updated_at": "",
            "result": {},
            "error": "",
        }
    return payload


__all__ = ["TASKS_ENABLED", "get_async_task_state", "queue_task", "update_task_state"]
