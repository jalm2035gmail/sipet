from fastapi import APIRouter, HTTPException, Request

from fastapi_modulo.modulos.aplicaciones.controladores.dependencies import (
    APPLICATIONS_PERMISSION_STATE_EDIT,
    APPLICATIONS_PERMISSION_VIEW,
    require_applications_permission,
    request_actor_context,
)
from fastapi_modulo.modulos.aplicaciones.modelos.schemas import ModuleCatalogItem, ModuleToggleSchema
from fastapi_modulo.modulos.aplicaciones.servicios.catalog_service import decorate_modules_payload
from fastapi_modulo.modulos.aplicaciones.servicios.state_service import update_module_state

router = APIRouter()


@router.get("/api/system/modules", response_model=list[ModuleCatalogItem], include_in_schema=False)
@router.get("/api/aplicaciones/modulos", response_model=list[ModuleCatalogItem])
def aplicaciones_list(request: Request):
    require_applications_permission(request, APPLICATIONS_PERMISSION_VIEW)
    return decorate_modules_payload()


@router.put("/api/system/modules/{module_key}", response_model=ModuleCatalogItem, include_in_schema=False)
@router.put("/api/aplicaciones/modulos/{module_key}", response_model=ModuleCatalogItem)
def aplicaciones_update(module_key: str, body: ModuleToggleSchema, request: Request):
    require_applications_permission(request, APPLICATIONS_PERMISSION_STATE_EDIT)
    actor = request_actor_context(request)
    try:
        return update_module_state(
            module_key,
            body.enabled,
            user_id=actor["user_id"],
            tenant_id=actor["tenant_id"],
            ip=actor["ip"],
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


__all__ = ["router"]
