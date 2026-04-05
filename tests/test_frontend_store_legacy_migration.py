from __future__ import annotations

from fastapi_modulo.modulos_sipet.frontend.modelos import frontend_store


def test_legacy_migration_disabled_by_default_in_production(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("FRONTEND_LEGACY_MIGRATION_ENABLED", raising=False)

    assert frontend_store.legacy_migration_enabled() is False


def test_legacy_migration_can_be_enabled_explicitly_in_production(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("FRONTEND_LEGACY_MIGRATION_ENABLED", "true")

    assert frontend_store.legacy_migration_enabled() is True


def test_legacy_migration_enabled_by_default_outside_production(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("FRONTEND_LEGACY_MIGRATION_ENABLED", raising=False)

    assert frontend_store.legacy_migration_enabled() is True
