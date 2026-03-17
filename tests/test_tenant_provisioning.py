from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi_modulo.core.tenant_provisioning import build_tenant_payload, create_tenant
from fastapi_modulo.core.db import (
    MAIN,
    TenantDomain,
    TenantInstalledApp,
    TenantProvisionLog,
    TenantRegistry,
    ensure_tenant_admin_schema,
)


def test_build_tenant_payload() -> None:
    payload = build_tenant_payload("cliente1.midominio.com")
    assert payload.tenant_key == "cliente1_midominio_com"
    assert payload.primary_host == "cliente1.midominio.com"
    assert payload.db_name


def test_create_tenant_is_idempotent() -> None:
    engine = create_engine("sqlite:///:memory:")
    ensure_tenant_admin_schema(engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    session = Session()
    result_first = create_tenant(session, primary_host="cliente1.midominio.com")
    assert result_first.created is True

    result_second = create_tenant(session, primary_host="cliente1.midominio.com")
    assert result_second.created is False

    registry_count = session.query(TenantRegistry).count()
    domain_count = session.query(TenantDomain).count()
    app_count = session.query(TenantInstalledApp).count()
    log_count = session.query(TenantProvisionLog).count()
    session.close()

    assert registry_count == 1
    assert domain_count == 1
    assert app_count == 2
    assert log_count == 2
