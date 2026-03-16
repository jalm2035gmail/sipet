from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Request

from fastapi_modulo.modulos.modulo_base.bootstrap import response_builder
from fastapi_modulo.modulos.modulo_base.modelos.schemas import APIHealthResponse, APIResumenResponse
from fastapi_modulo.modulos.modulo_base.servicios.base_service import get_modulo_base_health, get_modulo_base_resumen

router = APIRouter()


def _noop_background_health_log() -> None:
    return None


@router.get("/api/modulo-base/health", response_model=APIHealthResponse)
def modulo_base_health(_request: Request, background_tasks: BackgroundTasks):
    background_tasks.add_task(_noop_background_health_log)
    return response_builder.success_response(get_modulo_base_health())


@router.get("/api/modulo-base/resumen", response_model=APIResumenResponse)
def modulo_base_resumen(request: Request):
    try:
        return response_builder.success_response(get_modulo_base_resumen(getattr(request.state, "tenant_id", None)))
    except PermissionError as exc:
        return response_builder.forbidden_response(str(exc))
    except ValueError as exc:
        return response_builder.error_response(str(exc), status_code=422)
