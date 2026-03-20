from __future__ import annotations

__all__ = ["router"]


def __getattr__(name: str):
    if name == "router":
        from fastapi_modulo.modulos.capacitacion.controladores.capacitacion import router

        return router
    raise AttributeError(name)
