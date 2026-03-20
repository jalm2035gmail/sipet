from __future__ import annotations

from fastapi_modulo.modulos.mi_tablero.modelos.schemas import (
    DashboardDesignerLayoutSchema,
    DashboardPreferenceItemUpdateSchema,
    DashboardPreferenceSchema,
    DashboardPreferenceUpdateSchema,
    DashboardWidgetMutationSchema,
    DashboardWidgetOrderSchema,
)
from fastapi_modulo.modulos.mi_tablero.repositorios.preference_repository import (
    add_user_widget,
    get_user_preferences,
    get_user_dashboard_layout,
    remove_user_widget,
    reorder_user_widgets,
    save_user_preferences,
    save_user_dashboard_layout,
    update_user_widget_preferences,
)


def get_dashboard_preferences(request) -> DashboardPreferenceSchema:
    return DashboardPreferenceSchema.model_validate(get_user_preferences(request))


def update_dashboard_preferences(request, payload: DashboardPreferenceUpdateSchema) -> DashboardPreferenceSchema:
    current = get_dashboard_preferences(request).model_dump()
    current.update(payload.model_dump())
    return DashboardPreferenceSchema.model_validate(save_user_preferences(request, current))


def update_dashboard_widget_order(request, payload: DashboardWidgetOrderSchema) -> DashboardPreferenceSchema:
    return DashboardPreferenceSchema.model_validate(reorder_user_widgets(request, payload.widgets))


def add_dashboard_widget(request, payload: DashboardWidgetMutationSchema) -> DashboardPreferenceSchema:
    current = get_dashboard_preferences(request)
    title = payload.title.strip() or payload.key.replace("_", " ").title()
    widget = {"key": payload.key, "title": title, "enabled": True}
    return DashboardPreferenceSchema.model_validate(add_user_widget(request, widget))


def remove_dashboard_widget(request, widget_key: str) -> DashboardPreferenceSchema:
    return DashboardPreferenceSchema.model_validate(remove_user_widget(request, widget_key))


def update_dashboard_item_preferences(
    request,
    payload: DashboardPreferenceItemUpdateSchema,
) -> DashboardPreferenceSchema:
    return DashboardPreferenceSchema.model_validate(
        update_user_widget_preferences(
            request,
            payload.item_key,
            payload.model_dump(),
        )
    )


def get_dashboard_designer_layout(request) -> DashboardDesignerLayoutSchema:
    return DashboardDesignerLayoutSchema.model_validate(get_user_dashboard_layout(request))


def save_dashboard_designer_layout(
    request,
    payload: DashboardDesignerLayoutSchema,
) -> DashboardDesignerLayoutSchema:
    return DashboardDesignerLayoutSchema.model_validate(save_user_dashboard_layout(request, payload.model_dump()))
