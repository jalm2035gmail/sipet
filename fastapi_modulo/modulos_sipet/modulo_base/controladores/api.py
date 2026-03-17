from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends

from fastapi_modulo.modulos_sipet.modulo_base.bootstrap import response_builder
from fastapi_modulo.modulos_sipet.modulo_base.controladores.dependencies import get_modulo_base_request_context, get_modulo_base_tenant_id
from fastapi_modulo.modulos_sipet.modulo_base.modelos.schemas import (
    APIErrorResponse,
    APIHealthResponse,
    APIResumenResponse,
    ModuloBaseHealthResponse,
    ModuloBaseRequestContext,
    ModuloBaseResumenResponse,
)
from fastapi_modulo.modulos_sipet.modulo_base.servicios.base_service import get_modulo_base_health, get_modulo_base_resumen

router = APIRouter()
logger = logging.getLogger(__name__)


def _log_health_check(context: ModuloBaseRequestContext) -> None:
    logger.debug("modulo_base health check", extra={"tenant_id": context.tenant_id, "user_role": context.user_role})


@router.get(
    "/api/modulo-base/health",
    response_model=APIHealthResponse,
    responses={422: {"model": APIErrorResponse}},
)
def modulo_base_health(
    background_tasks: BackgroundTasks,
    context: Annotated[ModuloBaseRequestContext, Depends(get_modulo_base_request_context)],
):
    background_tasks.add_task(_log_health_check, context)
    payload = ModuloBaseHealthResponse.model_validate(get_modulo_base_health())
    return response_builder.success_response(payload.model_dump())


@router.get(
    "/api/modulo-base/resumen",
    response_model=APIResumenResponse,
    responses={403: {"model": APIErrorResponse}, 422: {"model": APIErrorResponse}},
)
def modulo_base_resumen(tenant_id: Annotated[str, Depends(get_modulo_base_tenant_id)]):
    try:
        payload = ModuloBaseResumenResponse.model_validate(get_modulo_base_resumen(tenant_id))
    except PermissionError as exc:
        return response_builder.forbidden_response(str(exc))
    except ValueError as exc:
        return response_builder.error_response(
            str(exc),
            status_code=422,
        )
    return response_builder.success_response(payload.model_dump())
