from __future__ import annotations
import csv
import io
from pathlib import Path
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi_modulo.core.db import SessionLocal
from fastapi_modulo.modulos_sipet.web.servicios.module_tools import render_backend_page_html
from fastapi_modulo.modulos.reservaciones.modelos.db_models import ensure_reservaciones_schema
from fastapi_modulo.modulos.reservaciones.modelos.schemas import (
    BloqueoCreate, CitaCreate, CitaEstadoUpdate, CitaReadDetail, CitaUpdate,
    EjecutivoCreate, EjecutivoUpdate, ExcepcionCreate, FranjaCreate,
    ReprogramarCita, TipoCitaCreate,
)
from fastapi_modulo.modulos.reservaciones.modelos import store
from fastapi_modulo.modulos.reservaciones.controladores.dependencies import (
    RolReservaciones,
    require_any_res_access,
    require_full_access,
    require_at_least_ejecutivo,
    get_ejecutivo_id_en_sesion,
    ACCESS_DENIED,
)

MODULE_DIR = Path(__file__).resolve().parents[1]
VIEWS_DIR = MODULE_DIR / "vistas"

try:
    ensure_reservaciones_schema()
except Exception as _e:
    print(f"[reservaciones] schema init warning: {_e}")

router = APIRouter()

# ── Páginas HTML ──────────────────────────────────────────────────────────────

@router.get("/reservaciones", response_class=HTMLResponse)
async def reservaciones_page(
    request: Request,
    _rol: RolReservaciones = Depends(require_any_res_access),
):
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
async def calendario_page(
    ejecutivo_id: int,
    request: Request,
    db=Depends(SessionLocal),
    _rol: RolReservaciones = Depends(require_any_res_access),
):
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


@router.get("/reservaciones/kanban", response_class=HTMLResponse)
async def kanban_page(
    request: Request,
    _rol: RolReservaciones = Depends(require_any_res_access),
):
    content = (VIEWS_DIR / "kanban.html").read_text(encoding="utf-8")
    return render_backend_page_html(
        request,
        title="Kanban de Citas",
        description="Vista kanban del flujo de citas",
        content=content,
        hide_floating_actions=True,
        show_page_header=False,
    )


@router.get("/reservaciones/cancelar/{token}", response_class=HTMLResponse)
async def cancelar_cita_publica_page(token: str, db=Depends(SessionLocal)):
    """Página pública para que el cliente confirme la cancelación con su token."""
    from fastapi_modulo.modulos.reservaciones.modelos.db_models import ResCita
    cita = db.query(ResCita).filter(ResCita.cancel_token == token).first()
    if not cita:
        return HTMLResponse("<h2 style='font-family:sans-serif;padding:2rem'>Enlace inválido o ya utilizado.</h2>", status_code=404)
    if cita.state in ("cancelled", "completed", "no_show"):
        return HTMLResponse(f"<h2 style='font-family:sans-serif;padding:2rem'>Esta cita ya está en estado «{cita.state}».</h2>")
    persona = cita.nombre_persona
    fecha = cita.start_datetime.strftime("%d/%m/%Y %H:%M") if cita.start_datetime else ""
    html = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>Cancelar cita</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
</head><body class="bg-light d-flex align-items-center justify-content-center" style="min-height:100vh">
<div class="card shadow p-4" style="max-width:480px;width:100%">
  <h4 class="mb-3 text-danger">Cancelar cita</h4>
  <p>Hola <strong>{persona}</strong>, estás a punto de cancelar la siguiente cita:</p>
  <p class="fw-bold fs-5">{fecha}</p>
  <form method="post" action="/api/reservaciones/cancelar/{token}">
    <div class="mb-3">
      <label class="form-label">Motivo (opcional)</label>
      <input name="motivo" class="form-control" maxlength="300" placeholder="Indique el motivo...">
    </div>
    <button type="submit" class="btn btn-danger w-100">Confirmar cancelación</button>
    <a href="/" class="btn btn-outline-secondary w-100 mt-2">Mantener cita</a>
  </form>
</div></body></html>"""
    return HTMLResponse(html)


@router.post("/api/reservaciones/cancelar/{token}", response_class=HTMLResponse)
async def cancelar_por_token_form(token: str, db=Depends(SessionLocal)):
    """Endpoint que recibe el formulario de cancelación pública."""
    from fastapi import Form
    try:
        obj = store.cancelar_por_token(db, token)
    except ValueError as exc:
        return HTMLResponse(f"<p style='color:red;font-family:sans-serif;padding:2rem'>{exc}</p>", status_code=400)
    if not obj:
        return HTMLResponse("<p style='font-family:sans-serif;padding:2rem'>Token inválido o ya utilizado.</p>", status_code=404)
    return HTMLResponse("""<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>Cita cancelada</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
</head><body class="bg-light d-flex align-items-center justify-content-center" style="min-height:100vh">
<div class="card shadow p-4 text-center" style="max-width:400px;width:100%">
  <div class="display-1 text-success mb-3">✓</div>
  <h4>Cita cancelada</h4>
  <p class="text-muted">Su cita ha sido cancelada exitosamente.</p>
</div></body></html>""")


# ── API: Ejecutivos ───────────────────────────────────────────────────────────

@router.get("/api/reservaciones/ejecutivos/{ejecutivo_id}/horario")
async def api_list_franjas(
    ejecutivo_id: int,
    db=Depends(SessionLocal),
    _rol: RolReservaciones = Depends(require_any_res_access),
):
    items = store.list_franjas(db, ejecutivo_id)
    return JSONResponse({"success": True, "data": [
        {"id": f.id, "dia_semana": f.dia_semana, "hora_ini": f.hora_ini, "hora_fin": f.hora_fin}
        for f in items
    ]})


@router.post("/api/reservaciones/ejecutivos/{ejecutivo_id}/horario")
async def api_create_franja(
    ejecutivo_id: int,
    data: FranjaCreate,
    db=Depends(SessionLocal),
    _rol: RolReservaciones = Depends(require_full_access),
):
    obj = store.create_franja(db, ejecutivo_id, data)
    return JSONResponse({"success": True, "data": {"id": obj.id}})


@router.delete("/api/reservaciones/horario/{franja_id}")
async def api_delete_franja(
    franja_id: int,
    db=Depends(SessionLocal),
    _rol: RolReservaciones = Depends(require_full_access),
):
    ok = store.delete_franja(db, franja_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Franja no encontrada")
    return JSONResponse({"success": True})


@router.get("/api/reservaciones/ejecutivos")
async def api_list_ejecutivos(
    request: Request,
    db=Depends(SessionLocal),
    _rol: RolReservaciones = Depends(require_any_res_access),
):
    items = store.list_ejecutivos(db)
    return JSONResponse({"success": True, "data": [
        {"id": e.id, "name": e.name, "email": e.email, "phone": e.phone,
         "especialidad": e.especialidad, "disponible": e.disponible,
         "tiempo_promedio_cita": e.tiempo_promedio_cita}
        for e in items
    ]})


@router.post("/api/reservaciones/ejecutivos")
async def api_create_ejecutivo(
    data: EjecutivoCreate,
    request: Request,
    db=Depends(SessionLocal),
    _rol: RolReservaciones = Depends(require_full_access),
):
    obj = store.create_ejecutivo(db, data)
    return JSONResponse({"success": True, "data": {"id": obj.id, "name": obj.name}})


@router.put("/api/reservaciones/ejecutivos/{ejecutivo_id}")
async def api_update_ejecutivo(
    ejecutivo_id: int,
    data: EjecutivoUpdate,
    request: Request,
    db=Depends(SessionLocal),
    _rol: RolReservaciones = Depends(require_full_access),
):
    obj = store.update_ejecutivo(db, ejecutivo_id, data)
    if not obj:
        raise HTTPException(status_code=404, detail="Ejecutivo no encontrado")
    return JSONResponse({"success": True, "data": {"id": obj.id, "name": obj.name}})


@router.get("/api/reservaciones/ejecutivos/{ejecutivo_id}/slots")
async def api_get_slots(
    ejecutivo_id: int,
    fecha: str,
    request: Request,
    db=Depends(SessionLocal),
    _rol: RolReservaciones = Depends(require_any_res_access),
):
    slots = store.get_slots_for_day(db, ejecutivo_id, fecha)
    return JSONResponse({"success": True, "data": slots})


@router.get("/api/reservaciones/ejecutivos/{ejecutivo_id}/agenda")
async def api_get_agenda(
    ejecutivo_id: int,
    request: Request,
    db=Depends(SessionLocal),
    fecha_ini: str = "",
    fecha_fin: str = "",
    rol: RolReservaciones = Depends(require_at_least_ejecutivo),
    ej_sesion: Optional[int] = Depends(get_ejecutivo_id_en_sesion),
):
    if not fecha_ini or not fecha_fin:
        raise HTTPException(status_code=400, detail="Se requieren fecha_ini y fecha_fin (YYYY-MM-DD)")
    # Ejecutivo solo puede ver su propia agenda
    if rol == RolReservaciones.EJECUTIVO:
        if ej_sesion is None or ejecutivo_id != ej_sesion:
            raise HTTPException(status_code=403, detail=ACCESS_DENIED)
    try:
        agenda = store.get_agenda_ejecutivo(db, ejecutivo_id, fecha_ini, fecha_fin)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return JSONResponse({"success": True, "data": agenda})


@router.get("/api/reservaciones/ejecutivos/{ejecutivo_id}/disponibilidad")
async def api_get_disponibilidad(
    ejecutivo_id: int,
    request: Request,
    db=Depends(SessionLocal),
    fecha_ini: str = "",
    fecha_fin: str = "",
    _rol: RolReservaciones = Depends(require_any_res_access),
):
    if not fecha_ini or not fecha_fin:
        raise HTTPException(status_code=400, detail="Se requieren fecha_ini y fecha_fin (YYYY-MM-DD)")
    try:
        data = store.get_disponibilidad_rango(db, ejecutivo_id, fecha_ini, fecha_fin)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return JSONResponse({"success": True, "data": data})


# ── API: Bloqueos de agenda ───────────────────────────────────────────────────

@router.get("/api/reservaciones/bloqueos/{ejecutivo_id}")
async def api_list_bloqueos(
    ejecutivo_id: int,
    db=Depends(SessionLocal),
    _rol: RolReservaciones = Depends(require_any_res_access),
):
    items = store.list_bloqueos(db, ejecutivo_id)
    return JSONResponse({"success": True, "data": [
        {"id": b.id, "start_datetime": b.start_datetime.isoformat(),
         "end_datetime": b.end_datetime.isoformat(), "motivo": b.motivo}
        for b in items
    ]})


@router.post("/api/reservaciones/bloqueos")
async def api_create_bloqueo(
    data: BloqueoCreate,
    db=Depends(SessionLocal),
    _rol: RolReservaciones = Depends(require_full_access),
):
    obj = store.create_bloqueo(db, data)
    return JSONResponse({"success": True, "data": {"id": obj.id}})


@router.delete("/api/reservaciones/bloqueos/{bloqueo_id}")
async def api_delete_bloqueo(
    bloqueo_id: int,
    db=Depends(SessionLocal),
    _rol: RolReservaciones = Depends(require_full_access),
):
    ok = store.delete_bloqueo(db, bloqueo_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Bloqueo no encontrado")
    return JSONResponse({"success": True})


# ── API: Excepciones por fecha ────────────────────────────────────────────────

@router.get("/api/reservaciones/excepciones")
async def api_list_excepciones(
    db=Depends(SessionLocal),
    ejecutivo_id: Optional[int] = None,
    _rol: RolReservaciones = Depends(require_any_res_access),
):
    items = store.list_excepciones(db, ejecutivo_id)
    return JSONResponse({"success": True, "data": [
        {"id": e.id, "fecha": e.fecha.isoformat() if hasattr(e.fecha, 'isoformat') else str(e.fecha),
         "ejecutivo_id": e.ejecutivo_id, "motivo": e.motivo}
        for e in items
    ]})


@router.post("/api/reservaciones/excepciones")
async def api_create_excepcion(
    data: ExcepcionCreate,
    db=Depends(SessionLocal),
    _rol: RolReservaciones = Depends(require_full_access),
):
    obj = store.create_excepcion(db, data)
    return JSONResponse({"success": True, "data": {"id": obj.id}})


@router.delete("/api/reservaciones/excepciones/{excepcion_id}")
async def api_delete_excepcion(
    excepcion_id: int,
    db=Depends(SessionLocal),
    _rol: RolReservaciones = Depends(require_full_access),
):
    ok = store.delete_excepcion(db, excepcion_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Excepción no encontrada")
    return JSONResponse({"success": True})


# ── API: Tipos ────────────────────────────────────────────────────────────────

@router.get("/api/reservaciones/tipos")
async def api_list_tipos(
    request: Request,
    db=Depends(SessionLocal),
    _rol: RolReservaciones = Depends(require_any_res_access),
):
    items = store.list_tipos(db)
    return JSONResponse({"success": True, "data": [
        {"id": t.id, "name": t.name, "duracion_minutos": t.duracion_minutos, "color": t.color} for t in items
    ]})


@router.post("/api/reservaciones/tipos")
async def api_create_tipo(
    data: TipoCitaCreate,
    request: Request,
    db=Depends(SessionLocal),
    _rol: RolReservaciones = Depends(require_full_access),
):
    obj = store.create_tipo(db, data)
    return JSONResponse({"success": True, "data": {"id": obj.id, "name": obj.name}})


# ── API: Citas ────────────────────────────────────────────────────────────────

@router.get("/api/reservaciones/citas/exportar")
async def api_exportar_citas(
    db=Depends(SessionLocal),
    ejecutivo_id: Optional[int] = None,
    fecha_ini: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    _rol: RolReservaciones = Depends(require_full_access),
):
    rows = store.get_citas_csv_rows(db, ejecutivo_id, fecha_ini, fecha_fin)
    if not rows:
        return JSONResponse({"success": True, "data": [], "message": "Sin resultados"})
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=citas.csv"},
    )


@router.get("/api/reservaciones/citas")
async def api_list_citas(
    request: Request,
    db=Depends(SessionLocal),
    ejecutivo_id: Optional[int] = None,
    state: Optional[str] = None,
    limit: int = 100,
    rol: RolReservaciones = Depends(require_any_res_access),
    ej_sesion: Optional[int] = Depends(get_ejecutivo_id_en_sesion),
):
    # Ejecutivo solo ve sus propias citas
    if rol == RolReservaciones.EJECUTIVO:
        if ej_sesion is None:
            raise HTTPException(status_code=403, detail="No tiene perfil de ejecutivo asignado")
        ejecutivo_id = ej_sesion
    items = store.list_citas(db, limit=limit, ejecutivo_id=ejecutivo_id, state=state)
    return JSONResponse({"success": True, "data": [
        {
            "id": c.id,
            "name": c.name,
            "nombre_persona": c.nombre_persona,
            "celular_persona": c.celular_persona,
            "start_datetime": c.start_datetime.isoformat() if c.start_datetime else None,
            "end_datetime": c.end_datetime.isoformat() if c.end_datetime else None,
            "ejecutivo_id": c.ejecutivo_id,
            "tipo_id": c.tipo_id,
            "state": c.state,
            "source": c.source,
            "notes": c.notes,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in items
    ]})


@router.get("/api/reservaciones/citas/{cita_id}")
async def api_get_cita(
    cita_id: int,
    db=Depends(SessionLocal),
    rol: RolReservaciones = Depends(require_any_res_access),
    ej_sesion: Optional[int] = Depends(get_ejecutivo_id_en_sesion),
):
    obj = store.get_cita(db, cita_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    # Ejecutivo solo puede ver sus propias citas
    if rol == RolReservaciones.EJECUTIVO:
        if ej_sesion is None or obj.ejecutivo_id != ej_sesion:
            raise HTTPException(status_code=403, detail=ACCESS_DENIED)
    ej = obj.ejecutivo
    tipo = obj.tipo
    detail = CitaReadDetail.model_validate(obj)
    detail.ejecutivo_name = ej.name if ej else None
    detail.tipo_name = tipo.name if tipo else None
    detail.tipo_duracion_minutos = tipo.duracion_minutos if tipo else None
    return JSONResponse({"success": True, "data": detail.model_dump(mode="json")})


@router.post("/api/reservaciones/citas")
async def api_create_cita(
    data: CitaCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db=Depends(SessionLocal),
    _rol: RolReservaciones = Depends(require_at_least_ejecutivo),
):
    try:
        obj = store.create_cita(db, data)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    # Enviar confirmación si hay email
    if obj.email_persona:
        background_tasks.add_task(
            store.enviar_confirmacion_en_background,
            obj.id,
            SessionLocal,
        )
    return JSONResponse({"success": True, "data": {"id": obj.id, "name": obj.name}})


@router.put("/api/reservaciones/citas/{cita_id}/estado")
async def api_update_cita_estado(
    cita_id: int,
    data: CitaEstadoUpdate,
    background_tasks: BackgroundTasks,
    db=Depends(SessionLocal),
    rol: RolReservaciones = Depends(require_at_least_ejecutivo),
    ej_sesion: Optional[int] = Depends(get_ejecutivo_id_en_sesion),
):
    if rol == RolReservaciones.EJECUTIVO:
        obj = store.get_cita(db, cita_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Cita no encontrada")
        if ej_sesion is None or obj.ejecutivo_id != ej_sesion:
            raise HTTPException(status_code=403, detail=ACCESS_DENIED)
    try:
        obj = store.update_cita_state(db, cita_id, data.state, motivo=data.motivo)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not obj:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    # Confirmación por correo cuando transición → confirmed
    if data.state == "confirmed" and obj.email_persona:
        background_tasks.add_task(store.enviar_confirmacion_en_background, obj.id, SessionLocal)
    return JSONResponse({"success": True, "data": {"id": obj.id, "state": obj.state}})


@router.put("/api/reservaciones/citas/{cita_id}/reprogramar")
async def api_reprogramar_cita(
    cita_id: int,
    data: ReprogramarCita,
    db=Depends(SessionLocal),
    rol: RolReservaciones = Depends(require_at_least_ejecutivo),
    ej_sesion: Optional[int] = Depends(get_ejecutivo_id_en_sesion),
):
    if rol == RolReservaciones.EJECUTIVO:
        obj = store.get_cita(db, cita_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Cita no encontrada")
        if ej_sesion is None or obj.ejecutivo_id != ej_sesion:
            raise HTTPException(status_code=403, detail=ACCESS_DENIED)
    try:
        obj = store.reprogramar_cita(db, cita_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return JSONResponse({"success": True, "data": {
        "id": obj.id,
        "start_datetime": obj.start_datetime.isoformat(),
        "end_datetime": obj.end_datetime.isoformat() if obj.end_datetime else None,
    }})


@router.post("/api/reservaciones/citas/{cita_id}/cancelar")
async def api_cancelar_cita(
    cita_id: int,
    data: CitaEstadoUpdate,
    db=Depends(SessionLocal),
    rol: RolReservaciones = Depends(require_at_least_ejecutivo),
    ej_sesion: Optional[int] = Depends(get_ejecutivo_id_en_sesion),
):
    if rol == RolReservaciones.EJECUTIVO:
        obj = store.get_cita(db, cita_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Cita no encontrada")
        if ej_sesion is None or obj.ejecutivo_id != ej_sesion:
            raise HTTPException(status_code=403, detail=ACCESS_DENIED)
    try:
        obj = store.cancelar_cita(db, cita_id, motivo=data.motivo)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not obj:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return JSONResponse({"success": True, "data": {"id": obj.id, "state": obj.state}})


@router.post("/api/reservaciones/citas/{cita_id}/token-cancelacion")
async def api_generar_token_cancelacion(
    cita_id: int,
    request: Request,
    db=Depends(SessionLocal),
    _rol: RolReservaciones = Depends(require_at_least_ejecutivo),
):
    try:
        token = store.generar_token_cancelacion(db, cita_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if token is None:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    base_url = str(request.base_url).rstrip("/")
    return JSONResponse({"success": True, "data": {
        "token": token,
        "url": f"{base_url}/reservaciones/cancelar/{token}",
    }})


@router.post("/api/reservaciones/citas/{cita_id}/recordatorio")
async def api_enviar_recordatorio(
    cita_id: int,
    background_tasks: BackgroundTasks,
    db=Depends(SessionLocal),
    _rol: RolReservaciones = Depends(require_at_least_ejecutivo),
):
    obj = store.get_cita(db, cita_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    if not obj.email_persona:
        raise HTTPException(status_code=400, detail="La cita no tiene correo electrónico registrado")
    background_tasks.add_task(store.enviar_confirmacion_en_background, cita_id, SessionLocal)
    return JSONResponse({"success": True, "message": "Recordatorio enviado"})


@router.get("/api/reservaciones/stats")
async def api_stats(
    request: Request,
    db=Depends(SessionLocal),
    _rol: RolReservaciones = Depends(require_full_access),
):
    stats = store.get_dashboard_stats_avanzado(db)
    return JSONResponse({"success": True, "data": stats})


# ── Portal público (sin autenticación) ────────────────────────────────────────

@router.post("/api/reservaciones/publico/citas")
async def api_create_cita_publica(data: CitaCreate, db=Depends(SessionLocal)):
    """
    Crea una cita desde el portal público (sin autenticación requerida).
    El source se fuerza a 'portal' independientemente del cuerpo recibido.
    Solo permite ejecutivos activos y con disponibilidad.
    """
    try:
        obj = store.create_cita(db, data, source="portal")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return JSONResponse({"success": True, "data": {"id": obj.id, "name": obj.name}})


__all__ = ["router"]
