from fastapi import APIRouter, Request

from fastapi_modulo.modulos.aplicaciones.controladores.dependencies import (
    APPLICATIONS_PERMISSION_VIEW,
    require_applications_permission,
)
from fastapi_modulo.modulos.aplicaciones.modelos.schemas import AsyncTaskStateResponse
from fastapi_modulo.modulos.aplicaciones.servicios.task_queue_service import get_async_task_state

router = APIRouter()


@router.get("/api/aplicaciones/tareas/{task_name}/{task_id}", response_model=AsyncTaskStateResponse)
def aplicaciones_task_status(task_name: str, task_id: str, request: Request):
    require_applications_permission(request, APPLICATIONS_PERMISSION_VIEW)
    return get_async_task_state(task_name, task_id)


__all__ = ["router"]
