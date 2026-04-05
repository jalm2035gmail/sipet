from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.exc import IntegrityError

from fastapi_modulo.modulos.multiempresa.controladores.multiempresa_access_service import (
    get_me_scope,
    get_scope_info,
    require_full_access,
)
from fastapi_modulo.modulos.multiempresa.modelos.me_models import EmpresaCreate, EmpresaUpdate
from fastapi_modulo.modulos.multiempresa.modelos.me_store import (
    create_empresa,
    delete_empresa,
    get_empresa,
    get_logo_path,
    get_me_consolidado,
    get_me_kpis,
    list_empresas,
    save_logo,
    update_empresa,
)

router = APIRouter()


# ── Scope ─────────────────────────────────────────────────────────────────────

@router.get("/api/multiempresa/scope")
def api_scope(request: Request):
    return get_scope_info(request)


# ── Logos ─────────────────────────────────────────────────────────────────────

@router.get("/api/multiempresa/logos/{filename}")
def serve_logo(filename: str):
    path = get_logo_path(filename)
    if not path:
        raise HTTPException(status_code=404, detail="Logo no encontrado")
    return FileResponse(str(path))


# ── KPIs ──────────────────────────────────────────────────────────────────────

@router.get("/api/multiempresa/kpis")
def api_kpis(request: Request):
    return get_me_kpis(tenant_filter=get_me_scope(request))


# ── Consolidado ───────────────────────────────────────────────────────────────

@router.get("/api/multiempresa/consolidado")
def api_consolidado(request: Request):
    return get_me_consolidado(tenant_filter=get_me_scope(request))


# ── Empresas CRUD ─────────────────────────────────────────────────────────────

@router.get("/api/multiempresa/empresas")
def api_list_empresas(
    request: Request,
    estado: str = Query(default=""),
    q: str = Query(default=""),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    sort: str = Query(default="nombre"),
):
    scope = get_me_scope(request)
    return list_empresas(
        estado=estado or None,
        tenant_filter=scope,
        q=q or None,
        limit=limit,
        offset=offset,
        sort=sort,
    )


@router.get("/api/multiempresa/empresas/{empresa_id}")
def api_get_empresa(empresa_id: int, request: Request):
    obj = get_empresa(empresa_id, tenant_filter=get_me_scope(request))
    if not obj:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return obj


@router.post("/api/multiempresa/empresas", status_code=201)
def api_create_empresa(body: EmpresaCreate, request: Request):
    require_full_access(request)
    try:
        return create_empresa(body.model_dump(exclude_none=True))
    except IntegrityError as e:
        err = str(e.orig).lower() if e.orig else ""
        if "codigo" in err or "UNIQUE" in str(e):
            raise HTTPException(status_code=409, detail="Ya existe una empresa con ese código o tenant_id")
        raise HTTPException(status_code=409, detail="Conflicto al crear la empresa")


@router.put("/api/multiempresa/empresas/{empresa_id}")
def api_update_empresa(empresa_id: int, body: EmpresaUpdate, request: Request):
    try:
        obj = update_empresa(empresa_id, body.model_dump(exclude_none=True), tenant_filter=get_me_scope(request))
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Conflicto al actualizar")
    if not obj:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return obj


@router.delete("/api/multiempresa/empresas/{empresa_id}", status_code=204)
def api_delete_empresa(empresa_id: int, request: Request):
    require_full_access(request)
    if not delete_empresa(empresa_id):
        raise HTTPException(status_code=404, detail="Empresa no encontrada")


# ── Logo upload ───────────────────────────────────────────────────────────────

@router.post("/api/multiempresa/empresas/{empresa_id}/logo")
async def api_upload_logo(empresa_id: int, request: Request, file: UploadFile = File(...)):
    scope = get_me_scope(request)
    data = await file.read()
    content_type = file.content_type or "application/octet-stream"
    try:
        obj = save_logo(empresa_id, data, content_type, tenant_filter=scope)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not obj:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return obj
