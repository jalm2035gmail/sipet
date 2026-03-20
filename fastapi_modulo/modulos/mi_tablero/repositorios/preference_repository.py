from __future__ import annotations

from copy import deepcopy

from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from fastapi_modulo.core import db as core_db
from fastapi_modulo.modulos.mi_tablero.modelos.db_models import DashboardPreference

_FALLBACK_STORE: dict[tuple[int, int], dict] = {}


def _default_preferences() -> dict:
    return {
        "theme": "system",
        "layout": "grid",
        "widgets": [],
        "designer_layout": {
            "widgets": [
                {"type": "apps", "x": 0, "y": 0, "w": 2, "h": 1},
                {"type": "alerts", "x": 2, "y": 0, "w": 2, "h": 1},
            ]
        },
    }


def _ensure_table() -> None:
    DashboardPreference.__table__.create(bind=core_db.get_engine_for_host(core_db.get_request_host()), checkfirst=True)


def _session() -> Session:
    return core_db.get_session_factory_for_host(core_db.get_request_host())()


def _coerce_int(value, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return default


def _resolve_user_id(request) -> int:
    state_user = getattr(getattr(request, "state", None), "user", None)
    if isinstance(state_user, dict):
        return _coerce_int(state_user.get("id"), 0)
    if state_user is not None:
        return _coerce_int(getattr(state_user, "id", None), 0)
    return 0


def _resolve_tenant_id(request) -> int:
    state_tenant = getattr(getattr(request, "state", None), "tenant_id", None)
    if state_tenant is not None:
        return _coerce_int(state_tenant, 0)
    return _coerce_int(getattr(getattr(request, "state", None), "tenant", None), 0)


def _base_query(db: Session, request):
    return db.query(DashboardPreference).filter(
        DashboardPreference.user_id == _resolve_user_id(request),
        DashboardPreference.tenant_id == _resolve_tenant_id(request),
    )


def _scope_key(request) -> tuple[int, int]:
    return (_resolve_user_id(request), _resolve_tenant_id(request))


def _serialize_widgets(rows: list[DashboardPreference]) -> list[dict]:
    widgets = []
    for row in rows:
        if row.item_key == "__settings__":
            continue
        widgets.append(
            {
                "key": row.item_key,
                "title": row.item_title or row.item_key.replace("_", " ").title(),
                "enabled": not bool(row.is_hidden),
                "priority_order": int(row.priority_order or 0),
                "is_favorite": bool(row.is_favorite),
                "is_pinned": bool(row.is_pinned),
                "is_hidden": bool(row.is_hidden),
            }
        )
    return widgets


def _get_settings_row(db: Session, request) -> DashboardPreference | None:
    return (
        _base_query(db, request)
        .filter(DashboardPreference.item_key == "__settings__")
        .order_by(DashboardPreference.id.desc())
        .first()
    )


def get_user_preferences(request) -> dict:
    try:
        _ensure_table()
        with _session() as db:
            rows = _base_query(db, request).order_by(DashboardPreference.priority_order.asc(), DashboardPreference.id.asc()).all()
            settings_row = _get_settings_row(db, request)
            if not rows and _scope_key(request) in _FALLBACK_STORE:
                return deepcopy(_FALLBACK_STORE[_scope_key(request)])
            preferences = _default_preferences()
            if settings_row:
                if settings_row.theme:
                    preferences["theme"] = settings_row.theme
                if settings_row.layout:
                    preferences["layout"] = settings_row.layout
            preferences["widgets"] = _serialize_widgets(rows)
            _FALLBACK_STORE[_scope_key(request)] = deepcopy(preferences)
            return preferences
    except OperationalError:
        return deepcopy(_FALLBACK_STORE.get(_scope_key(request), _default_preferences()))


def save_user_preferences(request, preferences: dict) -> dict:
    try:
        _ensure_table()
        with _session() as db:
            settings_row = _get_settings_row(db, request)
            if settings_row is None:
                settings_row = DashboardPreference(
                    user_id=_resolve_user_id(request),
                    tenant_id=_resolve_tenant_id(request),
                    item_key="__settings__",
                    item_title="Settings",
                )
                db.add(settings_row)
            settings_row.theme = preferences.get("theme") or "system"
            settings_row.layout = preferences.get("layout") or "grid"
            db.commit()
        current = get_user_preferences(request)
        current["designer_layout"] = deepcopy(preferences.get("designer_layout", current["designer_layout"]))
        _FALLBACK_STORE[_scope_key(request)] = deepcopy(current)
        return current
    except OperationalError:
        current = deepcopy(_FALLBACK_STORE.get(_scope_key(request), _default_preferences()))
        current["theme"] = preferences.get("theme", current["theme"])
        current["layout"] = preferences.get("layout", current["layout"])
        current["widgets"] = deepcopy(preferences.get("widgets", current["widgets"]))
        current["designer_layout"] = deepcopy(preferences.get("designer_layout", current["designer_layout"]))
        _FALLBACK_STORE[_scope_key(request)] = current
        return deepcopy(current)


def reorder_user_widgets(request, ordered_widget_keys: list[str]) -> dict:
    try:
        _ensure_table()
        with _session() as db:
            rows = (
                _base_query(db, request)
                .filter(DashboardPreference.item_key != "__settings__")
                .order_by(DashboardPreference.priority_order.asc(), DashboardPreference.id.asc())
                .all()
            )
            if not rows and _scope_key(request) in _FALLBACK_STORE:
                current = deepcopy(_FALLBACK_STORE[_scope_key(request)])
                widget_map = {item["key"]: item for item in current["widgets"]}
                ordered = [widget_map[key] for key in ordered_widget_keys if key in widget_map]
                remaining = [item for item in current["widgets"] if item["key"] not in ordered_widget_keys]
                current["widgets"] = ordered + remaining
                for index, widget in enumerate(current["widgets"]):
                    widget["priority_order"] = index
                _FALLBACK_STORE[_scope_key(request)] = deepcopy(current)
                return current
            row_map = {row.item_key: row for row in rows}
            ordered_rows = [row_map[key] for key in ordered_widget_keys if key in row_map]
            remaining_rows = [row for row in rows if row.item_key not in ordered_widget_keys]
            for index, row in enumerate(ordered_rows + remaining_rows):
                row.priority_order = index
            db.commit()
        return get_user_preferences(request)
    except OperationalError:
        current = get_user_preferences(request)
        widget_map = {item["key"]: item for item in current["widgets"]}
        ordered = [widget_map[key] for key in ordered_widget_keys if key in widget_map]
        remaining = [item for item in current["widgets"] if item["key"] not in ordered_widget_keys]
        current["widgets"] = ordered + remaining
        for index, widget in enumerate(current["widgets"]):
            widget["priority_order"] = index
        _FALLBACK_STORE[_scope_key(request)] = deepcopy(current)
        return current


def add_user_widget(request, widget: dict) -> dict:
    try:
        _ensure_table()
        with _session() as db:
            existing = (
                _base_query(db, request)
                .filter(DashboardPreference.item_key == str(widget.get("key") or ""))
                .first()
            )
            if existing is None:
                max_priority = (
                    _base_query(db, request)
                    .filter(DashboardPreference.item_key != "__settings__")
                    .count()
                )
                existing = DashboardPreference(
                    user_id=_resolve_user_id(request),
                    tenant_id=_resolve_tenant_id(request),
                    item_key=str(widget.get("key") or ""),
                    priority_order=max_priority,
                )
                db.add(existing)
            existing.item_title = str(widget.get("title") or "").strip() or existing.item_key.replace("_", " ").title()
            existing.is_hidden = not bool(widget.get("enabled", True))
            existing.is_favorite = bool(widget.get("is_favorite", False))
            existing.is_pinned = bool(widget.get("is_pinned", False))
            db.commit()
        current = get_user_preferences(request)
        _FALLBACK_STORE[_scope_key(request)] = deepcopy(current)
        return current
    except OperationalError:
        current = get_user_preferences(request)
        widgets = [item for item in current["widgets"] if item["key"] != str(widget.get("key") or "")]
        widgets.append(
            {
                "key": str(widget.get("key") or ""),
                "title": str(widget.get("title") or "").strip() or str(widget.get("key") or "").replace("_", " ").title(),
                "enabled": bool(widget.get("enabled", True)),
                "priority_order": len(widgets),
                "is_favorite": bool(widget.get("is_favorite", False)),
                "is_pinned": bool(widget.get("is_pinned", False)),
                "is_hidden": not bool(widget.get("enabled", True)),
            }
        )
        current["widgets"] = widgets
        _FALLBACK_STORE[_scope_key(request)] = deepcopy(current)
        return current


def remove_user_widget(request, widget_key: str) -> dict:
    try:
        _ensure_table()
        with _session() as db:
            _base_query(db, request).filter(DashboardPreference.item_key == str(widget_key or "")).delete()
            db.commit()
        current = get_user_preferences(request)
        _FALLBACK_STORE[_scope_key(request)] = deepcopy(current)
        return current
    except OperationalError:
        current = get_user_preferences(request)
        current["widgets"] = [item for item in current["widgets"] if item["key"] != str(widget_key or "")]
        _FALLBACK_STORE[_scope_key(request)] = deepcopy(current)
        return current


def update_user_widget_preferences(request, item_key: str, updates: dict) -> dict:
    try:
        _ensure_table()
        with _session() as db:
            existing = (
                _base_query(db, request)
                .filter(DashboardPreference.item_key == str(item_key or ""))
                .first()
            )
            if existing is None:
                existing = DashboardPreference(
                    user_id=_resolve_user_id(request),
                    tenant_id=_resolve_tenant_id(request),
                    item_key=str(item_key or ""),
                    item_title=str(item_key or "").replace("_", " ").title(),
                    priority_order=int(updates.get("priority_order", 0)),
                )
                db.add(existing)
            existing.is_favorite = bool(updates.get("is_favorite", existing.is_favorite))
            existing.is_pinned = bool(updates.get("is_pinned", existing.is_pinned))
            existing.is_hidden = bool(updates.get("is_hidden", existing.is_hidden))
            existing.priority_order = int(updates.get("priority_order", existing.priority_order or 0))
            db.commit()
        current = get_user_preferences(request)
        _FALLBACK_STORE[_scope_key(request)] = deepcopy(current)
        return current
    except OperationalError:
        current = get_user_preferences(request)
        widgets = current["widgets"]
        match = next((item for item in widgets if item["key"] == str(item_key or "")), None)
        if match is None:
            match = {
                "key": str(item_key or ""),
                "title": str(item_key or "").replace("_", " ").title(),
                "enabled": not bool(updates.get("is_hidden", False)),
                "priority_order": int(updates.get("priority_order", 0)),
                "is_favorite": False,
                "is_pinned": False,
                "is_hidden": False,
            }
            widgets.append(match)
        match["is_favorite"] = bool(updates.get("is_favorite", match["is_favorite"]))
        match["is_pinned"] = bool(updates.get("is_pinned", match["is_pinned"]))
        match["is_hidden"] = bool(updates.get("is_hidden", match["is_hidden"]))
        match["enabled"] = not match["is_hidden"]
        match["priority_order"] = int(updates.get("priority_order", match["priority_order"]))
        widgets.sort(key=lambda item: (int(item.get("priority_order", 0)), item["key"]))
        _FALLBACK_STORE[_scope_key(request)] = deepcopy(current)
        return current


def clear_user_preferences(request) -> None:
    try:
        _ensure_table()
        with _session() as db:
            _base_query(db, request).delete()
            db.commit()
    except OperationalError:
        _FALLBACK_STORE.pop(_scope_key(request), None)


def get_user_dashboard_layout(request) -> dict:
    current = get_user_preferences(request)
    return deepcopy(current.get("designer_layout", _default_preferences()["designer_layout"]))


def save_user_dashboard_layout(request, layout: dict) -> dict:
    current = get_user_preferences(request)
    current["designer_layout"] = deepcopy(layout)
    _FALLBACK_STORE[_scope_key(request)] = deepcopy(current)
    return deepcopy(current["designer_layout"])
