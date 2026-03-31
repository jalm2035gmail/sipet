"""
multitienda/tenant.py
---------------------
Gestión del ciclo de vida de los tenants (tiendas).
"""

from datetime import datetime
from typing import List, Optional

from cupones_fidelizacion.modelos_base import Tienda, EstadoGeneral
from cupones_fidelizacion.repositorio import RepositorioBase
from cupones_fidelizacion.excepciones import TenantNoEncontrado, TenantInactivo


class TenantRepositorio(RepositorioBase[Tienda]):

    def obtener_por_nombre(self, nombre: str) -> Optional[Tienda]:
        resultados = self.filtrar(nombre=nombre)
        return resultados[0] if resultados else None

    def listar_activos(self) -> List[Tienda]:
        return self.filtrar(estado=EstadoGeneral.ACTIVO)


class TenantService:
    """
    Servicio principal para la gestión de tiendas.
    Punto de entrada para registrar, activar y suspender tenants.
    """

    def __init__(self, repositorio: Optional[TenantRepositorio] = None):
        self._repo = repositorio or TenantRepositorio()

    # ------------------------------------------------------------------
    # Creación
    # ------------------------------------------------------------------

    def registrar_tienda(
        self,
        nombre: str,
        moneda: str = "MXN",
        zona_horaria: str = "America/Mexico_City",
        configuracion_extra: Optional[dict] = None,
    ) -> Tienda:
        """Registra una nueva tienda en la plataforma."""
        if self._repo.obtener_por_nombre(nombre):
            raise ValueError(f"Ya existe una tienda con el nombre '{nombre}'.")
        tienda = Tienda(
            nombre=nombre,
            moneda=moneda,
            zona_horaria=zona_horaria,
            configuracion_extra=configuracion_extra or {},
        )
        return self._repo.guardar(tienda)

    # ------------------------------------------------------------------
    # Consulta
    # ------------------------------------------------------------------

    def obtener(self, tenant_id: str) -> Tienda:
        tienda = self._repo.obtener(tenant_id)
        if not tienda:
            raise TenantNoEncontrado(f"Tienda '{tenant_id}' no encontrada.")
        return tienda

    def verificar_activa(self, tenant_id: str) -> Tienda:
        """Obtiene la tienda y lanza excepción si no está activa."""
        tienda = self.obtener(tenant_id)
        if tienda.estado != EstadoGeneral.ACTIVO:
            raise TenantInactivo(
                f"La tienda '{tienda.nombre}' no está activa (estado: {tienda.estado})."
            )
        return tienda

    def listar_tiendas(self) -> List[Tienda]:
        return self._repo.listar_todos()

    def listar_activas(self) -> List[Tienda]:
        return self._repo.listar_activos()

    # ------------------------------------------------------------------
    # Gestión de estado
    # ------------------------------------------------------------------

    def suspender(self, tenant_id: str) -> Tienda:
        tienda = self.obtener(tenant_id)
        return self._repo.actualizar(tenant_id, estado=EstadoGeneral.SUSPENDIDO)

    def reactivar(self, tenant_id: str) -> Tienda:
        tienda = self.obtener(tenant_id)
        return self._repo.actualizar(tenant_id, estado=EstadoGeneral.ACTIVO)

    def eliminar(self, tenant_id: str) -> bool:
        self.obtener(tenant_id)  # valida existencia
        self._repo.actualizar(tenant_id, estado=EstadoGeneral.ELIMINADO)
        return True

    # ------------------------------------------------------------------
    # Configuración extra
    # ------------------------------------------------------------------

    def actualizar_configuracion(self, tenant_id: str, **campos) -> Tienda:
        tienda = self.obtener(tenant_id)
        campos_validos = {k: v for k, v in campos.items() if hasattr(tienda, k)}
        return self._repo.actualizar(tenant_id, **campos_validos)
