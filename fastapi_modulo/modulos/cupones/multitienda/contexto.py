"""
multitienda/contexto.py
-----------------------
Contexto de tenant: garantiza que toda operación se ejecute
bajo un tenant válido y activo.
"""

from functools import wraps
from typing import Callable

from cupones_fidelizacion.multitienda.tenant import TenantService
from cupones_fidelizacion.excepciones import AccesoDenegado


_tenant_service_global = TenantService()


def con_tenant(func: Callable) -> Callable:
    """
    Decorador que verifica que el primer argumento posicional o el
    keyword argument 'tenant_id' corresponda a una tienda activa.

    Uso:
        @con_tenant
        def mi_operacion(tenant_id: str, ...):
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        tenant_id = kwargs.get("tenant_id") or (args[1] if len(args) > 1 else None)
        if not tenant_id:
            raise ValueError("Se requiere tenant_id para esta operación.")
        _tenant_service_global.verificar_activa(tenant_id)
        return func(*args, **kwargs)
    return wrapper


def verificar_pertenencia(tenant_id_contexto: str, tenant_id_entidad: str) -> None:
    """
    Valida que una entidad pertenezca al tenant en contexto.
    Lanza AccesoDenegado si no coinciden.
    """
    if tenant_id_contexto != tenant_id_entidad:
        raise AccesoDenegado(
            "Intento de acceder a un recurso que no pertenece a esta tienda."
        )
