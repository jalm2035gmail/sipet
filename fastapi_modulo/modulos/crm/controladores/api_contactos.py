from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from fastapi_modulo.modulos.crm.modelos.schemas import ContactoCreate, ContactoUpdate
from fastapi_modulo.modulos.crm.servicios.contacto_service import (
    archivar_contacto,
    convertir_contacto_a_cliente,
    create_contacto,
    delete_contacto,
    get_contacto,
    list_contactos_by_tenant,
    update_contacto,
)

router = APIRouter()


@router.get("/api/crm/contactos")
def api_list_contactos(request: Request, tipo: str = "", q: str = "", responsable: str = "", sucursal: str = "", skip: int = 0, limit: int = 100):
    return JSONResponse(list_contactos_by_tenant(getattr(request.state, "tenant_id", None), tipo or None, q or None, responsable or None, sucursal or None, skip, limit))


@router.get("/api/crm/contactos/{contacto_id}")
def api_get_contacto(contacto_id: int, request: Request):
    obj = get_contacto(contacto_id, getattr(request.state, "tenant_id", None))
    if not obj:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return JSONResponse(obj)


@router.post("/api/crm/contactos")
def api_create_contacto(body: ContactoCreate, request: Request):
    try:
        return JSONResponse(
            create_contacto(
                body.model_dump(),
                getattr(request.state, "tenant_id", None),
                actor=getattr(request.state, "user_name", ""),
            ),
            status_code=201,
        )
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Ya existe un contacto con ese email")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.put("/api/crm/contactos/{contacto_id}")
def api_update_contacto(contacto_id: int, body: ContactoUpdate, request: Request):
    try:
        result = update_contacto(
            contacto_id,
            body.model_dump(exclude_unset=True),
            getattr(request.state, "tenant_id", None),
            actor=getattr(request.state, "user_name", ""),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if not result:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return JSONResponse(result)


@router.delete("/api/crm/contactos/{contacto_id}")
def api_delete_contacto(contacto_id: int, request: Request):
    if not delete_contacto(contacto_id, getattr(request.state, "tenant_id", None)):
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return JSONResponse({"ok": True})


@router.post("/api/crm/contactos/{contacto_id}/convertir-cliente")
def api_convertir_contacto_a_cliente(contacto_id: int, request: Request):
    result = convertir_contacto_a_cliente(
        contacto_id,
        getattr(request.state, "tenant_id", None),
        actor=getattr(request.state, "user_name", ""),
    )
    if not result:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return JSONResponse(result)


@router.patch("/api/crm/contactos/{contacto_id}/archivar")
def api_archivar_contacto(contacto_id: int, request: Request):
    result = archivar_contacto(
        contacto_id,
        getattr(request.state, "tenant_id", None),
        actor=getattr(request.state, "user_name", ""),
    )
    if not result:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return JSONResponse(result)
