from __future__ import annotations

from types import SimpleNamespace

from fastapi_modulo.core import module_registry


def test_set_module_enabled_allows_enabling_always_enabled_manageable_module(monkeypatch) -> None:
    monkeypatch.setitem(
        module_registry.MODULES_BY_KEY,
        "empresa",
        SimpleNamespace(key="empresa", always_enabled=True, manageable=True),
    )
    monkeypatch.setattr(module_registry, "is_supported_module", lambda module: True)
    monkeypatch.setattr(module_registry, "_ensure_module_settings_table", lambda: None)

    class _Conn:
        def execute(self, *args, **kwargs):
            class _Result:
                rowcount = 1

            return _Result()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class _Engine:
        def begin(self):
            return _Conn()

    monkeypatch.setattr(module_registry, "get_admin_engine", lambda: _Engine())
    monkeypatch.setattr(module_registry, "list_modules_payload", lambda: [{"key": "empresa", "label": "Personalización", "enabled": True}])

    payload = module_registry.set_module_enabled("empresa", True)

    assert payload["key"] == "empresa"
    assert payload["restart_required"] is True


def test_set_module_enabled_rejects_disabling_always_enabled_manageable_module(monkeypatch) -> None:
    monkeypatch.setitem(
        module_registry.MODULES_BY_KEY,
        "empresa",
        SimpleNamespace(key="empresa", always_enabled=True, manageable=True),
    )
    monkeypatch.setattr(module_registry, "is_supported_module", lambda module: True)

    try:
        module_registry.set_module_enabled("empresa", False)
    except ValueError as exc:
        assert "no se puede desactivar" in str(exc)
    else:
        raise AssertionError("Expected ValueError when disabling always_enabled module")
