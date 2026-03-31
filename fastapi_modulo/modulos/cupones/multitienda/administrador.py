"""
multitienda/administrador.py
-----------------------------
Vista de administrador de plataforma: agrega datos de todos los tenants.
Solo debe ser usada por el operador de la plataforma, nunca por las tiendas.
"""

from typing import List, Dict
from cupones_fidelizacion.multitienda.tenant import TenantService
from cupones_fidelizacion.modelos_base import Tienda, EstadoGeneral


class AdministradorPlataforma:
    """
    Proporciona una vista consolidada de todos los tenants.
    No exponer este servicio a los dueños de tienda individuales.
    """

    def __init__(self, tenant_service: TenantService):
        self._tenant_svc = tenant_service

    def resumen_tiendas(self) -> Dict:
        """Retorna un resumen de todas las tiendas por estado."""
        todas = self._tenant_svc.listar_tiendas()
        resumen = {estado.value: 0 for estado in EstadoGeneral}
        for tienda in todas:
            resumen[tienda.estado.value] += 1
        return {
            "total": len(todas),
            "por_estado": resumen,
            "tiendas": [self._tienda_a_dict(t) for t in todas],
        }

    def buscar_tienda(self, nombre: str) -> List[Tienda]:
        todas = self._tenant_svc.listar_tiendas()
        return [t for t in todas if nombre.lower() in t.nombre.lower()]

    def suspender_tienda(self, tenant_id: str, motivo: str = "") -> Tienda:
        tienda = self._tenant_svc.suspender(tenant_id)
        # Aquí se podría emitir un evento de auditoría con el motivo
        return tienda

    def reactivar_tienda(self, tenant_id: str) -> Tienda:
        return self._tenant_svc.reactivar(tenant_id)

    @staticmethod
    def _tienda_a_dict(tienda: Tienda) -> Dict:
        return {
            "id": tienda.id,
            "nombre": tienda.nombre,
            "moneda": tienda.moneda,
            "estado": tienda.estado.value,
            "creado_en": tienda.creado_en.isoformat(),
        }
