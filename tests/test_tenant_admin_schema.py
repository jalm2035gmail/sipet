from fastapi_modulo.core.db import (
    MAIN,
    TenantDomain,
    TenantInstalledApp,
    TenantProvisionLog,
    TenantRegistry,
    ensure_tenant_admin_schema,
)
from sqlalchemy import create_engine, inspect


def test_tenant_admin_models_have_expected_tables() -> None:
    assert TenantRegistry.__tablename__ == "tenant_registry"
    assert TenantDomain.__tablename__ == "tenant_domains"
    assert TenantInstalledApp.__tablename__ == "tenant_installed_apps"
    assert TenantProvisionLog.__tablename__ == "tenant_provision_logs"


def test_ensure_tenant_admin_schema_creates_tables() -> None:
    engine = create_engine("sqlite:///:memory:")
    MAIN.metadata.create_all(bind=engine, tables=[])
    ensure_tenant_admin_schema(engine)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert "tenant_registry" in tables
    assert "tenant_domains" in tables
    assert "tenant_installed_apps" in tables
    assert "tenant_provision_logs" in tables
