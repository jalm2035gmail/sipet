"""
fidelizacion/configurador.py
-----------------------------
Define y gestiona el plan de fidelización de cada tienda.
Cada tenant puede tener un único plan activo con sus propias reglas.
"""

from typing import Optional, Dict

from cupones_fidelizacion.modelos_base import ConfiguracionPlan, NivelFidelizacion
from cupones_fidelizacion.repositorio import RepositorioBase
from cupones_fidelizacion.excepciones import PlanNoConfigurado


class PlanRepositorio(RepositorioBase[ConfiguracionPlan]):

    def obtener_por_tenant(self, tenant_id: str) -> Optional[ConfiguracionPlan]:
        resultados = self.filtrar(tenant_id=tenant_id, activo=True)
        return resultados[0] if resultados else None


class PlanFidelizacionService:
    """
    Permite a cada tienda definir su propio programa de puntos y niveles.
    """

    def __init__(self, repositorio: Optional[PlanRepositorio] = None):
        self._repo = repositorio or PlanRepositorio()

    # ------------------------------------------------------------------
    # Creación y actualización
    # ------------------------------------------------------------------

    def configurar_plan(
        self,
        tenant_id: str,
        nombre: str,
        puntos_por_unidad_moneda: float = 1.0,
        unidad_moneda: float = 10.0,
        puntos_para_canje: int = 100,
        valor_punto_en_moneda: float = 0.10,
        dias_expiracion_puntos: Optional[int] = None,
        tiers: Optional[Dict[NivelFidelizacion, int]] = None,
    ) -> ConfiguracionPlan:
        """
        Crea o reemplaza el plan de fidelización del tenant.
        Si ya existe uno activo, lo desactiva primero.
        """
        plan_existente = self._repo.obtener_por_tenant(tenant_id)
        if plan_existente:
            self._repo.actualizar(plan_existente.id, activo=False)

        tiers_default = {
            NivelFidelizacion.BRONCE: 0,
            NivelFidelizacion.PLATA: 1000,
            NivelFidelizacion.ORO: 5000,
            NivelFidelizacion.PLATINO: 15000,
        }

        plan = ConfiguracionPlan(
            tenant_id=tenant_id,
            nombre=nombre,
            puntos_por_unidad_moneda=puntos_por_unidad_moneda,
            unidad_moneda=unidad_moneda,
            puntos_para_canje=puntos_para_canje,
            valor_punto_en_moneda=valor_punto_en_moneda,
            dias_expiracion_puntos=dias_expiracion_puntos,
            tiers=tiers or tiers_default,
        )
        return self._repo.guardar(plan)

    def obtener_plan(self, tenant_id: str) -> ConfiguracionPlan:
        plan = self._repo.obtener_por_tenant(tenant_id)
        if not plan:
            raise PlanNoConfigurado(
                f"La tienda '{tenant_id}' no tiene un plan de fidelización configurado."
            )
        return plan

    def plan_existe(self, tenant_id: str) -> bool:
        return self._repo.obtener_por_tenant(tenant_id) is not None

    def actualizar_tiers(
        self, tenant_id: str, nuevos_tiers: Dict[NivelFidelizacion, int]
    ) -> ConfiguracionPlan:
        plan = self.obtener_plan(tenant_id)
        return self._repo.actualizar(plan.id, tiers=nuevos_tiers)

    def actualizar_valor_punto(
        self, tenant_id: str, valor: float
    ) -> ConfiguracionPlan:
        if valor <= 0:
            raise ValueError("El valor del punto debe ser positivo.")
        plan = self.obtener_plan(tenant_id)
        return self._repo.actualizar(plan.id, valor_punto_en_moneda=valor)

    def desactivar_plan(self, tenant_id: str) -> None:
        plan = self.obtener_plan(tenant_id)
        self._repo.actualizar(plan.id, activo=False)
