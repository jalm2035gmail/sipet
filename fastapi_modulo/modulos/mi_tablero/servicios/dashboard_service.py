from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from fastapi_modulo.modulos.mi_tablero.controladores.dashboard_security import (
    build_dashboard_security_context,
    can_view_module,
    validate_catalog_item,
)
from fastapi_modulo.modulos.mi_tablero.ml.recommender_model import recommend_modules, train_recommendation_model
from fastapi_modulo.modulos.mi_tablero.modelos.schemas import DashboardModuleSchema
from fastapi_modulo.modulos.mi_tablero.repositorios.dashboard_repository import list_available_modules
from fastapi_modulo.modulos.mi_tablero.servicios.analytics_service import build_dashboard_metrics
from fastapi_modulo.modulos.mi_tablero.servicios.preference_service import get_dashboard_preferences
from fastapi_modulo.modulos.mi_tablero.tareas.dashboard_tasks import (
    enqueue_dashboard_stats,
    get_cached_dashboard_stats,
)
from fastapi_modulo.modulos.mi_tablero.servicios.widget_service import build_default_widgets

_TEMPLATE_ENV = Environment(
    loader=FileSystemLoader(str(Path(__file__).resolve().parents[1] / "vistas")),
    autoescape=select_autoescape(["html", "xml"]),
)


def _serialize_module(module: dict) -> dict:
    return DashboardModuleSchema(
        key=str(module.get("key") or module.get("route") or "").strip(),
        label=str(module.get("label") or "Modulo").strip() or "Modulo",
        description=str(module.get("description") or "").strip(),
        route=str(module.get("route") or "").strip(),
        icon=str(module.get("icon") or "").strip(),
    ).model_dump()


def list_visible_modules(request) -> list[dict]:
    return [_serialize_module(module) for module in list_available_modules() if can_view_module(request, module)]


def get_dashboard_catalog(request) -> list[dict]:
    return list_visible_modules(request)


def get_catalog_item(request, item_key: str) -> dict:
    return validate_catalog_item(item_key, get_dashboard_catalog(request))


def get_dashboard_recommendations(request) -> list[dict]:
    visible_modules = list_visible_modules(request)
    train_recommendation_model(visible_modules, n_clusters=min(5, len(visible_modules) or 1))
    return recommend_modules(visible_modules)


def _build_dashboard_sections(modules: list[dict], preferences: dict, usage_stats: dict, security: dict) -> dict:
    preferred_widgets = sorted(
        preferences.get("widgets", []),
        key=lambda item: (int(item.get("priority_order", 0)), str(item.get("key") or "")),
    )
    visible_widget_keys = [item["key"] for item in preferred_widgets if not item.get("is_hidden")]
    favorite_keys = {item["key"] for item in preferred_widgets if item.get("is_favorite")}
    pinned_keys = {item["key"] for item in preferred_widgets if item.get("is_pinned")}
    hidden_keys = {item["key"] for item in preferred_widgets if item.get("is_hidden")}
    modules_by_key = {item["key"]: item for item in modules}
    ordered_modules = [modules_by_key[key] for key in visible_widget_keys if key in modules_by_key]
    remaining_modules = [item for item in modules if item["key"] not in visible_widget_keys and item["key"] not in hidden_keys]
    board_modules = ordered_modules + remaining_modules
    recent_source = usage_stats.get("most_used_apps", [])
    recent_items = [modules_by_key[item["item_key"]] for item in recent_source if item.get("item_key") in modules_by_key][:4] or board_modules[:4]
    favorite_items = [modules_by_key[key] for key in visible_widget_keys if key in favorite_keys and key in modules_by_key][:4]
    pinned_items = [modules_by_key[key] for key in visible_widget_keys if key in pinned_keys and key in modules_by_key][:4]
    hidden_items = [modules_by_key[key] for key in hidden_keys if key in modules_by_key][:4]
    recommended_items = recommend_modules(modules, limit=4)
    alerts = [
        {"key": "alerts_access", "label": "Revision de accesos", "description": f"{len(modules)} apps visibles para el perfil."},
        {"key": "alerts_tasks", "label": "Tareas pendientes", "description": f"{max(1, len(recommended_items))} widgets sugeridos para organizar el tablero."},
        {"key": "alerts_hidden", "label": "Apps ocultas", "description": f"{len(hidden_items)} apps ocultas disponibles para reactivar."},
    ]
    indicators = [
        {"label": "Apps visibles", "value": len(board_modules)},
        {"label": "Apps favoritas", "value": len(favorite_items)},
        {"label": "Apps fijadas", "value": len(pinned_items)},
        {"label": "Apps sugeridas", "value": len(recommended_items)},
        {"label": "Apps por rol", "value": len(security.get("user_app_access", []))},
    ]
    tasks = [
        {"key": "task_favorites", "label": "Marcar favoritas", "done": bool(favorite_items)},
        {"key": "task_dragdrop", "label": "Ordenar widgets", "done": bool(preferences.get("designer_layout", {}).get("widgets", []))},
        {"key": "task_pin", "label": "Fijar accesos clave", "done": bool(pinned_items)},
        {"key": "task_hide", "label": "Ocultar apps secundarias", "done": bool(hidden_items)},
        {"key": "task_alerts", "label": "Revisar alertas", "done": False},
    ]
    personal_stats = {
        "user_id": security.get("user_id", ""),
        "allowed_apps": len(security.get("user_app_access", [])),
        "most_used_apps": usage_stats.get("most_used_apps", []),
        "abandoned_apps": usage_stats.get("abandoned_apps", []),
        "most_used_screens": usage_stats.get("most_used_screens", []),
    }
    suggested_by_role = [modules_by_key[key] for key in security.get("user_app_access", []) if key in modules_by_key][:4]
    return {
        "favorites": favorite_items or pinned_items,
        "pinned": pinned_items,
        "pinned_keys": [item["key"] for item in pinned_items],
        "recent": recent_items,
        "hidden": hidden_items,
        "hidden_keys": [item["key"] for item in hidden_items],
        "alerts": alerts,
        "indicators": indicators,
        "tasks": tasks,
        "personal_stats": personal_stats,
        "recommended": recommended_items,
        "suggested_by_role": suggested_by_role or recommended_items,
        "ordered_modules": board_modules,
    }


def build_dashboard_payload(request) -> dict:
    visible_modules = list_visible_modules(request)
    security = build_dashboard_security_context(request)
    user_id = str(security["user_id"])
    cached_stats = get_cached_dashboard_stats(user_id)
    task_state = enqueue_dashboard_stats(user_id, visible_modules) if cached_stats is None else {"status": "cached", "task_id": None}
    preferences = get_dashboard_preferences(request).model_dump()
    sections = _build_dashboard_sections(visible_modules, preferences, cached_stats or {}, security)
    return {
        "preferences": preferences,
        "widgets": build_default_widgets(),
        "metrics": build_dashboard_metrics(visible_modules),
        "recommended_modules": recommend_modules(visible_modules),
        "usage_stats": cached_stats or {},
        "stats_job": task_state,
        "sections": sections,
        "modules": visible_modules,
    }


def build_dashboard_content(request) -> str:
    payload = build_dashboard_payload(request)
    return _TEMPLATE_ENV.get_template("mi_tablero.html").render(
        payload=payload,
        dashboard_items=payload["modules"],
    )
