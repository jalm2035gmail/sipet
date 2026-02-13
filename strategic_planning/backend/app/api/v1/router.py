from fastapi import APIRouter

from strategic_planning.backend.app.api.v1.endpoints import (
    auth,
    dashboard,
    kpis,
    personalizacion,
    poa,
    strategic,
    users,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(
    strategic.router, prefix="/strategic", tags=["strategic"]
)
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(kpis.router, prefix="/kpis", tags=["kpis"])
api_router.include_router(poa.router, prefix="/poa", tags=["poa"])
api_router.include_router(
    personalizacion.router, prefix="/personalizacion", tags=["personalizacion"]
)
