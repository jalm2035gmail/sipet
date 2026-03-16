from __future__ import annotations

import sys
import types

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient
import fastapi_modulo.modulos.modulo_base.servicios.base_service as base_service_module

fake_main = types.ModuleType("fastapi_modulo.main")


def _fake_render_backend_page(
    request: Request,
    title: str,
    description: str = "",
    content: str = "",
    **_: object,
) -> HTMLResponse:
    return HTMLResponse(f"<html><title>{title}</title><body>{content}</body></html>")


def _fake_get_user_app_access(request: Request) -> list[str]:
    raw = request.headers.get("x-app-access", "")
    return [item.strip() for item in raw.split(",") if item.strip()]


def _fake_is_admin_or_superadmin(request: Request) -> bool:
    return getattr(request.state, "user_role", "").strip().lower() in {"administrador", "admin", "superadmin"}


def _fake_build_view_buttons_html(_view_buttons: object = None) -> str:
    return ""


def _fake_get_colores_context() -> dict[str, str]:
    return {
        "primary": "#14532d",
        "secondary": "#0f172a",
    }


fake_main.render_backend_page = _fake_render_backend_page
fake_main._get_user_app_access = _fake_get_user_app_access
fake_main.is_admin_or_superadmin = _fake_is_admin_or_superadmin
fake_main.build_view_buttons_html = _fake_build_view_buttons_html
fake_main.get_colores_context = _fake_get_colores_context
sys.modules["fastapi_modulo.main"] = fake_main

import fastapi_modulo.modulos.modulo_base.core.responses as core_responses  # noqa: E402
from fastapi_modulo.modulos.modulo_base.controladores.modulo_base import MODULE_ROUTERS, router  # noqa: E402
from fastapi_modulo.modulos.modulo_base.__manifest__ import MANIFEST  # noqa: E402
from fastapi_modulo.modulos.modulo_base.bootstrap import MODULE_CONFIG, module, permission_registry  # noqa: E402
from fastapi_modulo.modulos.modulo_base.core.audit import TenantAuditMixin  # noqa: E402
from fastapi_modulo.modulos.modulo_base.core.permissions import STANDARD_MODULE_ACTIONS, build_standard_permissions  # noqa: E402
from fastapi_modulo.modulos.modulo_base.core.repository import BaseRepository, SQLAlchemyRepository  # noqa: E402
from fastapi_modulo.modulos.modulo_base.core.responses import ModuleResponseBuilder  # noqa: E402
from fastapi_modulo.modulos.modulo_base.core.service import BaseService  # noqa: E402
from fastapi_modulo.modulos.modulo_base.modelos.db_models import ModuloBaseRegistro  # noqa: E402
from fastapi_modulo.modulos.modulo_base.modelos.schemas import APIHealthResponse, APIResponse, APIResumenResponse, ModuloBaseCreate, ModuloBaseResumenResponse  # noqa: E402

core_responses.render_backend_page_html = _fake_render_backend_page


def _app() -> TestClient:
    app = FastAPI()

    @app.middleware("http")
    async def inject_context(request: Request, call_next):
        request.state.user_role = request.headers.get("x-role", "usuario")
        request.state.tenant_id = request.headers.get("x-tenant-id", "test")
        return await call_next(request)

    app.include_router(router)
    return TestClient(app)


def test_modulo_base_requires_access() -> None:
    client = _app()
    response = client.get("/modulo-base")
    assert response.status_code == 403


def test_modulo_base_page_renders_with_access() -> None:
    client = _app()
    response = client.get("/modulo-base", headers={"x-role": "admin"})
    assert response.status_code == 200
    assert "Modulo base" in response.text


def test_modulo_base_resumen(monkeypatch) -> None:
    class FakeQuery:
        def filter_by(self, **_filters: object) -> "FakeQuery":
            return self

        def count(self) -> int:
            return 0

    class FakeSession:
        def query(self, _model: object) -> FakeQuery:
            return FakeQuery()

        def close(self) -> None:
            return None

    monkeypatch.setattr(base_service_module, "ensure_modulo_base_schema", lambda: None)
    monkeypatch.setattr(base_service_module, "get_db", lambda: FakeSession())

    client = _app()
    response = client.get("/api/modulo-base/resumen", headers={"x-role": "admin"})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["module"] == "modulo_base"
    assert "core" in body["data"]["sections"]
    assert APIResumenResponse(**body).data == ModuloBaseResumenResponse(**body["data"])


def test_modulo_base_assets() -> None:
    client = _app()
    js = client.get("/api/modulo-base/assets/modulo_base.js", headers={"x-role": "admin"})
    css = client.get("/api/modulo-base/assets/modulo_base.css", headers={"x-role": "admin"})
    assert js.status_code == 200
    assert css.status_code == 200


def test_modulo_base_health_response_model() -> None:
    client = _app()
    response = client.get("/api/modulo-base/health", headers={"x-role": "admin"})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert APIHealthResponse(**body).data is not None


def test_manifest_has_sidebar_icon() -> None:
    assert MANIFEST["icon"] == "fa-solid fa-layer-group"


def test_module_config_uses_internal_framework_contracts() -> None:
    assert MODULE_CONFIG.template_name == "base_page.html"
    assert MODULE_CONFIG.assets_prefix == "/api/modulo-base/assets"
    assert MODULE_CONFIG.uses_migrations is True
    assert MODULE_CONFIG.requires_data_bootstrap is True
    assert MODULE_CONFIG.requires_seeds is True
    assert MODULE_CONFIG.migrations_dir.name == "migrations"
    assert MODULE_CONFIG.migration_versions_dir.name == "versions"


def test_permission_registry_loads_module_permissions() -> None:
    permissions = permission_registry.load()
    assert permissions
    assert permissions[0].code == "modulo_base.ver"
    assert permissions[-1].code == "modulo_base.auditoria"
    assert [permission.action for permission in permissions] == list(STANDARD_MODULE_ACTIONS)


def test_standard_permission_builder_covers_official_actions() -> None:
    permissions = build_standard_permissions("demo", "Demo")
    assert [permission.code for permission in permissions] == [
        "demo.ver",
        "demo.crear",
        "demo.editar",
        "demo.eliminar",
        "demo.exportar",
        "demo.aprobar",
        "demo.configurar",
        "demo.administrar",
        "demo.auditoria",
    ]


def test_base_module_declares_uniform_behavior() -> None:
    app = FastAPI()

    module.register_assets()
    module.register_routes(app)

    assert module.name == "Modulo base"
    assert module.route == "/modulo-base"
    assert "modulo_base.ver" in module.permissions
    assert "modulo_base.auditoria" in module.permissions
    assert module.uses_migrations is True
    assert module.requires_data_bootstrap is True
    assert module.requires_seeds is True
    assert module.assets["css"].endswith("static/css/modulo_base.css")
    assert module.assets["js"].endswith("static/js/modulo_base.js")
    assert module.router is router


def test_module_routers_are_declared_explicitly() -> None:
    assert len(MODULE_ROUTERS) == 3
    assert all(item is not None for item in MODULE_ROUTERS)


def test_manifest_declares_alembic_contract() -> None:
    assert MANIFEST["schema"]["uses_migrations"] is True
    assert MANIFEST["schema"]["alembic_required_in_production"] is True
    assert "migrations/README.md" in MANIFEST["structure"]["migrations"]
    assert MANIFEST["permissions"] == [
        "modulo_base.ver",
        "modulo_base.crear",
        "modulo_base.editar",
        "modulo_base.eliminar",
        "modulo_base.exportar",
        "modulo_base.aprobar",
        "modulo_base.configurar",
        "modulo_base.administrar",
        "modulo_base.auditoria",
    ]
    assert MANIFEST["api_prefix"] == "/api/modulo-base"
    assert MANIFEST["routes"][0] == "/modulo-base"
    assert MANIFEST["menu"]["route"] == "/modulo-base"
    assert MANIFEST["widgets"] == []
    assert MANIFEST["tasks"] == []


def test_api_response_schema_is_homogeneous() -> None:
    body = APIResponse(ok=True, message="ok", data={"module": "modulo_base"})
    assert body.model_dump() == {
        "ok": True,
        "message": "ok",
        "data": {"module": "modulo_base"},
    }


def test_response_builder_error_helpers() -> None:
    class AssetStub:
        def render_view(self, _name: str, fallback: str = "") -> str:
            return fallback

    builder = ModuleResponseBuilder(MODULE_CONFIG, AssetStub())  # type: ignore[arg-type]
    error = builder.error_response("fallo", status_code=422)
    forbidden = builder.forbidden_response()
    assert error.status_code == 422
    assert forbidden.status_code == 403


def test_create_schema_validates_name_length() -> None:
    schema = ModuloBaseCreate(nombre="demo", descripcion="ok")
    assert schema.nombre == "demo"


def test_base_service_stores_db_and_tenant() -> None:
    db = object()
    service = BaseService(db=db, tenant_id="tenant-a")
    assert service.db is db
    assert service.tenant_id == "tenant-a"


def test_base_repository_initializes_db() -> None:
    db = object()
    repository = BaseRepository(db)
    assert repository.db is db


def test_tenant_audit_mixin_defines_standard_columns() -> None:
    assert TenantAuditMixin.tenant_id.nullable is False
    assert TenantAuditMixin.creado_en.nullable is False
    assert TenantAuditMixin.actualizado_en.nullable is False
    assert TenantAuditMixin.creado_por.nullable is True
    assert TenantAuditMixin.actualizado_por.nullable is True


def test_operational_model_inherits_tenant_audit_mixin() -> None:
    assert issubclass(ModuloBaseRegistro, TenantAuditMixin)
    assert "tenant_id" in ModuloBaseRegistro.__table__.columns
    assert "creado_en" in ModuloBaseRegistro.__table__.columns
    assert "actualizado_en" in ModuloBaseRegistro.__table__.columns
    assert "creado_por" in ModuloBaseRegistro.__table__.columns
    assert "actualizado_por" in ModuloBaseRegistro.__table__.columns


def test_sqlalchemy_repository_crud_contract() -> None:
    class FakeModel:
        def __init__(self, **values: object) -> None:
            self.id = values.get("id")
            self.nombre = values.get("nombre")

    class FakeQuery:
        def __init__(self, records: list[FakeModel]) -> None:
            self.records = records

        def filter_by(self, **filters: object) -> "FakeQuery":
            filtered = [
                record
                for record in self.records
                if all(getattr(record, key, None) == value for key, value in filters.items())
            ]
            return FakeQuery(filtered)

        def first(self) -> FakeModel | None:
            return self.records[0] if self.records else None

        def all(self) -> list[FakeModel]:
            return list(self.records)

        def count(self) -> int:
            return len(self.records)

    class FakeDB:
        def __init__(self) -> None:
            self.records: list[FakeModel] = []

        def query(self, _model: type[FakeModel]) -> FakeQuery:
            return FakeQuery(self.records)

        def add(self, instance: FakeModel) -> None:
            instance.id = len(self.records) + 1
            self.records.append(instance)

        def commit(self) -> None:
            return None

        def refresh(self, _instance: FakeModel) -> None:
            return None

        def delete(self, instance: FakeModel) -> None:
            self.records.remove(instance)

    repository = SQLAlchemyRepository(FakeDB(), FakeModel)
    created = repository.create(nombre="uno")
    listed = repository.list()
    fetched = repository.get(created.id)
    updated = repository.update(created.id, nombre="dos")
    deleted = repository.delete(created.id)

    assert created.id == 1
    assert len(listed) == 1
    assert fetched is created
    assert updated is created
    assert created.nombre == "dos"
    assert deleted is True
    assert repository.list() == []
