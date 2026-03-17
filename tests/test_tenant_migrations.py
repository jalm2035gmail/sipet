from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi_modulo.core.tenant_migrations import list_migration_targets, run_tenant_migration
from fastapi_modulo.core.db import (
    MAIN,
    TenantMigrationRun,
    TenantRegistry,
    ensure_tenant_admin_schema,
)


def test_list_migration_targets_filters_active_tenants() -> None:
    engine = create_engine("sqlite:///:memory:")
    ensure_tenant_admin_schema(engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()
    session.add(TenantRegistry(tenant_key="a", primary_host="a.midominio.com", db_name="a_dev", db_url="sqlite:///./a_dev.db", is_active=1))
    session.add(TenantRegistry(tenant_key="b", primary_host="b.midominio.com", db_name="b_dev", db_url="sqlite:///./b_dev.db", is_active=0))
    session.commit()
    targets = list_migration_targets(session)
    session.close()
    assert [item.tenant_key for item in targets] == ["a"]


def test_run_tenant_migration_records_completed_run(tmp_path: Path) -> None:
    admin_engine = create_engine("sqlite:///:memory:")
    ensure_tenant_admin_schema(admin_engine)
    tenant_db_path = tmp_path / "tenant_demo.db"
    tenant_db_url = f"sqlite:///{tenant_db_path}"
    Session = sessionmaker(bind=admin_engine, autocommit=False, autoflush=False)
    session = Session()
    tenant = TenantRegistry(
        tenant_key="tenant_demo",
        primary_host="tenant.demo.com",
        db_name="tenant_demo_dev",
        db_url=tenant_db_url,
        is_active=1,
    )
    session.add(tenant)
    session.commit()

    results = run_tenant_migration(session, tenant)
    runs = session.query(TenantMigrationRun).filter(TenantMigrationRun.tenant_key == "tenant_demo").all()
    session.close()

    assert results
    assert any(item.status == "completed" for item in results)
    assert any(item.migration_key == "ensure_ia_config_schema" for item in results)
    assert runs
