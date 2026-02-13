from fastapi import APIRouter, Depends
from app.schemas.operational.poa import ActivityCreate
from app.services.poa_service import POAService, get_poa_service

router = APIRouter(prefix="/poas", tags=["poa"])

@router.post("/{poa_id}/activities/")
async def create_activity(
    poa_id: int,
    activity: ActivityCreate,
    service: POAService = Depends(get_poa_service)
):
    """Crear actividad en el POA"""
    return await service.create_activity(poa_id, activity)

@router.get("/{poa_id}/gantt")
async def get_poa_gantt(poa_id: int, service: POAService = Depends(get_poa_service)):
    """Obtener datos para diagrama de Gantt"""
    return await service.get_gantt_data(poa_id)

@router.put("/activities/{activity_id}/progress")
async def update_activity_progress(
    activity_id: int,
    progress: float,
    service: POAService = Depends(get_poa_service),
):
    """Actualizar progreso de actividad"""
    return await service.update_progress(activity_id, progress)
