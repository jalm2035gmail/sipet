"""
controladores/tasas_controller.py
─────────────────────────────────────────────────────────────────────────────
Gestión de tasas de interés del módulo frontend.

Rutas:
  GET  /api/frontend/tasas
  POST /api/frontend/tasas
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Request

from fastapi_modulo.modulos_sipet.frontend.modelos.frontend_schemas import TasaItem
from fastapi_modulo.modulos_sipet.frontend.modelos.frontend_store import (
    list_tasas as store_list_tasas,
    save_tasas as store_save_tasas,
)
from fastapi_modulo.modulos_sipet.frontend.servicios.builder_access import require_write
from fastapi_modulo.modulos_sipet.web.servicios.access_service import require_screen_access

router = APIRouter(prefix="/api/frontend", tags=["Tasas"])

_FRONTEND_BUILDER_SCREEN = "frontend.builder"


@router.get("/tasas")
def api_tasas_list(request: Request):
    require_screen_access(request, _FRONTEND_BUILDER_SCREEN, detail="Sin acceso al constructor frontend.")
    return {"success": True, "data": store_list_tasas()}


@router.post("/tasas")
async def api_tasas_save(request: Request, tasas: List[TasaItem]):
    """
    Guarda la lista completa de tasas.
    Pydantic valida que cada elemento tenga id, label y rate.
    """
    require_write(request)
    data = [t.model_dump() for t in tasas]
    return {"success": True, "data": store_save_tasas(data)}
