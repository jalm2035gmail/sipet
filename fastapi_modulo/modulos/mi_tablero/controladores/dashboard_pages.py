from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from fastapi_modulo.modulos.mi_tablero.controladores.dashboard_security import require_dashboard_page_access
from fastapi_modulo.modulos.mi_tablero.repositorios.dashboard_repository import list_available_modules
from fastapi_modulo.modulos.mi_tablero.servicios.dashboard_service import build_dashboard_content


router = APIRouter()


@router.get("/mi-tablero", response_class=HTMLResponse)
def dashboard_page(request: Request):
    dashboard_module = next((item for item in list_available_modules() if str(item.get("route") or "").strip() == "/mi-tablero"), None)
    require_dashboard_page_access(request, dashboard_module)
    from fastapi_modulo import main as core

    return core.render_backend_page(
        request,
        title="Mi tablero",
        description="Resumen personal y accesos directos.",
        content=build_dashboard_content(request),
        hide_floating_actions=True,
        show_page_header=False,
    )
