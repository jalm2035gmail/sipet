from fastapi_modulo.modulos.modulo_base.servicios.base_service import (
    get_modulo_base_health,
    get_modulo_base_resumen,
)

__all__ = ["get_modulo_base_health", "get_modulo_base_resumen"]
from fastapi_modulo.modulos.modulo_base.servicios.base_service import (
    ModuloBaseService,
    get_modulo_base_health,
    get_modulo_base_resumen,
    service,
)

__all__ = [
    "ModuloBaseService",
    "get_modulo_base_health",
    "get_modulo_base_resumen",
    "service",
]
