"""
fidelizacion/acumulador.py
--------------------------
Calcula y acredita puntos a la cuenta del cliente tras una compra.
"""

import math
from typing import Optional

from cupones_fidelizacion.modelos_base import (
    CuentaFidelizacion, MovimientoPuntos, TipoMovimientoPuntos
)
from cupones_fidelizacion.fidelizacion.configurador import PlanFidelizacionService
from cupones_fidelizacion.repositorio import RepositorioBase
from cupones_fidelizacion.excepciones import CuentaNoEncontrada


class CuentaRepositorio(RepositorioBase[CuentaFidelizacion]):

    def obtener_por_cliente_y_tenant(
        self, cliente_id: str, tenant_id: str
    ) -> Optional[CuentaFidelizacion]:
        resultados = self.filtrar(cliente_id=cliente_id, tenant_id=tenant_id)
        return resultados[0] if resultados else None


class MovimientoRepositorio(RepositorioBase[MovimientoPuntos]):

    def listar_por_cuenta(self, cuenta_id: str):
        return self.filtrar(cuenta_id=cuenta_id)


class PuntosAcumulador:
    """
    Otorga puntos al cliente según las reglas del plan de su tienda.
    """

    def __init__(
        self,
        plan_service: PlanFidelizacionService,
        cuenta_repo: Optional[CuentaRepositorio] = None,
        movimiento_repo: Optional[MovimientoRepositorio] = None,
    ):
        self._plan = plan_service
        self._cuenta_repo = cuenta_repo or CuentaRepositorio()
        self._movimiento_repo = movimiento_repo or MovimientoRepositorio()

    def acreditar(
        self,
        tenant_id: str,
        cliente_id: str,
        monto_compra: float,
        referencia: Optional[str] = None,
    ) -> MovimientoPuntos:
        """
        Calcula los puntos que corresponden al monto de compra y los acredita.
        Crea la cuenta si el cliente no tiene una aún.
        """
        plan = self._plan.obtener_plan(tenant_id)
        puntos_ganados = self._calcular_puntos(plan, monto_compra)

        cuenta = self._obtener_o_crear_cuenta(tenant_id, cliente_id)

        nuevo_saldo = cuenta.puntos_actuales + puntos_ganados
        self._cuenta_repo.actualizar(
            cuenta.id,
            puntos_actuales=nuevo_saldo,
            puntos_acumulados_total=cuenta.puntos_acumulados_total + puntos_ganados,
        )

        movimiento = MovimientoPuntos(
            cuenta_id=cuenta.id,
            tenant_id=tenant_id,
            tipo=TipoMovimientoPuntos.ACUMULACION,
            puntos=puntos_ganados,
            saldo_resultante=nuevo_saldo,
            referencia_transaccion=referencia,
            descripcion=f"Compra por ${monto_compra:.2f} — {puntos_ganados} pts ganados",
        )
        return self._movimiento_repo.guardar(movimiento)

    def _calcular_puntos(self, plan, monto: float) -> int:
        """Aplica la regla: X puntos por cada Y pesos gastados."""
        unidades = monto / plan.unidad_moneda
        return math.floor(unidades * plan.puntos_por_unidad_moneda)

    def _obtener_o_crear_cuenta(
        self, tenant_id: str, cliente_id: str
    ) -> CuentaFidelizacion:
        cuenta = self._cuenta_repo.obtener_por_cliente_y_tenant(cliente_id, tenant_id)
        if not cuenta:
            cuenta = CuentaFidelizacion(tenant_id=tenant_id, cliente_id=cliente_id)
            self._cuenta_repo.guardar(cuenta)
        return cuenta

    def obtener_saldo(self, tenant_id: str, cliente_id: str) -> int:
        cuenta = self._cuenta_repo.obtener_por_cliente_y_tenant(cliente_id, tenant_id)
        if not cuenta:
            return 0
        return cuenta.puntos_actuales
