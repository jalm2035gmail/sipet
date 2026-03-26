from __future__ import annotations
from pathlib import Path
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi_modulo.core.db import SessionLocal
from fastapi_modulo.modulos_sipet.web.servicios.module_tools import render_backend_page_html
from fastapi_modulo.modulos.reservaciones.modelos.db_models import ensure_reservaciones_schema
from fastapi_modulo.modulos.reservaciones.modelos.schemas import (
    CitaCreate, CitaUpdate, EjecutivoCreate, EjecutivoUpdate, TipoCitaCreate,
)
from fastapi_modulo.modulos.reservaciones.modelos import store

MODULE_DIR = Path(__file__).resolve().parents[1]
VIEWS_DIR = MODULE_DIR / "vistas"

try:
    ensure_reservaciones_schema()
except Exception as _e:
    print(f"[reservaciones] schema init warning: {_e}")

router = APIRouter()

# ── Páginas HTML ──────────────────────────────────────────────────────────────

@router.get("/reservaciones", response_class=HTMLResponse)
async def reservaciones_page(request: Request):
    content = (VIEWS_DIR / "reservaciones.html").read_text(encoding="utf-8")
    return render_backend_page_html(
        request,
        title="Reservaciones",
        description="Sistema de gestión de citas y ejecutivos",
        content=content,
        hide_floating_actions=True,
        show_page_header=False,
    )


@router.get("/reservaciones/calendario/{ejecutivo_id}", response_class=HTMLResponse)
async def calendario_page(ejecutivo_id: int, request: Request, db=Depends(SessionLocal)):
    ejecutivo = store.get_ejecutivo(db, ejecutivo_id)
    if not ejecutivo:
        raise HTTPException(status_code=404, detail="Ejecutivo no encontrado")
    content = (VIEWS_DIR / "calendario.html").read_text(encoding="utf-8")
    content = content.replace("__EJECUTIVO_ID__", str(ejecutivo_id))
    content = content.replace("__EJECUTIVO_NAME__", ejecutivo.name)
    content = content.replace("__BLOQUE_MIN__", str((ejecutivo.tiempo_promedio_cita or 30) + (ejecutivo.tiempo_descanso_sesiones or 0)))
    return render_backend_page_html(
        request,
        title=f"Calendario – {ejecutivo.name}",
        description="Calendario de citas del ejecutivo",
        content=content,
        hide_floating_actions=True,
        show_page_header=False,
    )


# ── API: Ejecutivos ───────────────────────────────────────────────────────────

@router.get("/api/reservaciones/ejecutivos")
async def api_list_ejecutivos(request: Request, db=Depends(SessionLocal)):
    items = store.list_ejecutivos(db)
    return JSONResponse({"success": True, "data": [
        {"id": e.id, "name": e.name, "email": e.email, "phone": e.phone,
         "especialidad": e.especialidad, "disponible": e.disponible,
         "tiempo_promedio_cita": e.tiempo_promedio_cita}
        for e in items
    ]})


@router.post("/api/reservaciones/ejecutivos")
async def api_create_ejecutivo(data: EjecutivoCreate, request: Request, db=Depends(SessionLocal)):
    obj = store.create_ejecutivo(db, data)
    return JSONResponse({"success": True, "data": {"id": obj.id, "name": obj.name}})


@router.put("/api/reservaciones/ejecutivos/{ejecutivo_id}")
async def api_update_ejecutivo(ejecutivo_id: int, data: EjecutivoUpdate, request: Request, db=Depends(SessionLocal)):
    obj = store.update_ejecutivo(db, ejecutivo_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Ejecutivo no encontrado")
    return JSONResponse({"success": True, "data": {"id": obj.id, "name": obj.name}})


@router.get("/api/reservaciones/ejecutivos/{ejecutivo_id}/slots")
async def api_get_slots(ejecutivo_id: int, fecha: str, request: Request, db=Depends(SessionLocal)):
    slots = store.get_slots_for_day(db, ejecutivo_id, fecha)
    return JSONResponse({"success": True, "data": slots})


# ── API: Tipos ────────────────────────────────────────────────────────────────

@router.get("/api/reservaciones/tipos")
async def api_list_tipos(request: Request, db=Depends(SessionLocal)):
    items = store.list_tipos(db)
    return JSONResponse({"success": True, "data": [
        {"id": t.id, "name": t.name, "duracion": t.duracion, "color": t.color} for t in items
    ]})


@router.post("/api/reservaciones/tipos")
async def api_create_tipo(data: TipoCitaCreate, request: Request, db=Depends(SessionLocal)):
    obj = store.create_tipo(db, data)
    return JSONResponse({"success": True, "data": {"id": obj.id, "name": obj.name}})


# ── API: Citas ────────────────────────────────────────────────────────────────

@router.get("/api/reservaciones/citas")
async def api_list_citas(
    request: Request,
    db=Depends(SessionLocal),
    ejecutivo_id: Optional[int] = None,
    state: Optional[str] = None,
    limit: int = 100,
):
    items = store.list_citas(db, limit=limit, ejecutivo_id=ejecutivo_id, state=state)
    return JSONResponse({"success": True, "data": [
        {
            "id": c.id,
            "name": c.name,
            "nombre_persona": c.nombre_persona,
            "celular_persona": c.celular_persona,
            "start_datetime": c.start_datetime.isoformat() if c.start_datetime else None,
            "ejecutivo_id": c.ejecutivo_id,
            "state": c.state,
            "notes": c.notes,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in items
    ]})


@router.post("/api/reservaciones/citas")
async def api_create_cita(data: CitaCreate, request: Request, db=Depends(SessionLocal)):
    obj = store.create_cita(db, data)
    return JSONResponse({"success": True, "data": {"id": obj.id, "name": obj.name}})


@router.put("/api/reservaciones/citas/{cita_id}/estado")
async def api_update_cita_estado(cita_id: int, request: Request, db=Depends(SessionLocal)):
    body = await request.json()
    state = body.get("state", "")
    if state not in ("draft", "confirmed", "in_progress", "completed", "cancelled"):
        raise HTTPException(status_code=400, detail="Estado inválido")
    obj = store.update_cita_state(db, cita_id, state)
    if not obj:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return JSONResponse({"success": True, "data": {"id": obj.id, "state": obj.state}})


@router.get("/api/reservaciones/stats")
async def api_stats(request: Request, db=Depends(SessionLocal)):
    stats = store.get_dashboard_stats(db)
    return JSONResponse({"success": True, "data": stats})


__all__ = ["router"]
