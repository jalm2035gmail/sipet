import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.concurrency import run_in_threadpool
import asyncio

from fastapi_modulo.modulos.notificaciones.controladores.conversaciones import (
    ensure_tables_once,
    router as conversaciones_router,
)
from fastapi_modulo.modulos.notificaciones.modelos.global_notifications_service import (
    notifications_summary,
    mark_notification_read,
    mark_all_notifications_read,
)
from fastapi_modulo.modulos_sipet.web.controladores.backend_shell import render_backend_page

router = APIRouter()
router.include_router(conversaciones_router)

_MODULE_ROOT = Path(__file__).parent.parent
_TEMPLATE_PATH = _MODULE_ROOT / "vistas" / "conversaciones.html"
_ASSET_FILES: dict[str, Path] = {
    "conversaciones.css": _MODULE_ROOT / "static" / "css" / "conversaciones.css",
    "conversaciones.js":  _MODULE_ROOT / "static" / "js"  / "conversaciones.js",
}

# Tipos MIME explícitos para los assets estáticos
_ASSET_MEDIA_TYPES: dict[str, str] = {
    "conversaciones.css": "text/css; charset=utf-8",
    "conversaciones.js":  "application/javascript; charset=utf-8",
}

# ---------------------------------------------------------------------------
# Inicialización única al cargar el módulo
# Llama ensure_tables_once() aquí para que las tablas existan antes de que
# llegue cualquier request, sin repetir DDL en cada endpoint.
# ---------------------------------------------------------------------------
ensure_tables_once()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_template() -> str:
    try:
        return _TEMPLATE_PATH.read_text(encoding="utf-8")
    except OSError:
        return "<p>No se pudo cargar la vista de notificaciones.</p>"


def _resolve_asset(filename: str) -> Optional[Path]:
    """Devuelve el Path del asset si existe y el nombre es conocido."""
    name = str(filename or "").strip()
    path = _ASSET_FILES.get(name)
    if path and path.exists():
        return path
    return None


# ---------------------------------------------------------------------------
# Assets estáticos
# ---------------------------------------------------------------------------

@router.get("/notificaciones/assets/{filename}", include_in_schema=False)
def notificaciones_asset(filename: str, request: Request) -> FileResponse:
    path = _resolve_asset(filename)
    if not path:
        raise HTTPException(status_code=404, detail="Recurso no encontrado")
    return FileResponse(
        path=str(path),
        media_type=_ASSET_MEDIA_TYPES.get(filename, "application/octet-stream"),
    )


# ---------------------------------------------------------------------------
# Vistas HTML
# ---------------------------------------------------------------------------

@router.get("/notificaciones", response_class=HTMLResponse)
def notificaciones_page(request: Request) -> HTMLResponse:
    return render_backend_page(
        request,
        title="Conversaciones",
        description="Chat IA AVAN con RAG documental y fuentes citadas.",
        content=_load_template(),
        hide_floating_actions=True,
        show_page_header=True,
    )


@router.get("/conversaciones", response_class=HTMLResponse)
def conversaciones_page(request: Request) -> HTMLResponse:
    return notificaciones_page(request)


# ---------------------------------------------------------------------------
# API REST — notificaciones globales
# Registradas aquí para centralizar todas las rutas del módulo en un solo
# router, evitando importaciones circulares con global_notifications_service.
# ---------------------------------------------------------------------------

@router.get("/api/v1/notificaciones/summary")
def api_notifications_summary(request: Request):
    return notifications_summary(request)


@router.post("/api/v1/notificaciones/read")
def api_mark_read(request: Request):
    return mark_notification_read(request)


@router.post("/api/v1/notificaciones/read-all")
def api_mark_all_read(request: Request):
    return mark_all_notifications_read(request)


# ---------------------------------------------------------------------------
# SSE — conteo de no leídos en tiempo real
# Reemplaza el polling periódico del frontend (setInterval en conversaciones.js).
# El cliente se conecta a este endpoint con:
#   const es = new EventSource('/api/v1/notificaciones/stream');
#   es.onmessage = (e) => { const { unread } = JSON.parse(e.data); ... };
# ---------------------------------------------------------------------------

@router.get("/api/v1/notificaciones/stream", include_in_schema=False)
async def notifications_stream(request: Request) -> StreamingResponse:
    """
    Server-Sent Events: emite el conteo de no leídas cada 15 segundos.
    El cliente solo necesita reconectarse si cierra la pestaña; el navegador
    lo reconecta automáticamente si la conexión se corta.
    """
    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break

                # Ejecuta la consulta DB en un thread para no bloquear el event loop
                response = await run_in_threadpool(notifications_summary, request)
                body = response.body.decode("utf-8") if hasattr(response, "body") else "{}"

                yield f"data: {body}\n\n"
                await asyncio.sleep(15)
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # Desactiva el buffer de Nginx
            "Connection": "keep-alive",
        },
    )
