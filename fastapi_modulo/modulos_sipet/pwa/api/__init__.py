"""
api/__init__.py — Registro central de routers del módulo PWA v2.

Uso en main.py (o en el controlador SIPET que monta el módulo):

    from api import build_router
    app.include_router(build_router(), prefix="/api/v2/pwa", tags=["pwa"])
"""
from fastapi import APIRouter

from api import conversations, notifications, sipet


def build_router() -> APIRouter:
    root = APIRouter()
    root.include_router(sipet.router,         prefix="/sipet",         tags=["sipet"])
    root.include_router(conversations.router, prefix="/conversations",  tags=["conversations"])
    root.include_router(notifications.router, prefix="/notifications",  tags=["notifications"])
    return root


__all__ = ["build_router"]
