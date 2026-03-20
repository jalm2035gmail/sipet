from __future__ import annotations

from fastapi import APIRouter

from fastapi_modulo.modulos.multitienda.marketplace.backend.main import app as marketplace_app

router = APIRouter()
router.mount("/multitienda", marketplace_app)

__all__ = ["router"]
