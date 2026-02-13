from typing import Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission
from app.core.permissions import Permission
from app.services.dashboard_service import DashboardService
from app.templates.api import ApiResponseTemplate

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/strategic-oversight")
async def strategic_dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(require_permission(Permission.STRATEGIC_VIEW_PLANS)),
) -> Dict:
    """Retorna métricas para el dashboard de progreso estratégico."""
    data = DashboardService.get_strategic_overview(db)
    return ApiResponseTemplate.success(
        data={
            "overview": data,
            "charts": {
                "status_distribution": [
                    {"status": status, "count": count}
                    for status, count in data["status_counts"].items()
                ],
                "progress_by_status": [
                    {"status": status, "progress": prog}
                    for status, prog in data["status_progress"].items()
                ],
            },
        },
        message="Dashboard estratégico actualizado",
    )
