from __future__ import annotations

import os
import secrets
from datetime import datetime, timezone
from typing import Any

from fastapi_modulo.modulos_sipet.modulo_base.core.cache_service import get_task_state, store_task_state

try:
    from celery import Celery
except Exception:  # pragma: no cover
    Celery = Any  # type: ignore[misc,assignment]

TASKS_ENABLED = (os.environ.get("MODULE_BASE_CELERY_ENABLED") or "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
DEFAULT_QUEUE = (os.environ.get("MODULE_BASE_CELERY_QUEUE") or "modulo_base").strip() or "modulo_base"
DEFAULT_BROKER_URL = (os.environ.get("MODULE_BASE_CELERY_BROKER_URL") or os.environ.get("CELERY_BROKER_URL") or "redis://localhost:6379/1").strip()
DEFAULT_RESULT_BACKEND = (
    os.environ.get("MODULE_BASE_CELERY_RESULT_BACKEND")
    or os.environ.get("CELERY_RESULT_BACKEND")
    or DEFAULT_BROKER_URL
).strip()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ModuleTaskRegistry:
    def __init__(self, module_key: str) -> None:
        self.module_key = str(module_key or "").strip()
        self._queues: dict[str, str] = {}

    def register(self, task_name: str, *, queue: str = "") -> str:
        normalized = str(task_name or "").strip()
        if not normalized:
            raise ValueError("El nombre de la tarea es obligatorio.")
        task_path = f"{self.module_key}.{normalized}"
        self._queues[task_path] = str(queue or self.module_key or DEFAULT_QUEUE).strip() or DEFAULT_QUEUE
        return task_path

    def get_queue(self, task_name: str) -> str:
        task_path = task_name if "." in str(task_name or "") else f"{self.module_key}.{str(task_name or '').strip()}"
        return self._queues.get(task_path, self.module_key or DEFAULT_QUEUE)

    def get_task_path(self, task_name: str) -> str:
        normalized = str(task_name or "").strip()
        if "." in normalized:
            return normalized
        return f"{self.module_key}.{normalized}"


class ModuleTaskQueue:
    def __init__(self, module_key: str, *, celery_app: Any = None, registry: ModuleTaskRegistry | None = None) -> None:
        self.module_key = str(module_key or "").strip()
        self.registry = registry or ModuleTaskRegistry(self.module_key)
        self.celery_app = celery_app

    def register_task(self, task_name: str, *, queue: str = "") -> str:
        return self.registry.register(task_name, queue=queue)

    def get_queue(self, task_name: str) -> str:
        return self.registry.get_queue(task_name)

    def queue_task(self, task_name: str, kwargs: dict[str, Any] | None = None) -> dict[str, Any]:
        task_path = self.registry.get_task_path(task_name)
        queue_name = self.get_queue(task_name)
        task_id = secrets.token_hex(16)
        payload = {
            "task_id": task_id,
            "task_name": task_path,
            "module_key": self.module_key,
            "queue": queue_name,
            "status": "queued",
            "updated_at": utc_now_iso(),
            "result": {},
            "error": "",
        }
        store_task_state(task_path, task_id, payload)
        if TASKS_ENABLED and self.celery_app is not None:
            try:
                self.celery_app.send_task(
                    task_path,
                    kwargs={**(kwargs or {}), "task_id": task_id},
                    task_id=task_id,
                    queue=queue_name,
                )
                return payload
            except Exception:
                pass
        payload["status"] = "inline"
        payload["updated_at"] = utc_now_iso()
        store_task_state(task_path, task_id, payload)
        return payload

    def get_task_state(self, task_name: str, task_id: str) -> dict[str, Any]:
        task_path = self.registry.get_task_path(task_name)
        payload = get_task_state(task_path, task_id)
        if payload is None:
            return {
                "task_id": str(task_id or "").strip(),
                "task_name": task_path,
                "module_key": self.module_key,
                "queue": self.get_queue(task_name),
                "status": "unknown",
                "updated_at": "",
                "result": {},
                "error": "",
            }
        return payload

    def report_task_state(
        self,
        task_name: str,
        task_id: str,
        *,
        status: str,
        result: dict[str, Any] | None = None,
        error: str = "",
    ) -> dict[str, Any]:
        task_path = self.registry.get_task_path(task_name)
        payload = {
            "task_id": str(task_id or "").strip(),
            "task_name": task_path,
            "module_key": self.module_key,
            "queue": self.get_queue(task_name),
            "status": str(status or "").strip() or "unknown",
            "updated_at": utc_now_iso(),
            "result": result or {},
            "error": str(error or "").strip(),
        }
        store_task_state(task_path, task_id, payload)
        return payload


def build_module_task_registry(module_key: str) -> ModuleTaskRegistry:
    return ModuleTaskRegistry(module_key)


def create_module_task_queue(module_key: str, *, celery_app: Any = None, registry: ModuleTaskRegistry | None = None) -> ModuleTaskQueue:
    return ModuleTaskQueue(module_key, celery_app=celery_app, registry=registry)


__all__ = [
    "DEFAULT_BROKER_URL",
    "DEFAULT_QUEUE",
    "DEFAULT_RESULT_BACKEND",
    "ModuleTaskQueue",
    "ModuleTaskRegistry",
    "TASKS_ENABLED",
    "build_module_task_registry",
    "create_module_task_queue",
    "utc_now_iso",
]
