from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI

from fastapi_modulo.core.db import MAIN, TenantInstalledApp, ensure_tenant_admin_schema
import fastapi_modulo.core.module_registry as module_registry


def test_manageable_module_requires_tenant_installation(monkeypatch) -> None:
    engine = create_engine("sqlite:///:memory:")
    ensure_tenant_admin_schema(engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()
    session.add(
        TenantInstalledApp(
            tenant_key="tenant_demo",
            app_key="crm",
            app_version="0.0.0",
            install_status="installed",
            is_enabled=1,
        )
    )
    session.commit()
    session.close()

    monkeypatch.setattr(module_registry, "get_admin_session_factory", lambda: Session)
    monkeypatch.setattr(module_registry, "_read_module_state_map", lambda: {"crm": True, "system_admin": True})
    monkeypatch.setattr(module_registry, "is_supported_module", lambda module: True)

    assert module_registry.is_module_enabled("crm", tenant_key="tenant_demo") is True
    assert module_registry.is_module_enabled("mkt", tenant_key="tenant_demo") is False


def test_manageable_module_uses_tenant_install_even_when_global_state_is_disabled(monkeypatch) -> None:
    engine = create_engine("sqlite:///:memory:")
    ensure_tenant_admin_schema(engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()
    session.add(
        TenantInstalledApp(
            tenant_key="tenant_demo",
            app_key="organizacion",
            app_version="0.0.0",
            install_status="installed",
            is_enabled=1,
        )
    )
    session.commit()
    session.close()

    monkeypatch.setattr(module_registry, "get_admin_session_factory", lambda: Session)
    monkeypatch.setattr(module_registry, "_read_module_state_map", lambda: {"organizacion": False, "system_admin": True})
    monkeypatch.setattr(module_registry, "is_supported_module", lambda module: True)

    assert module_registry.is_module_enabled("organizacion", tenant_key="tenant_demo") is True


def test_always_enabled_module_stays_available_without_install(monkeypatch) -> None:
    engine = create_engine("sqlite:///:memory:")
    ensure_tenant_admin_schema(engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    monkeypatch.setattr(module_registry, "get_admin_session_factory", lambda: Session)
    monkeypatch.setattr(module_registry, "_read_module_state_map", lambda: {"system_admin": True})
    monkeypatch.setattr(module_registry, "is_supported_module", lambda module: True)

    assert module_registry.is_module_enabled("system_admin", tenant_key="tenant_demo") is True


def test_register_enabled_routers_skips_incomplete_module_import(monkeypatch) -> None:
    app = FastAPI()
    fake_module = module_registry.ModuleDefinition(
        key="organizacion",
        label="Organizacion",
        description="Test",
        router_specs=[module_registry.RouterSpec("fastapi_modulo.modulos.empleados.controladores.empleados")],
    )

    monkeypatch.setattr(module_registry, "MODULE_DEFINITIONS", [fake_module])
    monkeypatch.setattr(module_registry, "_ensure_module_settings_table", lambda: None)
    monkeypatch.setattr(module_registry, "is_module_enabled", lambda module_key, tenant_key=None: True)
    monkeypatch.setattr(module_registry, "is_supported_module", lambda module: True)

    def _raise_key_error(_path: str):
        raise KeyError("fastapi_modulo.modulos.empleados")

    monkeypatch.setattr(module_registry, "import_module", _raise_key_error)

    registered = module_registry.register_enabled_routers(app)

    assert registered == []


def test_legacy_module_is_disabled_by_default(monkeypatch) -> None:
    legacy_module = module_registry.ModuleDefinition(
        key="legacy_demo",
        label="Legacy",
        description="Legacy",
        manifest_file="fastapi_modulo/modulos/legacy_demo/__manifest__.py",
        router_specs=[module_registry.RouterSpec("fastapi_modulo.modulos.legacy_demo.controladores.legacy_demo")],
    )

    monkeypatch.setattr(module_registry, "MODULES_BY_KEY", {"legacy_demo": legacy_module})
    monkeypatch.setattr(module_registry, "_read_module_state_map", lambda: {"legacy_demo": True})

    assert module_registry.is_supported_module(legacy_module) is False
    assert module_registry.is_module_enabled("legacy_demo", tenant_key="tenant_demo") is False


def test_multitienda_is_not_treated_as_unsupported_legacy() -> None:
    module = module_registry.MODULES_BY_KEY["multitienda"]

    assert module_registry.is_legacy_module(module) is False
    assert module_registry.is_supported_module(module) is True
