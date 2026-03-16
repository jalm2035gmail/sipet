from __future__ import annotations

from fastapi_modulo.modulos.aplicaciones.servicios import redis_service, task_queue_service


class _FakeRedis:
    def __init__(self) -> None:
        self.storage: dict[str, str] = {}

    def ping(self) -> bool:
        return True

    def setex(self, key: str, _ttl: int, value: str) -> None:
        self.storage[key] = value

    def get(self, key: str) -> str | None:
        return self.storage.get(key)

    def delete(self, key: str) -> None:
        self.storage.pop(key, None)


class _FakeCelery:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def send_task(self, name: str, kwargs: dict, task_id: str, queue: str) -> None:
        self.calls.append({"name": name, "kwargs": kwargs, "task_id": task_id, "queue": queue})


def test_queue_task_uses_celery_and_persists_state(monkeypatch) -> None:
    fake_redis = _FakeRedis()
    fake_celery = _FakeCelery()
    monkeypatch.setattr(redis_service, "get_redis_client", lambda: fake_redis)
    monkeypatch.setattr(task_queue_service, "celery_app", fake_celery)
    monkeypatch.setattr(task_queue_service, "TASKS_ENABLED", True)

    queued = task_queue_service.queue_task("protocol_sync", {"mode": "repair_missing_only"})
    state = task_queue_service.get_async_task_state("protocol_sync", str(queued["task_id"]))

    assert queued["status"] == "queued"
    assert fake_celery.calls[0]["name"] == "applications.protocol_sync"
    assert state["status"] == "queued"


def test_queue_task_falls_back_to_inline_when_disabled(monkeypatch) -> None:
    fake_redis = _FakeRedis()
    monkeypatch.setattr(redis_service, "get_redis_client", lambda: fake_redis)
    monkeypatch.setattr(task_queue_service, "TASKS_ENABLED", False)

    queued = task_queue_service.queue_task("package_apply", {"module_key": "crm"})

    assert queued["status"] == "inline"
    assert queued["task_name"] == "package_apply"
