"""
fidelizacion/nivel_motor.py
----------------------------
Evalúa y actualiza el tier (nivel) del cliente según sus puntos acumulados.
"""

from typing import List, Optional

from cupones_fidelizacion.modelos_base import NivelFidelizacion, CuentaFidelizacion
from cupones_fidelizacion.fidelizacion.configurador import PlanFidelizacionService
from cupones_fidelizacion.fidelizacion.acumulador import CuentaRepositorio


class NivelMotor:
    """
    Determina el nivel de fidelización del cliente
    basándose en sus puntos acumulados históricos.
    """

    def __init__(
        self,
        plan_service: PlanFidelizacionService,
        cuenta_repo: Optional[CuentaRepositorio] = None,
    ):
        self._plan = plan_service
        self._cuenta_repo = cuenta_repo or CuentaRepositorio()

    def calcular_nivel(self, tenant_id: str, puntos_acumulados: int) -> NivelFidelizacion:
        """Determina el nivel correspondiente a los puntos acumulados."""
        plan = self._plan.obtener_plan(tenant_id)
        nivel_actual = NivelFidelizacion.BRONCE

        # Ordena los tiers de mayor a menor y asigna el primero que se alcanza
        tiers_ordenados = sorted(
            plan.tiers.items(), key=lambda x: x[1], reverse=True
        )
        for nivel, umbral in tiers_ordenados:
            if puntos_acumulados >= umbral:
                nivel_actual = nivel
                break

        return nivel_actual

    def evaluar_y_actualizar(self, tenant_id: str, cliente_id: str) -> CuentaFidelizacion:
        """
        Calcula el nivel correcto y actualiza la cuenta si cambió.
        Retorna la cuenta actualizada.
        """
        cuenta = self._cuenta_repo.obtener_por_cliente_y_tenant(cliente_id, tenant_id)
        if not cuenta:
            return None

        nivel_correcto = self.calcular_nivel(tenant_id, cuenta.puntos_acumulados_total)

        if nivel_correcto != cuenta.nivel:
            cuenta = self._cuenta_repo.actualizar(cuenta.id, nivel=nivel_correcto)

        return cuenta

    def evaluar_todos(self, tenant_id: str) -> List[dict]:
        """
        Evalúa y actualiza el nivel de todos los clientes del tenant.
        Útil para ejecutar en batch periódicamente.
        """
        cuentas = self._cuenta_repo.filtrar(tenant_id=tenant_id)
        resultados = []
        for cuenta in cuentas:
            nivel_anterior = cuenta.nivel
            cuenta_actualizada = self.evaluar_y_actualizar(tenant_id, cuenta.cliente_id)
            resultados.append({
                "cliente_id": cuenta.cliente_id,
                "nivel_anterior": nivel_anterior.value,
                "nivel_nuevo": cuenta_actualizada.nivel.value,
                "cambio": nivel_anterior != cuenta_actualizada.nivel,
            })
        return resultados

    def puntos_para_siguiente_nivel(
        self, tenant_id: str, puntos_actuales: int
    ) -> Optional[dict]:
        """
        Retorna cuántos puntos faltan para el siguiente nivel.
        None si ya está en el nivel máximo.
        """
        plan = self._plan.obtener_plan(tenant_id)
        tiers_ordenados = sorted(plan.tiers.items(), key=lambda x: x[1])

        for nivel, umbral in tiers_ordenados:
            if umbral > puntos_actuales:
                return {
                    "nivel_siguiente": nivel.value,
                    "puntos_necesarios": umbral,
                    "puntos_faltantes": umbral - puntos_actuales,
                }
        return None  # Ya está en platino
