from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse


ShellRenderer = Callable[[Request, str, str], HTMLResponse]
SectionDispatcher = Callable[[Request, str], HTMLResponse | RedirectResponse]
HtmlFactory = Callable[[], str]


def create_pages_router(
    *,
    render_official_shell: ShellRenderer,
    dispatch_section_entrypoint: SectionDispatcher,
    inicio_html: HtmlFactory,
    configuracion_entrypoint: Callable[[Request], HTMLResponse | RedirectResponse],
    productos_html: HtmlFactory,
    tienda_html: HtmlFactory,
) -> APIRouter:
    router = APIRouter()

    @router.get("/multitienda/inicio", include_in_schema=False, response_class=HTMLResponse)
    def multitienda_inicio_entrypoint(request: Request):
        return render_official_shell(request, "inicio", inicio_html())

    @router.get("/multitienda", include_in_schema=False, response_class=HTMLResponse)
    def multitienda_entrypoint(request: Request):
        return render_official_shell(request, "inicio", inicio_html())

    @router.get("/multitienda/", include_in_schema=False, response_class=HTMLResponse)
    def multitienda_entrypoint_slash(request: Request):
        return render_official_shell(request, "inicio", inicio_html())

    @router.get("/multitienda/videos", include_in_schema=False, response_class=HTMLResponse)
    def multitienda_videos_entrypoint(request: Request):
        return dispatch_section_entrypoint(request, "videos")

    @router.get("/multitienda/referidos", include_in_schema=False, response_class=HTMLResponse)
    def multitienda_referidos_entrypoint(request: Request):
        return dispatch_section_entrypoint(request, "referidos")

    @router.get("/multitienda/notificaciones-pwa", include_in_schema=False, response_class=HTMLResponse)
    def multitienda_notificaciones_pwa_entrypoint(request: Request):
        return dispatch_section_entrypoint(request, "notificaciones_pwa")

    @router.get("/multitienda/reservaciones", include_in_schema=False, response_class=HTMLResponse)
    def multitienda_reservaciones_entrypoint(request: Request):
        return dispatch_section_entrypoint(request, "reservaciones")

    @router.get("/multitienda/cupones", include_in_schema=False, response_class=HTMLResponse)
    def multitienda_cupones_entrypoint(request: Request):
        return dispatch_section_entrypoint(request, "cupones")

    @router.get("/multitienda/fidelizacion", include_in_schema=False, response_class=HTMLResponse)
    def multitienda_fidelizacion_entrypoint(request: Request):
        return dispatch_section_entrypoint(request, "fidelizacion")

    @router.get("/multitienda/whatsapp", include_in_schema=False, response_class=HTMLResponse)
    def multitienda_whatsapp_entrypoint(request: Request):
        return dispatch_section_entrypoint(request, "whatsapp")

    @router.get("/multitienda/empleados", include_in_schema=False, response_class=HTMLResponse)
    def multitienda_empleados_entrypoint(request: Request):
        return dispatch_section_entrypoint(request, "empleados")

    @router.get("/multitienda/seguidores", include_in_schema=False, response_class=HTMLResponse)
    def multitienda_seguidores_entrypoint(request: Request):
        return dispatch_section_entrypoint(request, "seguidores")

    @router.get("/multitienda/proveedores", include_in_schema=False, response_class=HTMLResponse)
    def multitienda_proveedores_entrypoint(request: Request):
        return dispatch_section_entrypoint(request, "proveedores")

    @router.get("/multitienda/ia", include_in_schema=False, response_class=HTMLResponse)
    def multitienda_ia_entrypoint(request: Request):
        return dispatch_section_entrypoint(request, "ia")

    @router.get("/multitienda/institucion_financiera", include_in_schema=False, response_class=HTMLResponse)
    def multitienda_institucion_financiera_entrypoint(request: Request):
        return dispatch_section_entrypoint(request, "institucion_financiera")

    @router.get("/multitienda/apartados", include_in_schema=False, response_class=HTMLResponse)
    def multitienda_apartados_entrypoint(request: Request):
        return dispatch_section_entrypoint(request, "apartados")

    @router.get("/multitienda/subastas", include_in_schema=False, response_class=HTMLResponse)
    def multitienda_subastas_entrypoint(request: Request):
        return dispatch_section_entrypoint(request, "subastas")

    @router.get("/multitienda/crm", include_in_schema=False, response_class=HTMLResponse)
    def multitienda_crm_entrypoint(request: Request):
        return dispatch_section_entrypoint(request, "crm")

    @router.get("/multitienda/administracion_tiendas", include_in_schema=False, response_class=HTMLResponse)
    def multitienda_gestion_entrypoint(request: Request):
        return dispatch_section_entrypoint(request, "gestion")

    @router.get("/multitienda/repartidores", include_in_schema=False, response_class=HTMLResponse)
    def multitienda_repartidores_entrypoint(request: Request):
        return dispatch_section_entrypoint(request, "repartidores")

    @router.get("/multitienda/configuracion", include_in_schema=False, response_class=HTMLResponse)
    def multitienda_config_entrypoint(request: Request):
        return configuracion_entrypoint(request)

    @router.get("/configuracion", include_in_schema=False)
    @router.get("/configuracion/", include_in_schema=False)
    def multitienda_config_legacy_redirect():
        return RedirectResponse(url="/multitienda/configuracion", status_code=307)

    @router.get("/multitienda/productos", include_in_schema=False, response_class=HTMLResponse)
    def multitienda_productos_entrypoint(request: Request):
        return render_official_shell(request, "productos", productos_html())

    @router.get("/multitienda/tienda", include_in_schema=False, response_class=HTMLResponse)
    def multitienda_tienda_entrypoint(request: Request):
        return render_official_shell(request, "tienda", tienda_html())

    @router.get("/multitienda/tiendas", include_in_schema=False, response_class=HTMLResponse)
    def multitienda_tiendas_entrypoint(request: Request):
        return render_official_shell(request, "tienda", tienda_html())

    return router
