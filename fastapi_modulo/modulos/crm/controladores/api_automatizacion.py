from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from fastapi_modulo.modulos.crm.servicios.automation_service import (
    create_regla,
    delete_regla,
    evaluar_reglas,
    get_regla,
    list_reglas,
    update_regla,
)

router = APIRouter()


class ReglaCreate(BaseModel):
    nombre: str
    evento_trigger: str
    condicion_json: Optional[Dict[str, Any]] = None
    accion_tipo: str
    accion_params_json: Optional[Dict[str, Any]] = None
    activa: bool = True


class ReglaUpdate(BaseModel):
    nombre: Optional[str] = None
    evento_trigger: Optional[str] = None
    condicion_json: Optional[Dict[str, Any]] = None
    accion_tipo: Optional[str] = None
    accion_params_json: Optional[Dict[str, Any]] = None
    activa: Optional[bool] = None


class EvaluarRequest(BaseModel):
    evento_trigger: str
    contexto: Dict[str, Any] = {}


@router.get("/api/crm/automatizacion/reglas")
def api_list_reglas(request: Request, solo_activas: bool = False):
    return JSONResponse(list_reglas(getattr(request.state, "tenant_id", None), solo_activas=solo_activas))


@router.get("/api/crm/automatizacion/reglas/{regla_id}")
def api_get_regla(regla_id: int, request: Request):
    result = get_regla(getattr(request.state, "tenant_id", None), regla_id)
    if not result:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    return JSONResponse(result)


@router.post("/api/crm/automatizacion/reglas")
def api_create_regla(body: ReglaCreate, request: Request):
    return JSONResponse(
        create_regla(
            body.model_dump(),
            getattr(request.state, "tenant_id", None),
            actor=getattr(request.state, "user_name", ""),
        ),
        status_code=201,
    )


@router.patch("/api/crm/automatizacion/reglas/{regla_id}")
def api_update_regla(regla_id: int, body: ReglaUpdate, request: Request):
    result = update_regla(
        getattr(request.state, "tenant_id", None),
        regla_id,
        body.model_dump(exclude_none=True),
        actor=getattr(request.state, "user_name", ""),
    )
    if not result:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    return JSONResponse(result)


@router.delete("/api/crm/automatizacion/reglas/{regla_id}")
def api_delete_regla(regla_id: int, request: Request):
    if not delete_regla(getattr(request.state, "tenant_id", None), regla_id):
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    return JSONResponse({"ok": True})


@router.post("/api/crm/automatizacion/evaluar")
def api_evaluar_reglas(body: EvaluarRequest, request: Request):
    ejecutadas = evaluar_reglas(
        getattr(request.state, "tenant_id", None),
        body.evento_trigger,
        body.contexto,
        actor=getattr(request.state, "user_name", "sistema"),
    )
    return JSONResponse({"ejecutadas": len(ejecutadas), "detalle": ejecutadas})
