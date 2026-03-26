from __future__ import annotations

from types import SimpleNamespace

from fastapi_modulo.modulos_sipet.aplicaciones.repositorios import app_repository


class _Row:
    is_enabled = 0
    install_status = ""


class _Query:
    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return _Row()


class _Session:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def query(self, model):
        return _Query()

    def add(self, row):
        return None

    def commit(self):
        return None


def test_set_tenant_module_enabled_returns_legacy_module_payload(monkeypatch) -> None:
    monkeypatch.setattr(app_repository, "_admin_session", lambda: _Session())
    monkeypatch.setitem(
        app_repository.MODULES_BY_KEY,
        "multitienda",
        SimpleNamespace(key="multitienda", always_enabled=False, manageable=True),
    )

    def _list_modules_payload(tenant_key=None, include_legacy=False, **kwargs):
        if include_legacy:
            return [{"key": "multitienda", "label": "Multitienda", "enabled": True}]
        return []

    monkeypatch.setattr(app_repository, "list_modules_payload", _list_modules_payload)
    monkeypatch.setattr(app_repository, "set_module_enabled", lambda module_key, enabled: {"key": module_key, "enabled": enabled})

    payload = app_repository._set_tenant_module_enabled("multitienda", True, "default")

    assert payload["key"] == "multitienda"
    assert payload["restart_required"] is True


def test_set_tenant_module_enabled_promotes_intelicoop_to_global_router(monkeypatch) -> None:
    monkeypatch.setattr(app_repository, "_admin_session", lambda: _Session())
    monkeypatch.setitem(
        app_repository.MODULES_BY_KEY,
        "intelicoop",
        SimpleNamespace(key="intelicoop", always_enabled=False, manageable=True),
    )

    promoted = []

    def _list_modules_payload(tenant_key=None, include_legacy=False, **kwargs):
        if include_legacy:
            return [{"key": "intelicoop", "label": "Intelicoop", "enabled": True}]
        return []

    monkeypatch.setattr(app_repository, "list_modules_payload", _list_modules_payload)
    monkeypatch.setattr(
        app_repository,
        "set_module_enabled",
        lambda module_key, enabled: promoted.append((module_key, enabled)) or {"key": module_key, "enabled": enabled},
    )

    payload = app_repository._set_tenant_module_enabled("intelicoop", True, "default")

    assert payload["key"] == "intelicoop"
    assert payload["restart_required"] is True
    assert promoted == [("intelicoop", True)]


def test_set_tenant_module_enabled_allows_enabling_always_enabled_manageable_module(monkeypatch) -> None:
    monkeypatch.setattr(app_repository, "_admin_session", lambda: _Session())
    monkeypatch.setitem(
        app_repository.MODULES_BY_KEY,
        "empresa",
        SimpleNamespace(key="empresa", always_enabled=True, manageable=True),
    )

    def _list_modules_payload(tenant_key=None, include_legacy=False, **kwargs):
        if include_legacy:
            return [{"key": "empresa", "label": "Empresa", "enabled": True}]
        return []

    monkeypatch.setattr(app_repository, "list_modules_payload", _list_modules_payload)

    payload = app_repository._set_tenant_module_enabled("empresa", True, "default")

    assert payload["key"] == "empresa"
    assert payload["restart_required"] is False


def test_set_tenant_module_enabled_rejects_disabling_always_enabled_manageable_module(monkeypatch) -> None:
    monkeypatch.setitem(
        app_repository.MODULES_BY_KEY,
        "empresa",
        SimpleNamespace(key="empresa", always_enabled=True, manageable=True),
    )

    try:
        app_repository._set_tenant_module_enabled("empresa", False, "default")
    except ValueError as exc:
        assert "no se puede desactivar" in str(exc)
    else:
        raise AssertionError("Expected ValueError when disabling always_enabled module")
