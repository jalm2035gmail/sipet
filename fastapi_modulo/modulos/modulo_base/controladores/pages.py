from __future__ import annotations

from fastapi import APIRouter, Request

from fastapi_modulo.modulos.modulo_base.bootstrap import response_builder

router = APIRouter()


@router.get("/modulo-base")
def modulo_base_page(request: Request):
    return response_builder.page(request, fallback="<p>No se pudo cargar modulo base.</p>")
