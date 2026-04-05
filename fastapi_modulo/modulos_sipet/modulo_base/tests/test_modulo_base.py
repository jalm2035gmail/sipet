from __future__ import annotations

import sys
import types
import io
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient
import fastapi_modulo.modulos_sipet.modulo_base.servicios.base_service as base_service_module
import fastapi_modulo.modulos_sipet.modulo_base.controladores.dependencies as dependencies_module
import fastapi_modulo.modulos_sipet.modulo_base.core.cache_service as cache_service_module
import fastapi_modulo.modulos_sipet.modulo_base.core.lock_service as lock_service_module
import fastapi_modulo.modulos_sipet.modulo_base.core.media_service as media_service_module
import fastapi_modulo.modulos_sipet.modulo_base.core.task_queue as task_queue_module
import fastapi_modulo.modulos_sipet.modulo_base.core.http_service as http_service_module

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

import fastapi_modulo.modulos_sipet.modulo_base.controladores.api as api_module  # noqa: E402
import fastapi_modulo.modulos_sipet.modulo_base.core.responses as core_responses  # noqa: E402
from fastapi_modulo.modulos_sipet.modulo_base.controladores.modulo_base import MODULE_ROUTERS, router  # noqa: E402
from fastapi_modulo.modulos_sipet.modulo_base.__manifest__ import MANIFEST  # noqa: E402
from fastapi_modulo.modulos_sipet.modulo_base.bootstrap import MODULE_CONFIG, module, permission_registry  # noqa: E402
from fastapi_modulo.modulos_sipet.modulo_base.core.audit import BaseEntity, SoftDeleteBaseEntity, TenantAuditMixin  # noqa: E402
from fastapi_modulo.modulos_sipet.modulo_base.core.exceptions import install_module_exception_handlers  # noqa: E402
from fastapi_modulo.modulos_sipet.modulo_base.core.permissions import STANDARD_MODULE_ACTIONS, build_standard_permissions  # noqa: E402
from fastapi_modulo.modulos_sipet.modulo_base.core.repository import BaseRepository, SQLAlchemyRepository  # noqa: E402
from fastapi_modulo.modulos_sipet.modulo_base.core.responses import ModuleResponseBuilder  # noqa: E402
from fastapi_modulo.modulos_sipet.modulo_base.core.security import (  # noqa: E402
    SENSITIVE_ACTION_MODULE_ACTIVATE,
    hash_sensitive_secret,
    issue_sensitive_action_token,
    issue_signed_authorization,
    issue_temporary_token,
    require_admin_operation,
    verify_sensitive_action_token,
    verify_signed_authorization,
    verify_sensitive_secret,
    verify_temporary_token,
)
from fastapi_modulo.modulos_sipet.modulo_base.core.task_queue import (  # noqa: E402
    ModuleTaskRegistry,
    create_module_task_queue,
)
from fastapi_modulo.modulos_sipet.modulo_base.core.visual_editor_service import VisualEditorContract  # noqa: E402
from fastapi_modulo.modulos_sipet.modulo_base.core.cache_service import (  # noqa: E402
    check_rate_limit,
    create_operational_session,
    get_operational_session,
    get_task_state,
    get_tenant_cache,
    set_tenant_cache,
    store_task_state,
)
from fastapi_modulo.modulos_sipet.modulo_base.core.http_service import BaseHTTPService  # noqa: E402
from fastapi_modulo.modulos_sipet.modulo_base.core.lock_service import acquire_lock, guarded_lock, release_lock  # noqa: E402
from fastapi_modulo.modulos_sipet.modulo_base.core.media_service import (  # noqa: E402
    build_media_filename,
    create_thumbnail,
    normalize_image,
    process_and_store_media,
    sanitize_media_name,
    validate_image_payload,
)
from fastapi_modulo.modulos_sipet.modulo_base.core.ml_service import ModuleMLService  # noqa: E402
from fastapi_modulo.modulos_sipet.modulo_base.core.service import BaseService  # noqa: E402
from fastapi_modulo.modulos_sipet.modulo_base.modelos.db_models import ModuloBaseCategoria, ModuloBaseRegistro  # noqa: E402
from fastapi_modulo.modulos_sipet.modulo_base.modelos.enums import ModuloBaseEstado  # noqa: E402
from pydantic import ValidationError

from fastapi_modulo.modulos_sipet.modulo_base.modelos.schemas import (  # noqa: E402
    APIHealthResponse,
    APIResponse,
    APIResumenResponse,
    ModuloBaseCategoriaCreate,
    ModuloBaseCategoriaResponse,
    ModuloBaseCreate,
    ModuloBaseListResponse,
    ModuloBaseResponse,
    ModuloBaseResumenResponse,
    ModuloBaseUpdate,
)

try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None  # type: ignore[assignment]

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


def test_modulo_base_client_fixture_supports_shared_context(client_factory) -> None:
    response = client_factory(user_role="admin", tenant_id="fixture-tenant").get("/modulo-base")
    assert response.status_code == 200


def test_modulo_base_page_renders_with_access() -> None:
    client = _app()
    response = client.get("/modulo-base", headers={"x-role": "admin"})
    assert response.status_code == 200
    assert "Modulo base" in response.text
    assert "Design System" in response.text
    assert "Font Awesome" in response.text
    assert "Tabla base" in response.text


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

    monkeypatch.setattr(dependencies_module, "get_db", lambda: FakeSession())

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


def test_modulo_base_assets_require_access(client) -> None:
    js = client.get("/api/modulo-base/assets/modulo_base.js")
    css = client.get("/api/modulo-base/assets/modulo_base.css")
    assert js.status_code == 403
    assert css.status_code == 403


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
    assert MODULE_CONFIG.requires_data_bootstrap is False
    assert MODULE_CONFIG.requires_seeds is False
    assert MODULE_CONFIG.migrations_dir.name == "migrations"
    assert MODULE_CONFIG.migration_versions_dir.name == "versions"


def test_permission_registry_loads_module_permissions() -> None:
    permissions = permission_registry.load()
    assert permissions
    assert permissions[0].code == "modulo_base.ver"
    assert permissions[-1].code == "modulo_base.auditoria"
    assert [permission.action for permission in permissions] == list(STANDARD_MODULE_ACTIONS)


def test_permission_registry_rejects_request_without_required_access() -> None:
    app = FastAPI()
    module.register_routes(app)
    response = TestClient(app).get("/api/modulo-base/health")
    assert response.status_code == 403


def test_permission_registry_allows_explicit_module_permission() -> None:
    app = FastAPI()

    @app.middleware("http")
    async def inject_context(request: Request, call_next):
        request.state.user_role = "usuario"
        request.state._effective_access_payload = {
            "role": "usuario",
            "screen_access_levels": {"modulo_base": {"full_access": True, "read_only": False, "department_only": False, "user_only": False, "special_permissions": False}},
            "user_app_access": ["modulo_base"],
            "backend_roles": [],
            "conversation_access": {},
            "permission_flags": {"modulo_base_ver": True},
        }
        return await call_next(request)

    module.register_routes(app)
    response = TestClient(app).get("/api/modulo-base/health")

    assert response.status_code == 200


def test_permission_registry_rejects_app_access_without_required_permission() -> None:
    app = FastAPI()

    @app.middleware("http")
    async def inject_context(request: Request, call_next):
        request.state.user_role = "usuario"
        request.state._effective_access_payload = {
            "role": "usuario",
            "screen_access_levels": {"modulo_base": {"full_access": True, "read_only": False, "department_only": False, "user_only": False, "special_permissions": False}},
            "user_app_access": ["modulo_base"],
            "backend_roles": [],
            "conversation_access": {},
            "permission_flags": {},
        }
        return await call_next(request)

    module.register_routes(app)
    response = TestClient(app).get("/api/modulo-base/health")

    assert response.status_code == 403


def test_permission_registry_ignores_client_supplied_permission_headers() -> None:
    app = FastAPI()

    @app.middleware("http")
    async def inject_context(request: Request, call_next):
        request.state.user_role = "usuario"
        request.state._effective_access_payload = {
            "role": "usuario",
            "screen_access_levels": {"modulo_base": {"full_access": True, "read_only": False, "department_only": False, "user_only": False, "special_permissions": False}},
            "user_app_access": ["modulo_base"],
            "backend_roles": [],
            "conversation_access": {},
            "permission_flags": {},
        }
        return await call_next(request)

    module.register_routes(app)
    response = TestClient(app).get("/api/modulo-base/health", headers={"x-permissions": "modulo_base.ver"})

    assert response.status_code == 403


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
    assert module.requires_data_bootstrap is False
    assert module.requires_seeds is False
    assert module.assets["css"].endswith("static/css/modulo_base.css")
    assert module.assets["js"].endswith("static/js/modulo_base.js")
    assert module.router is router


def test_bootstrap_init_does_not_create_schema_implicitly(monkeypatch) -> None:
    calls: list[str] = []

    monkeypatch.setattr("fastapi_modulo.modulos_sipet.modulo_base.bootstrap.ensure_modulo_base_schema", lambda **_: calls.append("schema"))
    monkeypatch.setattr("fastapi_modulo.modulos_sipet.modulo_base.bootstrap.bootstrap_modulo_base_data", lambda: calls.append("bootstrap"))
    monkeypatch.setattr("fastapi_modulo.modulos_sipet.modulo_base.bootstrap.seed_modulo_base_data", lambda: calls.append("seed"))

    module.init()

    assert calls == []


def test_bootstrap_schema_setup_requires_explicit_call(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    monkeypatch.setattr(
        "fastapi_modulo.modulos_sipet.modulo_base.bootstrap.ensure_modulo_base_schema",
        lambda **kwargs: calls.append(kwargs),
    )

    from fastapi_modulo.modulos_sipet.modulo_base.bootstrap import prepare_modulo_base_schema_for_dev

    prepare_modulo_base_schema_for_dev(host="tenant-host")

    assert calls == [
        {
            "allow_create_all_in_dev": MODULE_CONFIG.allow_create_all_in_dev,
            "uses_migrations": MODULE_CONFIG.uses_migrations,
            "host": "tenant-host",
        }
    ]


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
        "errors": [],
    }


def test_response_builder_error_helpers() -> None:
    class AssetStub:
        def render_view(self, _name: str, fallback: str = "") -> str:
            return fallback

    builder = ModuleResponseBuilder(MODULE_CONFIG, AssetStub())  # type: ignore[arg-type]
    success = builder.success_response({"module": "modulo_base"})
    error = builder.error_response("fallo", status_code=422)
    forbidden = builder.forbidden_response()
    assert success.status_code == 200
    assert error.status_code == 422
    assert forbidden.status_code == 403
    assert success.body == b'{"ok":true,"message":"","data":{"module":"modulo_base"},"errors":[]}'
    assert b'"type":"error"' in error.body
    assert b'"type":"permission_error"' in forbidden.body


def test_resumen_uses_request_tenant_header(monkeypatch, client_factory) -> None:
    class FakeQuery:
        def __init__(self) -> None:
            self.filters: dict[str, object] = {}

        def filter_by(self, **filters: object) -> "FakeQuery":
            self.filters = filters
            return self

        def count(self) -> int:
            return 7 if self.filters.get("tenant_id") == "tenant-x" else 0

    class FakeSession:
        def query(self, _model: object) -> FakeQuery:
            return FakeQuery()

        def close(self) -> None:
            return None

    monkeypatch.setattr(dependencies_module, "get_db", lambda: FakeSession())

    response = client_factory(user_role="admin", tenant_id="tenant-x").get("/api/modulo-base/resumen")

    assert response.status_code == 200
    assert response.json()["data"]["tenant_id"] == "tenant-x"
    assert response.json()["data"]["total_registros"] == 7


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    def ping(self) -> bool:
        return True

    def setex(self, key: str, _ttl: int, value: str) -> None:
        self.store[key] = value

    def get(self, key: str) -> str | None:
        return self.store.get(key)

    def delete(self, key: str) -> None:
        self.store.pop(key, None)

    def incr(self, key: str) -> int:
        value = int(self.store.get(key, "0")) + 1
        self.store[key] = str(value)
        return value

    def expire(self, _key: str, _ttl: int) -> bool:
        return True

    def set(self, key: str, value: str, nx: bool = False, ex: int | None = None) -> bool:
        if nx and key in self.store:
            return False
        self.store[key] = value
        return ex is not None


class FakeCelery:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def send_task(self, name: str, kwargs: dict[str, object], task_id: str, queue: str) -> None:
        self.calls.append(
            {
                "name": name,
                "kwargs": kwargs,
                "task_id": task_id,
                "queue": queue,
            }
        )


class FakeHTTPResponse:
    def __init__(self, status_code: int = 200, payload: object = None, text: str = "", headers: dict[str, str] | None = None) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self.headers = headers or {"content-type": "application/json"}

    def json(self) -> object:
        if self._payload is None:
            raise ValueError("sin json")
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = http_service_module.httpx.Request("GET", "https://example.com") if http_service_module.httpx is not None else None
            response = http_service_module.httpx.Response(self.status_code, request=request) if http_service_module.httpx is not None else None
            raise http_service_module.httpx.HTTPStatusError("fallo", request=request, response=response)


class FakeHTTPClient:
    def __init__(self, responses: list[object]) -> None:
        self.responses = responses
        self.calls: list[dict[str, object]] = []

    def request(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _make_test_image_bytes(size: tuple[int, int] = (300, 180), color: tuple[int, int, int] = (20, 40, 60)) -> bytes:
    if Image is None:
        raise RuntimeError("Pillow no disponible en pruebas")
    image = Image.new("RGB", size, color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_cache_service_supports_tenant_cache_task_state_and_operational_session(monkeypatch) -> None:
    fake = FakeRedis()
    monkeypatch.setattr(cache_service_module, "get_redis_client", lambda: fake)
    monkeypatch.setattr(lock_service_module, "get_redis_client", lambda: fake)

    set_tenant_cache("tenant-a", "dashboard", "summary", {"total": 1}, ttl_seconds=60)
    store_task_state("sync", "task-1", {"status": "running"}, ttl_seconds=60)
    session = create_operational_session("admin", {"step": "upload"}, ttl_seconds=60)

    assert get_tenant_cache("tenant-a", "dashboard", "summary") == {"total": 1}
    assert get_task_state("sync", "task-1") == {"status": "running"}
    assert get_operational_session(session["session_id"]) == session


def test_cache_service_supports_rate_limit(monkeypatch) -> None:
    fake = FakeRedis()
    monkeypatch.setattr(cache_service_module, "get_redis_client", lambda: fake)

    first = check_rate_limit("api", "tenant-a", limit=2, window_seconds=60)
    second = check_rate_limit("api", "tenant-a", limit=2, window_seconds=60)
    third = check_rate_limit("api", "tenant-a", limit=2, window_seconds=60)

    assert first["allowed"] is True
    assert second["allowed"] is True
    assert third["allowed"] is False


def test_lock_service_supports_distributed_lock_flow(monkeypatch) -> None:
    fake = FakeRedis()
    monkeypatch.setattr(cache_service_module, "get_redis_client", lambda: fake)
    monkeypatch.setattr(lock_service_module, "get_redis_client", lambda: fake)

    token = acquire_lock("module-sync", ttl_seconds=60)
    assert token
    assert acquire_lock("module-sync", ttl_seconds=60) == ""
    release_lock("module-sync", token)
    assert acquire_lock("module-sync", ttl_seconds=60)


def test_guarded_lock_raises_conflict_when_lock_exists(monkeypatch) -> None:
    fake = FakeRedis()
    monkeypatch.setattr(cache_service_module, "get_redis_client", lambda: fake)
    monkeypatch.setattr(lock_service_module, "get_redis_client", lambda: fake)
    token = acquire_lock("module-import", ttl_seconds=60)
    assert token

    try:
        with guarded_lock("module-import", detail="ocupado"):
            raise AssertionError("No deberia entrar al contexto")
    except HTTPException as exc:
        assert exc.status_code == 409
        assert exc.detail == "ocupado"
    else:
        raise AssertionError("guarded_lock debe fallar si el lock ya existe")


def test_task_queue_registry_supports_module_task_contract() -> None:
    registry = ModuleTaskRegistry("modulo_base")
    task_path = registry.register("protocol_sync", queue="modulo_base_sync")
    assert task_path == "modulo_base.protocol_sync"
    assert registry.get_queue("protocol_sync") == "modulo_base_sync"
    assert registry.get_task_path("protocol_sync") == "modulo_base.protocol_sync"


def test_task_queue_service_queues_task_with_celery_and_persists_state(monkeypatch) -> None:
    fake_redis = FakeRedis()
    fake_celery = FakeCelery()
    monkeypatch.setattr(cache_service_module, "get_redis_client", lambda: fake_redis)
    monkeypatch.setattr(task_queue_module, "TASKS_ENABLED", True)

    queue = create_module_task_queue("modulo_base", celery_app=fake_celery)
    queue.register_task("report_export", queue="modulo_base_reports")
    queued = queue.queue_task("report_export", {"format": "pdf"})
    state = queue.get_task_state("report_export", str(queued["task_id"]))

    assert queued["status"] == "queued"
    assert state["status"] == "queued"
    assert fake_celery.calls[0]["name"] == "modulo_base.report_export"
    assert fake_celery.calls[0]["queue"] == "modulo_base_reports"


def test_task_queue_service_reports_task_state(monkeypatch) -> None:
    fake_redis = FakeRedis()
    monkeypatch.setattr(cache_service_module, "get_redis_client", lambda: fake_redis)

    queue = create_module_task_queue("modulo_base", celery_app=None)
    queue.register_task("protocol_sync", queue="modulo_base_sync")
    queued = queue.queue_task("protocol_sync", {"mode": "full"})
    reported = queue.report_task_state(
        "protocol_sync",
        str(queued["task_id"]),
        status="completed",
        result={"processed": 10},
    )

    assert reported["status"] == "completed"
    assert queue.get_task_state("protocol_sync", str(queued["task_id"]))["result"] == {"processed": 10}


def test_media_service_supports_safe_naming() -> None:
    assert sanitize_media_name("Logo Empresa 2026!") == "logo-empresa-2026"
    assert build_media_filename("logo empresa", "archivo final.PNG").startswith("logo-empresa_")


def test_media_service_validates_and_normalizes_images() -> None:
    contents = _make_test_image_bytes()
    metadata = validate_image_payload(contents, "logo.png")
    normalized, normalized_meta = normalize_image(contents, profile="logo", output_format="PNG")

    assert metadata["format"] == "PNG"
    assert normalized
    assert normalized_meta["target_width"] == 512
    assert normalized_meta["target_height"] == 512


def test_media_service_creates_thumbnails() -> None:
    contents = _make_test_image_bytes(size=(800, 500))
    thumbnail, metadata = create_thumbnail(contents)
    assert thumbnail
    assert metadata["profile"] == "thumbnail"
    assert metadata["target_width"] <= 320
    assert metadata["target_height"] <= 320


def test_media_service_processes_and_stores_media(tmp_path, monkeypatch) -> None:
    contents = _make_test_image_bytes()
    monkeypatch.setattr(media_service_module, "MEDIA_STORAGE_ROOT", Path(tmp_path))

    stored = process_and_store_media(
        contents,
        category="logos",
        original_name="Logo Principal.png",
        profile="logo",
        output_format="PNG",
    )

    assert stored["category"] == "logos"
    assert stored["filename"].endswith(".png")
    assert Path(stored["path"]).exists()


def test_http_service_builds_headers_and_returns_json_payload() -> None:
    client = FakeHTTPClient([FakeHTTPResponse(payload={"ok": True})])
    service = BaseHTTPService(base_url="https://api.demo.test", headers={"X-App": "sipet"}, client=client)

    response = service.get("/health", headers={"Authorization": "Bearer token"})

    assert response["ok"] is True
    assert response["data"] == {"ok": True}
    assert client.calls[0]["url"] == "https://api.demo.test/health"
    assert client.calls[0]["headers"]["X-App"] == "sipet"
    assert client.calls[0]["headers"]["Authorization"] == "Bearer token"


def test_http_service_retries_before_succeeding() -> None:
    timeout_exc = http_service_module.httpx.TimeoutException("timeout") if http_service_module.httpx is not None else Exception("timeout")
    client = FakeHTTPClient([timeout_exc, FakeHTTPResponse(payload={"retry": "ok"})])
    service = BaseHTTPService(base_url="https://api.demo.test", retries=1, client=client)

    response = service.get("/retry")

    assert response["data"] == {"retry": "ok"}
    assert len(client.calls) == 2


def test_http_service_maps_remote_errors_to_http_exception() -> None:
    client = FakeHTTPClient([FakeHTTPResponse(status_code=500, payload={"error": "boom"})])
    service = BaseHTTPService(base_url="https://api.demo.test", client=client)

    try:
        service.get("/fail")
    except HTTPException as exc:
        assert exc.status_code == 502
    else:
        raise AssertionError("BaseHTTPService debe convertir errores remotos en HTTPException")


def test_ml_service_creates_standard_structure(tmp_path) -> None:
    service = ModuleMLService(tmp_path)
    service.ensure_structure()
    assert service.models_dir.exists()
    assert service.pipelines_dir.exists()
    assert service.artifacts_dir.exists()


def test_ml_service_resolves_artifact_paths_and_runs_inference(tmp_path) -> None:
    service = ModuleMLService(tmp_path)
    service.ensure_structure()

    class FakeModel:
        def predict(self, payload: object) -> object:
            return {"received": payload}

    output = service.run_inference(
        FakeModel(),
        payload=[1, 2, 3],
        preprocessor=lambda values: [item * 2 for item in values],
    )

    assert service.artifact_path("models", "score.joblib") == service.models_dir / "score.joblib"
    assert output == {"received": [2, 4, 6]}


def test_visual_editor_contract_creates_optional_grapesjs_structure(tmp_path) -> None:
    contract = VisualEditorContract(tmp_path, "demo")
    contract.ensure_structure()
    assert contract.landing_dir.exists()
    assert contract.presentations_dir.exists()
    assert contract.widgets_dir.exists()
    assert contract.forms_dir.exists()


def test_visual_editor_contract_exposes_optional_editor_config(tmp_path) -> None:
    contract = VisualEditorContract(tmp_path, "demo")
    config = contract.editor_config()
    assets = contract.build_asset_manifest()

    assert config["module_key"] == "demo"
    assert "landing" in config["scopes"]
    assert assets["js"].endswith("grapes.min.js")


def test_security_helper_hashes_and_verifies_sensitive_secret() -> None:
    hashed = hash_sensitive_secret("clave-segura")
    assert hashed
    assert verify_sensitive_secret("clave-segura", hashed) is True
    assert verify_sensitive_secret("otra-clave", hashed) is False


def test_security_helper_issues_and_verifies_temporary_token() -> None:
    issued = issue_temporary_token(subject="admin", module_key="modulo_base", purpose="zip_import")
    assert issued["token"]
    payload = verify_temporary_token(
        token=issued["token"],
        subject="admin",
        module_key="modulo_base",
        purpose="zip_import",
    )
    assert payload["sub"] == "admin"
    assert payload["purpose"] == "zip_import"


def test_security_helper_issues_and_verifies_sensitive_action_token() -> None:
    hashed = hash_sensitive_secret("confirmacion")
    issued = issue_sensitive_action_token(
        subject="admin",
        action=SENSITIVE_ACTION_MODULE_ACTIVATE,
        module_key="modulo_base",
        secret="confirmacion",
        secret_hash=hashed,
    )
    payload = verify_sensitive_action_token(
        token=issued["token"],
        subject="admin",
        action=SENSITIVE_ACTION_MODULE_ACTIVATE,
        module_key="modulo_base",
    )
    assert payload["purpose"] == SENSITIVE_ACTION_MODULE_ACTIVATE


def test_security_helper_issues_and_verifies_signed_authorization() -> None:
    issued = issue_signed_authorization(
        subject="admin",
        module_key="modulo_base",
        action="protocol_sync",
        permissions=["modulo_base.administrar"],
    )
    payload = verify_signed_authorization(
        token=issued["token"],
        subject="admin",
        module_key="modulo_base",
        action="protocol_sync",
        required_permission="modulo_base.administrar",
    )
    assert "modulo_base.administrar" in payload["permissions"]


def test_security_helper_requires_admin_role() -> None:
    require_admin_operation("admin", action="module_activate")
    try:
        require_admin_operation("usuario", action="module_activate")
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("La validacion admin debe bloquear usuarios no administrativos")


def test_modulo_base_resumen_returns_uniform_validation_error(monkeypatch) -> None:
    def _raise_validation(*, db, tenant_id: str) -> dict[str, object]:
        del db, tenant_id
        raise ValueError("tenant invalido")

    monkeypatch.setattr(api_module, "get_modulo_base_resumen", _raise_validation)

    client = _app()
    response = client.get("/api/modulo-base/resumen", headers={"x-role": "admin"})

    assert response.status_code == 422
    body = response.json()
    assert body["ok"] is False
    assert body["message"] == "tenant invalido"
    assert body["errors"][0]["type"] == "validation_error"


def test_modulo_base_resumen_returns_uniform_permission_error(monkeypatch) -> None:
    def _raise_permission(*, db, tenant_id: str) -> dict[str, object]:
        del db, tenant_id
        raise PermissionError("sin acceso")

    monkeypatch.setattr(api_module, "get_modulo_base_resumen", _raise_permission)

    client = _app()
    response = client.get("/api/modulo-base/resumen", headers={"x-role": "admin"})

    assert response.status_code == 403
    body = response.json()
    assert body["ok"] is False
    assert body["message"] == "sin acceso"
    assert body["errors"][0]["type"] == "permission_error"


def test_request_validation_handler_uses_standard_json_shape() -> None:
    app = FastAPI()
    install_module_exception_handlers(app)

    @app.get("/api/demo/{item_id}")
    def read_demo(item_id: int) -> dict[str, int]:
        return {"item_id": item_id}

    client = TestClient(app)
    response = client.get("/api/demo/not-an-int")

    assert response.status_code == 422
    body = response.json()
    assert body["ok"] is False
    assert body["message"] == "Solicitud invalida"
    assert body["errors"][0]["type"] == "validation_error"


def test_create_schema_validates_name_length() -> None:
    schema = ModuloBaseCreate(nombre="  demo base  ", descripcion=" ok ", categoria_id=1)
    assert schema.nombre == "demo base"
    assert schema.descripcion == "ok"
    assert schema.categoria_id == 1


def test_categoria_create_schema_normalizes_slug() -> None:
    schema = ModuloBaseCategoriaCreate(nombre="Categoria Demo", slug="Categoria Demo", descripcion=" x ")
    assert schema.slug == "categoria-demo"
    assert schema.descripcion == "x"


def test_update_schema_requires_at_least_one_field() -> None:
    try:
        ModuloBaseUpdate()
    except ValidationError as exc:
        assert "al menos un campo" in str(exc)
    else:
        raise AssertionError("ModuloBaseUpdate debe exigir al menos un campo")


def test_response_schema_supports_nested_category() -> None:
    schema = ModuloBaseResponse(
        id=1,
        tenant_id="tenant-a",
        nombre="Registro",
        descripcion="Detalle",
        estado=ModuloBaseEstado.ACTIVO,
        categoria_id=3,
        categoria=ModuloBaseCategoriaResponse(
            id=3,
            tenant_id="tenant-a",
            nombre="Categoria",
            slug="categoria",
            descripcion="",
        ),
        eliminado=False,
    )
    assert schema.categoria is not None
    assert schema.categoria.slug == "categoria"


def test_list_response_validates_total_consistency() -> None:
    item = ModuloBaseResponse(
        id=1,
        tenant_id="tenant-a",
        nombre="Registro",
        descripcion="",
        estado=ModuloBaseEstado.ACTIVO,
        categoria_id=1,
        eliminado=False,
    )
    schema = ModuloBaseListResponse(items=[item], total=1)
    assert schema.total == 1

    try:
        ModuloBaseListResponse(items=[item], total=0)
    except ValidationError as exc:
        assert "total no puede ser menor" in str(exc)
    else:
        raise AssertionError("ModuloBaseListResponse debe validar el total")


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


def test_base_entity_declares_reusable_primary_key() -> None:
    assert BaseEntity.__abstract__ is True
    assert BaseEntity.id.primary_key is True
    assert BaseEntity.id.index is True


def test_soft_delete_base_entity_declares_optional_soft_delete_columns() -> None:
    assert SoftDeleteBaseEntity.__abstract__ is True
    assert SoftDeleteBaseEntity.eliminado.nullable is False
    assert SoftDeleteBaseEntity.eliminado_en.nullable is True
    assert SoftDeleteBaseEntity.eliminado_por.nullable is True


def test_operational_model_inherits_tenant_audit_mixin() -> None:
    assert issubclass(ModuloBaseRegistro, TenantAuditMixin)
    assert issubclass(ModuloBaseRegistro, SoftDeleteBaseEntity)
    assert "tenant_id" in ModuloBaseRegistro.__table__.columns
    assert "id" in ModuloBaseRegistro.__table__.columns
    assert "creado_en" in ModuloBaseRegistro.__table__.columns
    assert "actualizado_en" in ModuloBaseRegistro.__table__.columns
    assert "creado_por" in ModuloBaseRegistro.__table__.columns
    assert "actualizado_por" in ModuloBaseRegistro.__table__.columns
    assert "eliminado" in ModuloBaseRegistro.__table__.columns
    assert "eliminado_en" in ModuloBaseRegistro.__table__.columns
    assert "eliminado_por" in ModuloBaseRegistro.__table__.columns


def test_operational_models_define_relationships_constraints_and_indexes() -> None:
    assert ModuloBaseRegistro.categoria.property.mapper.class_ is ModuloBaseCategoria
    assert ModuloBaseCategoria.registros.property.mapper.class_ is ModuloBaseRegistro
    assert ModuloBaseRegistro.__table__.columns["estado"].type.enums == [item.value for item in ModuloBaseEstado]
    unique_constraints = {constraint.name for constraint in ModuloBaseRegistro.__table__.constraints}
    category_constraints = {constraint.name for constraint in ModuloBaseCategoria.__table__.constraints}
    assert "uq_modulo_base_registros_tenant_nombre" in unique_constraints
    assert "ck_modulo_base_registros_nombre_len" in unique_constraints
    assert "uq_modulo_base_categorias_tenant_slug" in category_constraints
    index_names = {index.name for index in ModuloBaseRegistro.__table__.indexes}
    category_index_names = {index.name for index in ModuloBaseCategoria.__table__.indexes}
    assert "ix_modulo_base_registros_tenant_estado" in index_names
    assert "ix_modulo_base_registros_tenant_categoria" in index_names
    assert "ix_modulo_base_categorias_tenant_nombre" in category_index_names


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
