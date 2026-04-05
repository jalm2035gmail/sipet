from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from fastapi_modulo.modulos.crm.modelos.schemas import NotaCreate
from fastapi_modulo.modulos.crm.servicios.nota_service import archivar_nota, create_nota, delete_nota, list_notas_by_tenant

router = APIRouter()


@router.get("/api/crm/notas")
def api_list_notas(request: Request, contacto_id: int = 0, oportunidad_id: int = 0):
    return JSONResponse(list_notas_by_tenant(getattr(request.state, "tenant_id", None), contacto_id or None, oportunidad_id or None))


@router.post("/api/crm/notas")
def api_create_nota(body: NotaCreate, request: Request):
    return JSONResponse(
        create_nota(
            body.model_dump(),
            getattr(request.state, "tenant_id", None),
            actor=getattr(request.state, "user_name", ""),
        ),
        status_code=201,
    )


@router.delete("/api/crm/notas/{nota_id}")
def api_delete_nota(nota_id: int, request: Request):
    if not delete_nota(nota_id, getattr(request.state, "tenant_id", None)):
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    return JSONResponse({"ok": True})


@router.patch("/api/crm/notas/{nota_id}/archivar")
def api_archivar_nota(nota_id: int, request: Request):
    result = archivar_nota(
        nota_id,
        getattr(request.state, "tenant_id", None),
        actor=getattr(request.state, "user_name", ""),
    )
    if not result:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    return JSONResponse(result)
