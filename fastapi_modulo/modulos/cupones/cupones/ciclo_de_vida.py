"""
cupones/ciclo_de_vida.py
------------------------
Gestiona los cambios de estado de los cupones:
activar, pausar, expirar, revocar y sincronizar expiración automática.
"""

from datetime import datetime
from typing import List

from cupones_fidelizacion.modelos_base import Cupon, EstadoCupon
from cupones_fidelizacion.cupones.generador import CuponRepositorio
from cupones_fidelizacion.excepciones import CuponNoEncontrado
from cupones_fidelizacion.multitienda.contexto import verificar_pertenencia


class CuponCicloDeVida:
    """
    Controla las transiciones de estado de los cupones.
    """

    def __init__(self, repositorio: CuponRepositorio):
        self._repo = repositorio

    # ------------------------------------------------------------------
    # Transiciones de estado
    # ------------------------------------------------------------------

    def pausar(self, tenant_id: str, cupon_id: str) -> Cupon:
        cupon = self._obtener_verificado(tenant_id, cupon_id)
        if cupon.estado not in (EstadoCupon.ACTIVO,):
            raise ValueError(f"Solo se puede pausar un cupón activo (estado actual: {cupon.estado}).")
        return self._repo.actualizar(cupon_id, estado=EstadoCupon.PAUSADO)

    def reactivar(self, tenant_id: str, cupon_id: str) -> Cupon:
        cupon = self._obtener_verificado(tenant_id, cupon_id)
        if cupon.estado != EstadoCupon.PAUSADO:
            raise ValueError("Solo se puede reactivar un cupón pausado.")
        return self._repo.actualizar(cupon_id, estado=EstadoCupon.ACTIVO)

    def revocar(self, tenant_id: str, cupon_id: str) -> Cupon:
        """Revocación definitiva. No se puede deshacer."""
        cupon = self._obtener_verificado(tenant_id, cupon_id)
        if cupon.estado == EstadoCupon.REVOCADO:
            raise ValueError("El cupón ya está revocado.")
        return self._repo.actualizar(cupon_id, estado=EstadoCupon.REVOCADO)

    # ------------------------------------------------------------------
    # Expiración automática
    # ------------------------------------------------------------------

    def sincronizar_expiraciones(self, tenant_id: str, ahora: datetime = None) -> List[Cupon]:
        """
        Revisa todos los cupones activos del tenant y marca como expirados
        los que hayan superado su fecha de fin.
        Debe llamarse periódicamente (ej. tarea cron diaria).
        """
        ahora = ahora or datetime.utcnow()
        cupones = self._repo.listar_activos_por_tenant(tenant_id)
        expirados = []
        for cupon in cupones:
            if cupon.fecha_fin < ahora:
                self._repo.actualizar(cupon.id, estado=EstadoCupon.EXPIRADO)
                expirados.append(cupon)
        return expirados

    def sincronizar_todos_los_tenants(self, tenant_ids: List[str]) -> dict:
        """Ejecuta la sincronización de expiraciones para múltiples tenants."""
        ahora = datetime.utcnow()
        resultado = {}
        for tid in tenant_ids:
            expirados = self.sincronizar_expiraciones(tid, ahora)
            resultado[tid] = len(expirados)
        return resultado

    # ------------------------------------------------------------------
    # Privados
    # ------------------------------------------------------------------

    def _obtener_verificado(self, tenant_id: str, cupon_id: str) -> Cupon:
        cupon = self._repo.obtener(cupon_id)
        if not cupon:
            raise CuponNoEncontrado(f"Cupón '{cupon_id}' no encontrado.")
        verificar_pertenencia(tenant_id, cupon.tenant_id)
        return cupon
