from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response

from fastapi_modulo.modulos.mi_tablero.controladores.dashboard_security import (
    require_dashboard_user,
    validate_catalog_item,
)
from fastapi_modulo.modulos.mi_tablero.modelos.schemas import (
    DashboardDesignerLayoutSchema,
    DashboardPreferenceItemUpdateSchema,
    DashboardPreferenceUpdateSchema,
    DashboardWidgetMutationSchema,
    DashboardWidgetOrderSchema,
)
from fastapi_modulo.modulos.mi_tablero.reports.dashboard_report import generate_dashboard_excel, generate_dashboard_pdf
from fastapi_modulo.modulos.mi_tablero.servicios.integration_service import fetch_external_indicator
from fastapi_modulo.modulos.mi_tablero.servicios.dashboard_service import (
    build_dashboard_payload,
    get_dashboard_catalog,
    get_dashboard_recommendations,
)
from fastapi_modulo.modulos.mi_tablero.servicios.preference_service import (
    add_dashboard_widget,
    get_dashboard_designer_layout,
    get_dashboard_preferences,
    remove_dashboard_widget,
    save_dashboard_designer_layout,
    update_dashboard_item_preferences,
    update_dashboard_preferences,
    update_dashboard_widget_order,
)
from fastapi_modulo.modulos.mi_tablero.servicios.widget_service import (
    generate_dashboard_thumbnail,
    generate_widget_icon,
)


router = APIRouter(tags=["mi_tablero"])


@router.get("/api/mi-tablero", response_class=JSONResponse)
async def dashboard_api(request: Request):
    require_dashboard_user(request)
    return JSONResponse(build_dashboard_payload(request))


@router.get("/api/dashboard/catalog", response_class=JSONResponse)
async def get_catalog(request: Request):
    require_dashboard_user(request)
    return JSONResponse(
        [
            {
                "key": item["key"],
                "description": item.get("description", ""),
            }
            for item in get_dashboard_catalog(request)
        ]
    )


@router.get("/api/dashboard/preferences", response_class=JSONResponse)
async def get_preferences(request: Request):
    require_dashboard_user(request)
    return JSONResponse(get_dashboard_preferences(request).model_dump())


@router.post("/api/dashboard/preferences", response_class=JSONResponse)
async def post_preferences(request: Request, payload: DashboardPreferenceUpdateSchema):
    require_dashboard_user(request)
    return JSONResponse(update_dashboard_preferences(request, payload).model_dump())


@router.get("/api/dashboard/layout", response_class=JSONResponse)
async def get_dashboard_layout(request: Request):
    require_dashboard_user(request)
    return JSONResponse(get_dashboard_designer_layout(request).model_dump())


@router.post("/api/dashboard/layout", response_class=JSONResponse)
async def post_dashboard_layout(request: Request, payload: DashboardDesignerLayoutSchema):
    require_dashboard_user(request)
    return JSONResponse(save_dashboard_designer_layout(request, payload).model_dump())


@router.patch("/api/dashboard/preferences/item", response_class=JSONResponse)
async def patch_preference_item(request: Request, payload: DashboardPreferenceItemUpdateSchema):
    require_dashboard_user(request)
    validate_catalog_item(payload.item_key, get_dashboard_catalog(request))
    return JSONResponse(update_dashboard_item_preferences(request, payload).model_dump())


@router.put("/api/dashboard/preferences/order", response_class=JSONResponse)
async def put_widget_order(request: Request, payload: DashboardWidgetOrderSchema):
    require_dashboard_user(request)
    catalog = get_dashboard_catalog(request)
    for widget_key in payload.widgets:
        validate_catalog_item(widget_key, catalog)
    return JSONResponse(update_dashboard_widget_order(request, payload).model_dump())


@router.post("/api/dashboard/widget/add", response_class=JSONResponse)
async def post_widget_add(request: Request, payload: DashboardWidgetMutationSchema):
    require_dashboard_user(request)
    validate_catalog_item(payload.key, get_dashboard_catalog(request))
    return JSONResponse(add_dashboard_widget(request, payload).model_dump())


@router.delete("/api/dashboard/widget/remove", response_class=JSONResponse)
async def delete_widget_remove(request: Request, payload: DashboardWidgetMutationSchema):
    require_dashboard_user(request)
    return JSONResponse(remove_dashboard_widget(request, payload.key).model_dump())


@router.get("/api/dashboard/recommendations", response_class=JSONResponse)
async def get_recommendations(request: Request):
    require_dashboard_user(request)
    return JSONResponse(
        [
            {
                "key": item["key"],
                "description": item.get("description", ""),
            }
            for item in get_dashboard_recommendations(request)
        ]
    )


@router.get("/dashboard/open/{item_key}")
async def open_dashboard_item(request: Request, item_key: str):
    require_dashboard_user(request)
    item = validate_catalog_item(item_key, get_dashboard_catalog(request))
    return RedirectResponse(url=item["route"], status_code=307)


@router.get("/api/dashboard/export/pdf")
async def export_dashboard_pdf(request: Request):
    security = require_dashboard_user(request)
    pdf_bytes = generate_dashboard_pdf(str(security["user_id"]), build_dashboard_payload(request))
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="dashboard_{security["user_id"]}.pdf"'},
    )


@router.get("/api/dashboard/export/excel")
async def export_dashboard_excel(request: Request):
    security = require_dashboard_user(request)
    excel_bytes = generate_dashboard_excel(str(security["user_id"]), build_dashboard_payload(request))
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="dashboard_{security["user_id"]}.xlsx"'},
    )


@router.get("/api/dashboard/widget/icon/{widget_type}")
async def get_widget_icon(request: Request, widget_type: str):
    require_dashboard_user(request)
    return Response(content=generate_widget_icon(widget_type), media_type="image/png")


@router.get("/api/dashboard/thumbnail")
async def get_dashboard_thumbnail(request: Request):
    require_dashboard_user(request)
    layout = get_dashboard_designer_layout(request).model_dump()
    return Response(content=generate_dashboard_thumbnail(layout), media_type="image/png")


@router.get("/api/dashboard/external")
async def get_external_indicator(request: Request, url: str):
    require_dashboard_user(request)
    return JSONResponse(await fetch_external_indicator(url))
