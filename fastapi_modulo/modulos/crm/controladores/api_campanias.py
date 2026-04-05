from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from fastapi_modulo.modulos.crm.modelos.schemas import CampaniaCreate, CampaniaResultadoUpdate, CampaniaUpdate, ContactoCampaniaCreate, SegmentacionParams
from fastapi_modulo.modulos.crm.servicios.campania_service import (
    activar_campania,
    add_contacto_campania,
    archivar_campania,
    cerrar_campania,
    create_campania,
    duplicar_campania,
    list_campanias_by_tenant,
    list_contactos_campania,
    remove_contacto_de_campania,
    registrar_resultado_campania,
    segmentar_contactos,
    update_campania,
)
from fastapi_modulo.modulos.crm.servicios.campaign_analytics_service import (
    get_kpis_campania,
    list_atribuciones,
)

router = APIRouter()


@router.get("/api/crm/campanias")
def api_list_campanias(request: Request, estado: str = "", q: str = "", responsable: str = "", skip: int = 0, limit: int = 100):
    return JSONResponse(list_campanias_by_tenant(getattr(request.state, "tenant_id", None), estado or None, q or None, responsable or None, skip, limit))


@router.post("/api/crm/campanias")
def api_create_campania(body: CampaniaCreate, request: Request):
    try:
        return JSONResponse(
            create_campania(
                body.model_dump(),
                getattr(request.state, "tenant_id", None),
                actor=getattr(request.state, "user_name", ""),
            ),
            status_code=201,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.put("/api/crm/campanias/{campania_id}")
def api_update_campania(campania_id: int, body: CampaniaUpdate, request: Request):
    try:
        result = update_campania(
            campania_id,
            body.model_dump(exclude_unset=True),
            getattr(request.state, "tenant_id", None),
            actor=getattr(request.state, "user_name", ""),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if not result:
        raise HTTPException(status_code=404, detail="Campaña no encontrada")
    return JSONResponse(result)


@router.get("/api/crm/campanias/{campania_id}/contactos")
def api_list_contactos_campania(campania_id: int, request: Request):
    return JSONResponse(list_contactos_campania(campania_id, getattr(request.state, "tenant_id", None)))


@router.post("/api/crm/campanias/contactos")
def api_add_contacto_campania(body: ContactoCampaniaCreate, request: Request):
    try:
        return JSONResponse(
            add_contacto_campania(
                body.model_dump(),
                getattr(request.state, "tenant_id", None),
                actor=getattr(request.state, "user_name", ""),
            ),
            status_code=201,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.delete("/api/crm/campanias/{campania_id}/contactos/{contacto_id}")
def api_remove_contacto_campania(campania_id: int, contacto_id: int, request: Request):
    removed = remove_contacto_de_campania(
        campania_id,
        contacto_id,
        getattr(request.state, "tenant_id", None),
        actor=getattr(request.state, "user_name", ""),
    )
    if not removed:
        raise HTTPException(status_code=404, detail="Relación campaña-contacto no encontrada")
    return JSONResponse({"ok": True})


@router.post("/api/crm/campanias/{campania_id}/duplicar")
def api_duplicar_campania(campania_id: int, request: Request):
    result = duplicar_campania(
        campania_id,
        getattr(request.state, "tenant_id", None),
        actor=getattr(request.state, "user_name", ""),
    )
    if not result:
        raise HTTPException(status_code=404, detail="Campaña no encontrada")
    return JSONResponse(result, status_code=201)


@router.post("/api/crm/campanias/{campania_id}/cerrar")
def api_cerrar_campania(campania_id: int, request: Request):
    result = cerrar_campania(
        campania_id,
        getattr(request.state, "tenant_id", None),
        actor=getattr(request.state, "user_name", ""),
    )
    if not result:
        raise HTTPException(status_code=404, detail="Campaña no encontrada")
    return JSONResponse(result)


@router.post("/api/crm/campanias/{campania_id}/resultado")
def api_registrar_resultado_campania(campania_id: int, body: CampaniaResultadoUpdate, request: Request):
    result = registrar_resultado_campania(
        campania_id,
        body.resultado,
        getattr(request.state, "tenant_id", None),
        actor=getattr(request.state, "user_name", ""),
    )
    if not result:
        raise HTTPException(status_code=404, detail="Campaña no encontrada")
    return JSONResponse(result)


@router.post("/api/crm/campanias/{campania_id}/activar")
def api_activar_campania(campania_id: int, request: Request):
    """Activa la campaña y genera actividades de seguimiento para el segmento."""
    try:
        result = activar_campania(
            campania_id,
            getattr(request.state, "tenant_id", None),
            actor=getattr(request.state, "user_name", ""),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if not result:
        raise HTTPException(status_code=404, detail="Campaña no encontrada")
    return JSONResponse(result)


@router.post("/api/crm/campanias/{campania_id}/segmentar")
def api_segmentar_campania(campania_id: int, body: SegmentacionParams, request: Request):
    """Segmenta contactos según los filtros y los incorpora a la campaña."""
    try:
        result = segmentar_contactos(
            campania_id,
            body.model_dump(exclude_none=True),
            getattr(request.state, "tenant_id", None),
            agregar=True,
            actor=getattr(request.state, "user_name", ""),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return JSONResponse(result)


@router.get("/api/crm/campanias/{campania_id}/kpis")
def api_kpis_campania(campania_id: int, request: Request):
    """Retorna KPIs y ROI de la campaña."""
    result = get_kpis_campania(campania_id, getattr(request.state, "tenant_id", None))
    if not result:
        raise HTTPException(status_code=404, detail="Campaña no encontrada")
    return JSONResponse(result)


@router.get("/api/crm/campanias/{campania_id}/atribuciones")
def api_atribuciones_campania(campania_id: int, request: Request):
    """Lista todas las atribuciones de contactos/oportunidades a la campaña."""
    return JSONResponse(list_atribuciones(campania_id, getattr(request.state, "tenant_id", None)))


@router.patch("/api/crm/campanias/{campania_id}/archivar")
def api_archivar_campania(campania_id: int, request: Request):
    result = archivar_campania(
        campania_id,
        getattr(request.state, "tenant_id", None),
        actor=getattr(request.state, "user_name", ""),
    )
    if not result:
        raise HTTPException(status_code=404, detail="Campaña no encontrada")
    return JSONResponse(result)
