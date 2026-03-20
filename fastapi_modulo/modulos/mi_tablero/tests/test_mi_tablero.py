from pathlib import Path

import pytest
import bcrypt
from fastapi import HTTPException
from jose import jwt

from fastapi_modulo.modulos.mi_tablero.__manifest__ import MANIFEST
from fastapi_modulo.modulos.mi_tablero.controladores.dashboard_api import (
    delete_widget_remove,
    export_dashboard_excel,
    export_dashboard_pdf,
    get_catalog,
    get_dashboard_layout,
    get_dashboard_thumbnail,
    get_external_indicator,
    get_preferences,
    get_recommendations,
    get_widget_icon,
    open_dashboard_item,
    patch_preference_item,
    post_dashboard_layout,
    post_preferences,
    post_widget_add,
    put_widget_order,
)
from fastapi_modulo.modulos.mi_tablero.controladores.dashboard_pages import dashboard_page
from fastapi_modulo.modulos.mi_tablero.controladores.dashboard_security import (
    build_dashboard_security_context,
    can_view_module,
    require_dashboard_page_access,
    validate_catalog_item,
    verify_dashboard_password,
)
from fastapi_modulo.modulos.mi_tablero.modelos.schemas import (
    DashboardDesignerLayoutSchema,
    DashboardPreferenceItemUpdateSchema,
    DashboardPreferenceUpdateSchema,
    DashboardWidgetMutationSchema,
    DashboardWidgetOrderSchema,
)
from fastapi_modulo.modulos.mi_tablero.repositorios.preference_repository import clear_user_preferences
from fastapi_modulo.modulos.mi_tablero.ml.recommender_model import (
    load_recommendation_model,
    recommend_modules,
    train_recommendation_model,
)
from fastapi_modulo.modulos.mi_tablero.reports.dashboard_report import generate_dashboard_pdf
from fastapi_modulo.modulos.mi_tablero.reports.dashboard_report import generate_dashboard_excel
from fastapi_modulo.modulos.mi_tablero.servicios.analytics_service import compute_usage
from fastapi_modulo.modulos.mi_tablero.servicios.dashboard_service import build_dashboard_content, build_dashboard_payload
from fastapi_modulo.modulos.mi_tablero.servicios.integration_service import fetch_external_indicator
from fastapi_modulo.modulos.mi_tablero.servicios.widget_service import generate_dashboard_thumbnail, generate_widget_icon


class _Request:
    headers = {}

    class state:
        user = {
            "id": "tester",
            "allowed_apps": ["CRM"],
            "allowed_screens": ["crm", "sales"],
            "is_superadmin": False,
        }


def test_manifest_sequence_is_001() -> None:
    assert MANIFEST["sequence"] == "001"
    assert MANIFEST["name"] == "mi_tablero"
    assert "repositories" in MANIFEST["structure"]
    assert "models" in MANIFEST["structure"]


def test_architecture_paths_exist() -> None:
    base_path = Path(__file__).resolve().parents[1]
    expected_paths = [
        "controladores/dashboard_pages.py",
        "controladores/dashboard_api.py",
        "controladores/dashboard_security.py",
        "servicios/dashboard_service.py",
        "servicios/preference_service.py",
        "servicios/analytics_service.py",
        "servicios/widget_service.py",
        "repositorios/dashboard_repository.py",
        "repositorios/preference_repository.py",
        "modelos/db_models.py",
        "modelos/schemas.py",
        "modelos/enums.py",
        "tareas/dashboard_tasks.py",
        "ml/recommender_model.py",
        "reports/dashboard_report.py",
        "vistas/mi_tablero.html",
        "static/css",
        "static/js",
        "static/widgets",
        "vistas/widgets",
    ]
    for relative_path in expected_paths:
        assert (base_path / relative_path).exists()


def test_dashboard_content_renders_visible_modules(monkeypatch) -> None:
    import fastapi_modulo.modulos.mi_tablero.servicios.dashboard_service as service

    monkeypatch.setattr(
        service,
        "list_available_modules",
        lambda: [
            {"key": "mi_tablero", "route": "/mi-tablero", "enabled": True, "label": "Mi tablero", "description": "Propio"},
            {"key": "crm", "route": "/crm", "enabled": True, "label": "CRM", "description": "Clientes", "app_access_name": "CRM"},
            {"key": "auditoria", "route": "/auditoria", "enabled": False, "label": "Auditoria", "description": "Control"},
        ],
    )

    html = build_dashboard_content(_Request())

    assert "/crm" in html
    assert "Clientes" in html
    assert "/auditoria" not in html


def test_dashboard_payload_includes_architecture_layers(monkeypatch) -> None:
    class _Core:
        @staticmethod
        def _get_user_app_access(_request):
            return ["CRM"]

        @staticmethod
        def list_modules_payload():
            return [
                {"key": "mi_tablero", "route": "/mi-tablero", "enabled": True, "label": "Mi tablero"},
                {"key": "crm", "route": "/crm", "enabled": True, "label": "CRM", "description": "Clientes", "app_access_name": "CRM"},
            ]

        @staticmethod
        def is_superadmin(_request):
            return False

    import fastapi_modulo.modulos.mi_tablero.servicios.dashboard_service as service

    monkeypatch.setattr(service, "list_available_modules", _Core.list_modules_payload)
    monkeypatch.setattr(service, "get_cached_dashboard_stats", lambda user_id: {"user_id": user_id, "total_items": 1})
    monkeypatch.setattr(service, "enqueue_dashboard_stats", lambda user_id, modules: {"status": "cached", "task_id": None})
    payload = build_dashboard_payload(_Request())

    assert payload["metrics"]["total_modules"] == 1
    assert payload["preferences"]["layout"] == "grid"
    assert payload["modules"][0]["route"] == "/crm"
    assert payload["usage_stats"]["total_items"] == 1
    assert "favorites" in payload["sections"]
    assert "pinned" in payload["sections"]
    assert "hidden" in payload["sections"]
    assert "ordered_modules" in payload["sections"]
    assert "recommended" in payload["sections"]
    assert "suggested_by_role" in payload["sections"]


def test_dashboard_api_endpoints(monkeypatch) -> None:
    import asyncio
    import fastapi_modulo.modulos.mi_tablero.controladores.dashboard_api as api

    clear_user_preferences(_Request())
    monkeypatch.setattr(api, "get_dashboard_catalog", lambda request: [{"key": "crm", "route": "/crm", "label": "CRM"}])
    monkeypatch.setattr(api, "get_dashboard_recommendations", lambda request: [{"key": "crm", "route": "/crm", "label": "CRM"}])
    monkeypatch.setattr(
        api,
        "build_dashboard_payload",
        lambda request: {
            "metrics": {"total_modules": 1},
            "widgets": [{"key": "quick_access"}],
            "modules": [{"label": "CRM", "route": "/crm"}],
            "preferences": {"designer_layout": {"widgets": []}},
        },
    )
    monkeypatch.setattr(
        api,
        "fetch_external_indicator",
        lambda url: __import__("asyncio").sleep(0, result={"url": url, "status_code": 200, "payload": {"value": 1}}),
    )

    catalog = asyncio.run(get_catalog(_Request()))
    preferences = asyncio.run(get_preferences(_Request()))
    recommendations = asyncio.run(get_recommendations(_Request()))
    layout = asyncio.run(get_dashboard_layout(_Request()))
    pdf_response = asyncio.run(export_dashboard_pdf(_Request()))
    excel_response = asyncio.run(export_dashboard_excel(_Request()))
    icon_response = asyncio.run(get_widget_icon(_Request(), "apps"))
    thumbnail_response = asyncio.run(get_dashboard_thumbnail(_Request()))
    external_response = asyncio.run(get_external_indicator(_Request(), "https://example.com/api"))
    open_response = asyncio.run(open_dashboard_item(_Request(), "crm"))

    assert catalog.body == b'[{"key":"crm","description":""}]'
    assert b'"designer_layout"' in preferences.body
    assert recommendations.body == b'[{"key":"crm","description":""}]'
    assert b'"widgets"' in layout.body
    assert pdf_response.media_type == "application/pdf"
    assert excel_response.media_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert icon_response.media_type == "image/png"
    assert thumbnail_response.media_type == "image/png"
    assert external_response.body == b'{"url":"https://example.com/api","status_code":200,"payload":{"value":1}}'
    assert open_response.headers["location"] == "/crm"


def test_dashboard_preferences_crud() -> None:
    import asyncio
    import fastapi_modulo.modulos.mi_tablero.controladores.dashboard_api as api

    request = _Request()
    clear_user_preferences(request)
    api.get_dashboard_catalog = lambda _request: [{"key": "crm", "route": "/crm", "label": "CRM"}]

    response = asyncio.run(
        post_preferences(
            request,
            DashboardPreferenceUpdateSchema(theme="light", layout="list"),
        )
    )
    assert b'"theme":"light"' in response.body
    assert b'"layout":"list"' in response.body

    response = asyncio.run(
        post_widget_add(
            request,
            DashboardWidgetMutationSchema(key="crm", title="Ventas"),
        )
    )
    assert b'"key":"crm"' in response.body

    response = asyncio.run(
        put_widget_order(
            request,
            DashboardWidgetOrderSchema(widgets=["crm"]),
        )
    )
    assert b'"widgets":[{"key":"crm","title":"Ventas","enabled":true,"priority_order":0' in response.body

    response = asyncio.run(
        patch_preference_item(
            request,
            DashboardPreferenceItemUpdateSchema(item_key="crm", is_favorite=True, priority_order=0),
        )
    )
    assert b'"is_favorite":true' in response.body

    response = asyncio.run(
        post_dashboard_layout(
            request,
            DashboardDesignerLayoutSchema(widgets=[{"type": "apps", "x": 0, "y": 0}, {"type": "alerts", "x": 2, "y": 0}]),
        )
    )
    assert b'"type":"alerts"' in response.body

    response = asyncio.run(
        delete_widget_remove(
            request,
            DashboardWidgetMutationSchema(key="crm"),
        )
    )
    assert b'"widgets":[]' in response.body


def test_dashboard_security_supports_jwt_and_password_hashing() -> None:
    token = jwt.encode(
        {
            "sub": "jwt-user",
            "allowed_apps": ["CRM"],
            "allowed_screens": ["crm"],
            "is_superadmin": False,
        },
        "dashboard-dev-secret",
        algorithm="HS256",
    )

    class _JwtRequest(_Request):
        headers = {"authorization": f"Bearer {token}"}

    security = build_dashboard_security_context(_JwtRequest())
    assert security["user_id"] == "jwt-user"
    assert "CRM" in security["user_app_access"]
    assert "crm" in security["user_screen_access"]

    hashed = bcrypt.hashpw(b"secret123", bcrypt.gensalt()).decode("utf-8")
    assert verify_dashboard_password("secret123", hashed) is True


def test_dashboard_security_enforces_app_screen_and_catalog() -> None:
    request = _Request()

    allowed_module = {
        "key": "crm",
        "route": "/crm",
        "enabled": True,
        "label": "CRM",
        "app_access_name": "CRM",
        "screen_access_name": "crm",
    }
    blocked_module = {
        "key": "auditoria",
        "route": "/auditoria",
        "enabled": True,
        "label": "Auditoria",
        "app_access_name": "Auditoria",
        "screen_access_name": "auditoria",
    }

    assert can_view_module(request, allowed_module) is True
    assert can_view_module(request, blocked_module) is False
    assert validate_catalog_item("crm", [allowed_module])["route"] == "/crm"
    with pytest.raises(HTTPException):
        validate_catalog_item("ruta-libre", [allowed_module])


def test_dashboard_page_returns_404_without_access(monkeypatch) -> None:
    import fastapi_modulo.modulos.mi_tablero.controladores.dashboard_pages as pages

    class _BlockedRequest:
        headers = {}

        class state:
            user = {
                "id": "blocked",
                "allowed_apps": [],
                "allowed_screens": [],
                "is_superadmin": False,
            }

    monkeypatch.setattr(
        pages,
        "list_available_modules",
        lambda: [
            {
                "key": "mi_tablero",
                "route": "/mi-tablero",
                "enabled": True,
                "label": "Mi tablero",
                "app_access_name": "CRM",
                "screen_access_name": "crm",
            }
        ],
    )

    with pytest.raises(HTTPException) as exc:
        dashboard_page(_BlockedRequest())

    assert exc.value.status_code == 404


def test_dashboard_permissions() -> None:
    request = _Request()
    assert can_view_module(
        request,
        {
            "key": "crm",
            "route": "/crm",
            "enabled": True,
            "app_access_name": "CRM",
            "screen_access_name": "crm",
        },
    ) is True
    with pytest.raises(HTTPException):
        validate_catalog_item("invalid", [{"key": "crm", "route": "/crm"}])


def test_dashboard_item_preferences_schema_validates_payload() -> None:
    payload = DashboardPreferenceItemUpdateSchema(item_key="crm", is_favorite=True, priority_order=2)
    assert payload.item_key == "crm"
    with pytest.raises(Exception):
        DashboardPreferenceItemUpdateSchema(item_key="", priority_order=-1)


def test_dashboard_preferences() -> None:
    request = _Request()
    clear_user_preferences(request)
    import asyncio

    response = asyncio.run(
        post_preferences(
            request,
            DashboardPreferenceUpdateSchema(theme="light", layout="list"),
        )
    )
    assert b'"theme":"light"' in response.body


def test_dashboard_stats_task_caches_results(monkeypatch) -> None:
    from fastapi_modulo.modulos.mi_tablero.tareas import dashboard_tasks

    class _Redis:
        def __init__(self):
            self.store = {}

        def set(self, key, value):
            self.store[key] = value

        def get(self, key):
            return self.store.get(key)

    fake_redis = _Redis()
    monkeypatch.setattr(dashboard_tasks, "get_dashboard_redis", lambda: fake_redis)

    stats = dashboard_tasks.compute_user_dashboard_stats(
        "tester",
        [{"key": "crm", "route": "/crm"}, {"key": "crm", "route": "/crm"}],
    )

    assert stats["most_used_apps"][0]["item_key"] == "crm"
    assert dashboard_tasks.get_cached_dashboard_stats("tester")["total_items"] == 2


def test_pandas_numpy_analytics_build_usage_summary() -> None:
    stats = compute_usage(
        "tester",
        [
            {"key": "crm", "route": "/crm", "screen_access_name": "crm-home", "widget_key": "crm_widget", "recommended_weight": 1.5},
            {"key": "crm", "route": "/crm", "screen_access_name": "crm-home", "widget_key": "crm_widget", "recommended_weight": 1.5},
            {"key": "mkt", "route": "/mkt", "screen_access_name": "mkt-home", "widget_key": "mkt_widget", "recommended_weight": 0.5},
        ],
    )

    assert stats["most_used_apps"][0]["item_key"] == "crm"
    assert stats["most_used_screens"][0]["screen_key"] == "crm-home"
    assert stats["recommended_widgets"][0]["widget_key"] == "crm_widget"
    assert stats["abandoned_apps"][0]["item_key"] == "mkt"


def test_sklearn_recommendation_model_trains_and_persists(tmp_path) -> None:
    model_path = tmp_path / "dashboard_model.pkl"
    modules = [
        {"key": "crm", "route": "/crm", "label": "CRM", "description": "Clientes", "usage_count": 10, "is_favorite": True},
        {"key": "mkt", "route": "/mkt", "label": "MKT", "description": "Campanas", "usage_count": 3},
        {"key": "pld", "route": "/pld", "label": "PLD", "description": "Riesgo", "usage_count": 8, "is_pinned": True},
    ]

    result = train_recommendation_model(modules, n_clusters=2, model_path=model_path)

    assert result["status"] == "trained"
    assert model_path.exists()
    assert load_recommendation_model(model_path) is not None

    ranked = recommend_modules(modules, limit=2)
    assert len(ranked) == 2


def test_dashboard_recommendations() -> None:
    ranked = recommend_modules(
        [
            {"key": "crm", "route": "/crm", "label": "CRM", "description": "Clientes", "is_favorite": True},
            {"key": "mkt", "route": "/mkt", "label": "MKT", "description": ""},
        ],
        limit=1,
    )
    assert ranked[0]["key"] == "crm"


def test_dashboard_template_renders_grapes_editor(monkeypatch) -> None:
    import fastapi_modulo.modulos.mi_tablero.servicios.dashboard_service as service

    monkeypatch.setattr(service, "list_available_modules", lambda: [{"key": "crm", "route": "/crm", "enabled": True, "label": "CRM"}])
    monkeypatch.setattr(
        service,
        "get_cached_dashboard_stats",
        lambda user_id: {
            "user_id": user_id,
            "total_items": 1,
            "most_used_apps": [{"item_key": "crm", "usage_count": 1}],
            "most_used_screens": [{"screen_key": "crm", "usage_count": 1}],
            "abandoned_apps": [],
        },
    )
    monkeypatch.setattr(service, "enqueue_dashboard_stats", lambda user_id, modules: {"status": "cached", "task_id": None})

    html = build_dashboard_content(_Request())

    assert "dashboard-layout-editor" in html
    assert "/static/vendor/grapesjs/grapes.min.js" in html
    assert 'href="/dashboard/open/crm"' in html
    assert "Favoritas y recientes" in html
    assert "Indicadores" in html
    assert "Orden actual" in html
    assert "Apps ocultas" in html
    assert "Apps mas usadas" in html


def test_dashboard_reportlab_generates_pdf() -> None:
    pdf_bytes = generate_dashboard_pdf(
        "tester",
        {
            "metrics": {"total_modules": 1},
            "widgets": [{"key": "quick_access"}],
            "modules": [{"label": "CRM", "route": "/crm"}],
        },
    )

    assert pdf_bytes.startswith(b"%PDF")


def test_dashboard_excel_generates_workbook() -> None:
    excel_bytes = generate_dashboard_excel(
        "tester",
        {
            "metrics": {"total_modules": 1},
            "widgets": [{"key": "quick_access"}],
            "stats_job": {"status": "cached"},
            "modules": [{"label": "CRM", "route": "/crm"}],
            "usage_stats": {
                "most_used_apps": [{"item_key": "crm", "usage_count": 3}],
                "most_used_screens": [{"screen_key": "crm-home", "usage_count": 3}],
            },
        },
    )

    assert excel_bytes[:2] == b"PK"


def test_pillow_generates_widget_icon_and_thumbnail() -> None:
    icon_bytes = generate_widget_icon("apps")
    thumbnail_bytes = generate_dashboard_thumbnail({"widgets": [{"type": "apps", "x": 0, "y": 0}]})

    assert icon_bytes.startswith(b"\x89PNG")
    assert thumbnail_bytes.startswith(b"\x89PNG")


def test_httpx_external_integration(monkeypatch) -> None:
    import asyncio
    import fastapi_modulo.modulos.mi_tablero.servicios.integration_service as integration_service

    class _Response:
        status_code = 200
        headers = {"content-type": "application/json"}

        @staticmethod
        def raise_for_status():
            return None

        @staticmethod
        def json():
            return {"ok": True}

    class _Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, url):
            assert url == "https://example.com/api"
            return _Response()

    monkeypatch.setattr(integration_service.httpx, "AsyncClient", lambda timeout=5.0: _Client())

    payload = asyncio.run(fetch_external_indicator("https://example.com/api"))

    assert payload["status_code"] == 200
    assert payload["payload"]["ok"] is True
