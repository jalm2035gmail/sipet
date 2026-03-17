from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request

from fastapi_modulo.core.db import TenantInstalledApp, TenantMigrationRun, TenantRegistry, ensure_tenant_admin_schema
from fastapi_modulo.modulos_sipet.web.servicios.tenant_observability_service import build_tenant_diagnostics


def test_build_tenant_diagnostics(monkeypatch) -> None:
    engine = create_engine("sqlite:///:memory:")
    ensure_tenant_admin_schema(engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()
    session.add(TenantRegistry(tenant_key="tenant_demo", primary_host="demo.midominio.com", db_name="demo_dev", db_url="sqlite:///./demo_dev.db", is_active=1))
    session.add(TenantInstalledApp(tenant_key="tenant_demo", app_key="crm", app_version="0.0.0", install_status="installed", is_enabled=1))
    session.add(TenantMigrationRun(tenant_key="tenant_demo", target_scope="tenant", migration_key="core", status="completed", detail="ok"))
    session.commit()
    session.close()

    monkeypatch.setattr("fastapi_modulo.modulos_sipet.web.servicios.tenant_observability_service._admin_session", lambda: Session())
    monkeypatch.setattr("fastapi_modulo.modulos_sipet.web.servicios.tenant_observability_service.get_active_module_keys", lambda tenant_key="": ["crm"])

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    scope = {
        "type": "http",
        "method": "GET",
        "scheme": "https",
        "path": "/api/backend/tenant-diagnostics",
        "headers": [(b"host", b"demo.midominio.com")],
    }
    request = Request(scope, receive=receive)
    request.state.tenant_id = "tenant_demo"
    request.state.tenant_key = "tenant_demo"
    request.state.access_mode = "tenant"
    request.state.tenant_context = type("Ctx", (), {"host": "demo.midominio.com"})()

    payload = build_tenant_diagnostics(request)
    assert payload["tenant"]["tenant_key"] == "tenant_demo"
    assert payload["database"]["url"] == "sqlite:///[redacted]"
    assert payload["registry"]["db_url"] == "sqlite:///[redacted]"
    assert payload["modules"]["installed_apps"] == ["crm"]
    assert payload["modules"]["active_module_keys"] == ["crm"]
