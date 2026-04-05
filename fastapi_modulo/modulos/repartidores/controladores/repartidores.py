from __future__ import annotations

from pathlib import Path
from typing import Generator, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi_modulo.core.db import SessionLocal
from fastapi_modulo.modulos_sipet.web import render_backend_page_html
from fastapi_modulo.modulos.repartidores.modelos.db_models import ensure_repartidores_schema
from fastapi_modulo.modulos.repartidores.modelos.schemas import (
    ActualizarEstadoEntregaInput,
    ActualizarLiquidacionEstadoInput,
    AsignarEntregaInput,
    EntregaCreate,
    GenerarLiquidacionInput,
    IncidenciaCreate,
    PosicionUpdate,
    RepartidorCreate,
    RepartidorUpdate,
    VehiculoCreate,
    ZonaCreate,
)
from fastapi_modulo.modulos.repartidores.modelos import store
from fastapi_modulo.modulos.repartidores.controladores.dependencies import (
    get_linked_repartidor_id,
    is_delivery_only,
    require_access,
    require_supervisor,
    require_write,
)

MODULE_DIR = Path(__file__).resolve().parents[1]
VIEWS_DIR = MODULE_DIR / 'vistas'

router = APIRouter()

try:
    ensure_repartidores_schema()
except Exception as _e:
    print(f"[repartidores] schema init warning: {_e}")


def get_db() -> Generator[object, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        close = getattr(db, 'close', None)
        if callable(close):
            close()


@router.get('/repartidores', response_class=HTMLResponse)
async def repartidores_page(request: Request, db=Depends(get_db), _user: dict = Depends(require_access)):
    content = (VIEWS_DIR / 'repartidores.html').read_text(encoding='utf-8')
    return render_backend_page_html(
        request,
        title='Repartidores',
        description='Gestión de repartidores, entregas, zonas e incidencias.',
        content=content,
        hide_floating_actions=True,
        show_page_header=False,
    )


@router.get('/api/repartidores/repartidores')
async def api_list_repartidores(
    request: Request,
    db=Depends(get_db),
    solo_activos: bool = True,
    zona_id: Optional[int] = None,
    state: Optional[str] = None,
    user: dict = Depends(require_access),
):
    # delivery_access solo puede verse a sí mismo
    if is_delivery_only(user):
        rep_id = get_linked_repartidor_id(db, user['username'])
        if rep_id is None:
            return JSONResponse({'success': True, 'data': []})
        rep = store.get_repartidor(db, rep_id)
        data = [store.serialize_repartidor(rep)] if rep else []
        return JSONResponse({'success': True, 'data': data})
    items = store.list_repartidores(db, solo_activos=solo_activos, zona_id=zona_id, state=state)
    return JSONResponse({'success': True, 'data': [store.serialize_repartidor(i) for i in items]})


@router.post('/api/repartidores/repartidores')
async def api_create_repartidor(data: RepartidorCreate, request: Request, db=Depends(get_db), _user: dict = Depends(require_supervisor)):
    try:
        obj = store.create_repartidor(db, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return JSONResponse({'success': True, 'data': store.serialize_repartidor(obj)})


@router.put('/api/repartidores/repartidores/{repartidor_id}')
@router.patch('/api/repartidores/repartidores/{repartidor_id}')
async def api_update_repartidor(repartidor_id: int, data: RepartidorUpdate, request: Request, db=Depends(get_db), _user: dict = Depends(require_supervisor)):
    try:
        obj = store.update_repartidor(db, repartidor_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not obj:
        raise HTTPException(status_code=404, detail='Repartidor no encontrado')
    return JSONResponse({'success': True, 'data': store.serialize_repartidor(obj)})


@router.get('/api/repartidores/zonas')
async def api_list_zonas(request: Request, db=Depends(get_db), solo_activas: bool = True, _user: dict = Depends(require_access)):
    items = store.list_zonas(db, solo_activas=solo_activas)
    return JSONResponse({'success': True, 'data': [store.serialize_zona(i) for i in items]})


@router.post('/api/repartidores/zonas')
async def api_create_zona(data: ZonaCreate, request: Request, db=Depends(get_db), _user: dict = Depends(require_supervisor)):
    try:
        obj = store.create_zona(db, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return JSONResponse({'success': True, 'data': store.serialize_zona(obj)})


@router.get('/api/repartidores/vehiculos')
async def api_list_vehiculos(request: Request, db=Depends(get_db), solo_activos: bool = True, _user: dict = Depends(require_access)):
    items = store.list_vehiculos(db, solo_activos=solo_activos)
    return JSONResponse({'success': True, 'data': [store.serialize_vehiculo(i) for i in items]})


@router.post('/api/repartidores/vehiculos')
async def api_create_vehiculo(data: VehiculoCreate, request: Request, db=Depends(get_db), _user: dict = Depends(require_supervisor)):
    obj = store.create_vehiculo(db, data)
    return JSONResponse({'success': True, 'data': store.serialize_vehiculo(obj)})


@router.get('/api/repartidores/entregas')
async def api_list_entregas(
    request: Request,
    db=Depends(get_db),
    repartidor_id: Optional[int] = None,
    state: Optional[str] = None,
    prioridad: Optional[str] = None,
    limit: int = 100,
    user: dict = Depends(require_access),
):
    # delivery_access solo ve sus propias entregas
    if is_delivery_only(user):
        linked = get_linked_repartidor_id(db, user['username'])
        repartidor_id = linked  # fuerza el filtro aunque no tenga repartidor vinculado
        if linked is None:
            return JSONResponse({'success': True, 'data': []})
    items = store.list_entregas(db, repartidor_id=repartidor_id, state=state, prioridad=prioridad, limit=limit)
    return JSONResponse({'success': True, 'data': [store.serialize_entrega(i) for i in items]})


@router.post('/api/repartidores/entregas')
async def api_create_entrega(data: EntregaCreate, request: Request, db=Depends(get_db), _user: dict = Depends(require_write)):
    try:
        obj = store.create_entrega(db, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return JSONResponse({'success': True, 'data': store.serialize_entrega(obj)})


@router.post('/api/repartidores/entregas/{entrega_id}/asignar')
@router.patch('/api/repartidores/entregas/{entrega_id}/asignar')
async def api_asignar_entrega(entrega_id: int, data: AsignarEntregaInput, request: Request, db=Depends(get_db), _user: dict = Depends(require_supervisor)):
    try:
        obj = store.assign_entrega(db, entrega_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not obj:
        raise HTTPException(status_code=404, detail='Entrega no encontrada')
    return JSONResponse({'success': True, 'data': store.serialize_entrega(obj)})


@router.post('/api/repartidores/entregas/{entrega_id}/estado')
@router.patch('/api/repartidores/entregas/{entrega_id}/estado')
async def api_estado_entrega(entrega_id: int, data: ActualizarEstadoEntregaInput, request: Request, db=Depends(get_db), user: dict = Depends(require_write)):
    # delivery_access solo puede actualizar estado de sus propias entregas
    if is_delivery_only(user):
        linked = get_linked_repartidor_id(db, user['username'])
        entrega = store.get_entrega(db, entrega_id)
        if not entrega or entrega.repartidor_id != linked:
            raise HTTPException(status_code=403, detail='No tienes permiso para modificar esta entrega.')
    try:
        obj = store.update_entrega_state(db, entrega_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not obj:
        raise HTTPException(status_code=404, detail='Entrega no encontrada')
    return JSONResponse({'success': True, 'data': store.serialize_entrega(obj)})


@router.get('/api/repartidores/incidencias')
async def api_list_incidencias(request: Request, db=Depends(get_db), state: Optional[str] = None, entrega_id: Optional[int] = None, user: dict = Depends(require_access)):
    items = store.list_incidencias(db, state=state, entrega_id=entrega_id)
    if is_delivery_only(user):
        linked = get_linked_repartidor_id(db, user['username'])
        items = [i for i in items if i.repartidor_id == linked or i.entrega_id in {
            e.id for e in store.list_entregas(db, repartidor_id=linked, limit=500)
        }]
    return JSONResponse({'success': True, 'data': [store.serialize_incidencia(i) for i in items]})


@router.post('/api/repartidores/incidencias')
async def api_create_incidencia(data: IncidenciaCreate, request: Request, db=Depends(get_db), _user: dict = Depends(require_write)):
    try:
        obj = store.create_incidencia(db, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return JSONResponse({'success': True, 'data': store.serialize_incidencia(obj)})


@router.get('/api/repartidores/liquidaciones')
async def api_list_liquidaciones(request: Request, db=Depends(get_db), repartidor_id: Optional[int] = None, state: Optional[str] = None, user: dict = Depends(require_access)):
    # delivery_access solo ve su propia liquidación
    if is_delivery_only(user):
        linked = get_linked_repartidor_id(db, user['username'])
        repartidor_id = linked
        if linked is None:
            return JSONResponse({'success': True, 'data': []})
    items = store.list_liquidaciones(db, repartidor_id=repartidor_id, state=state)
    return JSONResponse({'success': True, 'data': [store.serialize_liquidacion(i) for i in items]})


@router.patch('/api/repartidores/liquidaciones/{liquidacion_id}/estado')
async def api_update_liquidacion_estado(liquidacion_id: int, data: ActualizarLiquidacionEstadoInput, request: Request, db=Depends(get_db), _user: dict = Depends(require_supervisor)):
    try:
        obj = store.update_liquidacion_state(db, liquidacion_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return JSONResponse({'success': True, 'data': store.serialize_liquidacion(obj)})


@router.get('/api/repartidores/liquidaciones/{liquidacion_id}')
async def api_get_liquidacion(liquidacion_id: int, request: Request, db=Depends(get_db), user: dict = Depends(require_access)):
    liq = store.get_liquidacion(db, liquidacion_id)
    if not liq:
        raise HTTPException(status_code=404, detail='Liquidación no encontrada')
    # delivery_access solo puede ver su propia liquidación
    if is_delivery_only(user):
        linked = get_linked_repartidor_id(db, user['username'])
        if liq.repartidor_id != linked:
            raise HTTPException(status_code=403, detail='Sin acceso a esta liquidación.')
    return JSONResponse({'success': True, 'data': store.serialize_liquidacion(liq)})


@router.get('/api/repartidores/entregas/{entrega_id}/log')
async def api_entrega_log(entrega_id: int, request: Request, db=Depends(get_db), _user: dict = Depends(require_access)):
    logs = store.get_entrega_log(db, entrega_id)
    return JSONResponse({'success': True, 'data': [store.serialize_entrega_log(l) for l in logs]})


@router.post('/api/repartidores/liquidaciones/generar')
async def api_generar_liquidacion(data: GenerarLiquidacionInput, request: Request, db=Depends(get_db), _user: dict = Depends(require_supervisor)):
    try:
        obj = store.generate_liquidacion(db, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return JSONResponse({'success': True, 'data': store.serialize_liquidacion(obj)})


@router.get('/api/repartidores/stats')
async def api_stats(request: Request, db=Depends(get_db), _user: dict = Depends(require_access)):
    stats = store.get_dashboard_stats(db)
    return JSONResponse({'success': True, 'data': stats})


@router.get('/api/repartidores/alertas')
async def api_alertas(
    request: Request,
    db=Depends(get_db),
    _user: dict = Depends(require_access),
):
    from fastapi_modulo.modulos.repartidores.servicios.alertas import get_alertas_operativas

    alertas = get_alertas_operativas(db)
    return JSONResponse({'success': True, 'data': alertas, 'total': len(alertas)})


# ---------------------------------------------------------------------------
# FASE 6 — ANALÍTICA E INTELIGENCIA OPERATIVA
# ---------------------------------------------------------------------------

@router.get('/api/repartidores/analitica/kpis')
async def api_analitica_kpis(
    request: Request,
    db=Depends(get_db),
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    repartidor_id: Optional[int] = None,
    _user: dict = Depends(require_access),
):
    data = store.get_kpis_periodo(db, fecha_inicio, fecha_fin, repartidor_id)
    return JSONResponse({'success': True, 'data': data})


@router.get('/api/repartidores/analitica/productividad')
async def api_analitica_productividad(
    request: Request,
    db=Depends(get_db),
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    limit: int = 20,
    _user: dict = Depends(require_access),
):
    data = store.get_productividad_repartidores(db, fecha_inicio, fecha_fin, limit)
    return JSONResponse({'success': True, 'data': data})


@router.get('/api/repartidores/analitica/zonas')
async def api_analitica_zonas(
    request: Request,
    db=Depends(get_db),
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    _user: dict = Depends(require_access),
):
    data = store.get_entregas_por_zona(db, fecha_inicio, fecha_fin)
    return JSONResponse({'success': True, 'data': data})


@router.get('/api/repartidores/analitica/margen')
async def api_analitica_margen(
    request: Request,
    db=Depends(get_db),
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    repartidor_id: Optional[int] = None,
    _user: dict = Depends(require_supervisor),
):
    data = store.get_margen_logistico(db, fecha_inicio, fecha_fin, repartidor_id)
    return JSONResponse({'success': True, 'data': data})


@router.get('/api/repartidores/analitica/tendencia')
async def api_analitica_tendencia(
    request: Request,
    db=Depends(get_db),
    agrupacion: str = 'semana',
    periodos: int = 12,
    _user: dict = Depends(require_access),
):
    if agrupacion not in {'semana', 'mes'}:
        raise HTTPException(status_code=400, detail='agrupacion debe ser "semana" o "mes"')
    data = store.get_tendencia(db, agrupacion, periodos)
    return JSONResponse({'success': True, 'data': data})


@router.get('/api/repartidores/analitica/incidencias')
async def api_analitica_incidencias(
    request: Request,
    db=Depends(get_db),
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    repartidor_id: Optional[int] = None,
    _user: dict = Depends(require_access),
):
    data = store.get_reporte_incidencias(db, fecha_inicio, fecha_fin, repartidor_id)
    return JSONResponse({'success': True, 'data': data})


@router.get('/api/repartidores/analitica/exportar-csv')
async def api_exportar_csv(
    request: Request,
    db=Depends(get_db),
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    repartidor_id: Optional[int] = None,
    state: Optional[str] = None,
    _user: dict = Depends(require_supervisor),
):
    from fastapi.responses import Response

    contenido = store.exportar_entregas_csv(db, fecha_inicio, fecha_fin, repartidor_id, state)
    filename = f'entregas_{fecha_inicio or "all"}_{fecha_fin or "all"}.csv'
    return Response(
        content=contenido.encode('utf-8-sig'),
        media_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# FASE 7 — GEOLOCALIZACIÓN Y SEGUIMIENTO
# ---------------------------------------------------------------------------

@router.put('/api/repartidores/repartidores/{repartidor_id}/posicion')
@router.patch('/api/repartidores/repartidores/{repartidor_id}/posicion')
async def api_posicion_repartidor(
    repartidor_id: int,
    data: PosicionUpdate,
    request: Request,
    db=Depends(get_db),
    user: dict = Depends(require_write),
):
    from fastapi_modulo.modulos.repartidores.controladores.dependencies import is_delivery_only, get_linked_repartidor_id

    # delivery_access solo puede actualizar su propia posición
    if is_delivery_only(user):
        propio = get_linked_repartidor_id(db, user['username'])
        if propio != repartidor_id:
            raise HTTPException(status_code=403, detail='Solo puedes actualizar tu propia posición')

    rep = store.get_repartidor(db, repartidor_id)
    if not rep or not rep.activo:
        raise HTTPException(status_code=404, detail='Repartidor no encontrado')
    pos = store.update_repartidor_posicion(db, repartidor_id, data)
    return JSONResponse({'success': True, 'data': {
        'repartidor_id': pos.repartidor_id,
        'lat': pos.lat,
        'lng': pos.lng,
        'precision_m': pos.precision_m,
        'updated_at': pos.updated_at.isoformat() if pos.updated_at else None,
    }})


@router.post('/api/repartidores/entregas/{entrega_id}/calcular-distancia')
async def api_calcular_distancia(
    entrega_id: int,
    request: Request,
    db=Depends(get_db),
    _user: dict = Depends(require_write),
):
    entrega = store.calcular_distancia_entrega(db, entrega_id)
    if not entrega:
        raise HTTPException(status_code=404, detail='Entrega no encontrada')
    return JSONResponse({'success': True, 'data': {
        'entrega_id': entrega.id,
        'folio': entrega.folio,
        'distancia_km': float(entrega.distancia_km or 0),
        'tiempo_estimado_min': entrega.tiempo_estimado_min,
    }})


@router.get('/api/repartidores/mapa/entregas')
async def api_mapa_entregas(
    request: Request,
    db=Depends(get_db),
    state: Optional[str] = None,
    solo_con_coords: bool = False,
    _user: dict = Depends(require_access),
):
    data = store.get_mapa_entregas(db, state, solo_con_coords)
    return JSONResponse({'success': True, 'data': data, 'total': len(data)})


@router.get('/api/repartidores/mapa/repartidores')
async def api_mapa_repartidores(
    request: Request,
    db=Depends(get_db),
    _user: dict = Depends(require_access),
):
    data = store.get_mapa_repartidores(db)
    return JSONResponse({'success': True, 'data': data})


@router.get('/api/repartidores/mapa/zonas')
async def api_mapa_zonas(
    request: Request,
    db=Depends(get_db),
    _user: dict = Depends(require_access),
):
    data = store.get_zonas_mapa(db)
    return JSONResponse({'success': True, 'data': data})


@router.get('/api/repartidores/repartidores/cercanos')
async def api_repartidores_cercanos(
    request: Request,
    db=Depends(get_db),
    lat: float = 0.0,
    lng: float = 0.0,
    radio_km: float = 5.0,
    solo_disponibles: bool = True,
    _user: dict = Depends(require_access),
):
    if lat == 0.0 and lng == 0.0:
        raise HTTPException(status_code=400, detail='Se requieren lat y lng')
    data = store.get_repartidores_cercanos(db, lat, lng, radio_km, solo_disponibles)
    return JSONResponse({'success': True, 'data': data, 'total': len(data)})


__all__ = ['router']
