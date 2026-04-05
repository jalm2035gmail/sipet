from fastapi_modulo.modulos.multiempresa.controladores.multiempresa import router
from fastapi_modulo.modulos.multiempresa.modelos.me_store import ensure_me_schema

ensure_me_schema()

__all__ = ["router"]
