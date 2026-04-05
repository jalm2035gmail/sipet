"""
controladores/contact_controller.py
─────────────────────────────────────────────────────────────────────────────
Formulario de contacto público y gestión de mensajes en el builder.

Rutas:
  POST /api/frontend/contact                    → envío público (sin auth)
  GET  /api/frontend/contact                    → listado (requiere acceso)
  POST /api/frontend/contact/{contact_id}/read  → marcar como leído
"""

from __future__ import annotations

import uuid as _uuid

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from fastapi_modulo.modulos_sipet.frontend.modelos.frontend_schemas import ContactPayload
from fastapi_modulo.modulos_sipet.frontend.modelos.frontend_store import (
    create_contact as store_create_contact,
    list_contacts as store_list_contacts,
    mark_contact_read as store_mark_contact_read,
)
from fastapi_modulo.modulos_sipet.frontend.servicios.builder_access import require_write
from fastapi_modulo.modulos_sipet.web.servicios.access_service import require_screen_access

router = APIRouter(prefix="/api/frontend", tags=["Contact"])

_FRONTEND_BUILDER_SCREEN = "frontend.builder"


@router.post("/contact")
async def api_contact_submit(payload: ContactPayload):
    """
    Recibe un mensaje de contacto del sitio público.
    No requiere autenticación — endpoint público.
    Pydantic valida name, email (formato) y message automáticamente.
    """
    store_create_contact(
        id=str(_uuid.uuid4()),
        name=payload.name,
        email=payload.email,
        message=payload.message,
    )
    return {"success": True, "message": "Mensaje recibido, gracias."}


@router.get("/contact")
def api_contact_list(request: Request):
    require_screen_access(request, _FRONTEND_BUILDER_SCREEN, detail="Sin acceso al constructor frontend.")
    return {"success": True, "data": store_list_contacts()}


@router.post("/contact/{contact_id}/read")
def api_contact_mark_read(request: Request, contact_id: str):
    require_write(request)
    if not store_mark_contact_read(contact_id):
        return JSONResponse({"success": False, "error": "Mensaje no encontrado"}, status_code=404)
    return {"success": True}
