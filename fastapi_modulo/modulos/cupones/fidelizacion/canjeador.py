"""
fidelizacion/canjeador.py
--------------------------
Permite al cliente convertir sus puntos en descuento monetario.
Opera solo dentro de la misma tienda donde se acumularon los puntos.
"""

from typing import Optional

from cupones_fidelizacion.modelos_base import MovimientoPuntos, TipoMovimientoPuntos
from cupones_fidelizacion.fidelizacion.configurador import PlanFidelizacionService
from cupones_fidelizacion.fidelizacion.acumulador import (
    CuentaRepositorio, MovimientoRepositorio
)
from cupones_fidelizacion.excepciones import (
    CuentaNoEncontrada, PuntosInsuficientes, CanjeMinimNoAlcanzado
)


class ResultadoCanje:
    def __init__(
        self,
        puntos_canjeados: int,
        valor_descuento: float,
        saldo_restante: int,
    ):
        self.puntos_canjeados = puntos_canjeados
        self.valor_descuento = valor_descuento
        self.saldo_restante = saldo_restante

    def to_dict(self):
        return {
            "puntos_canjeados": self.puntos_canjeados,
            "valor_descuento": round(self.valor_descuento, 2),
            "saldo_restante": self.saldo_restante,
        }


class PuntosCanjeador:
    """
    Convierte puntos acumulados en valor de descuento.
    Solo opera dentro del mismo tenant donde se acumularon.
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

    def preview_canje(
        self,
        tenant_id: str,
        cliente_id: str,
        puntos_a_canjear: int,
    ) -> ResultadoCanje:
        """Muestra el valor del canje sin ejecutarlo."""
        plan = self._plan.obtener_plan(tenant_id)
        cuenta = self._obtener_cuenta(tenant_id, cliente_id)
        self._validar_canje(plan, cuenta, puntos_a_canjear)
        valor = puntos_a_canjear * plan.valor_punto_en_moneda
        return ResultadoCanje(
            puntos_canjeados=puntos_a_canjear,
            valor_descuento=valor,
            saldo_restante=cuenta.puntos_actuales - puntos_a_canjear,
        )

    def canjear(
        self,
        tenant_id: str,
        cliente_id: str,
        puntos_a_canjear: int,
        referencia: Optional[str] = None,
    ) -> ResultadoCanje:
        """
        Debita los puntos de la cuenta y retorna el valor del descuento obtenido.
        """
        plan = self._plan.obtener_plan(tenant_id)
        cuenta = self._obtener_cuenta(tenant_id, cliente_id)
        self._validar_canje(plan, cuenta, puntos_a_canjear)

        valor_descuento = puntos_a_canjear * plan.valor_punto_en_moneda
        nuevo_saldo = cuenta.puntos_actuales - puntos_a_canjear

        self._cuenta_repo.actualizar(
            cuenta.id,
            puntos_actuales=nuevo_saldo,
            puntos_canjeados_total=cuenta.puntos_canjeados_total + puntos_a_canjear,
        )

        movimiento = MovimientoPuntos(
            cuenta_id=cuenta.id,
            tenant_id=tenant_id,
            tipo=TipoMovimientoPuntos.CANJE,
            puntos=-puntos_a_canjear,
            saldo_resultante=nuevo_saldo,
            referencia_transaccion=referencia,
            descripcion=f"Canje de {puntos_a_canjear} pts → ${valor_descuento:.2f} de descuento",
        )
        self._movimiento_repo.guardar(movimiento)

        return ResultadoCanje(
            puntos_canjeados=puntos_a_canjear,
            valor_descuento=valor_descuento,
            saldo_restante=nuevo_saldo,
        )

    def _validar_canje(self, plan, cuenta, puntos: int) -> None:
        if puntos < plan.puntos_para_canje:
            raise CanjeMinimNoAlcanzado(
                f"El mínimo de canje es {plan.puntos_para_canje} puntos. "
                f"Intentas canjear {puntos}."
            )
        if puntos > cuenta.puntos_actuales:
            raise PuntosInsuficientes(
                f"No tienes suficientes puntos. Saldo: {cuenta.puntos_actuales}, "
                f"solicitado: {puntos}."
            )

    def _obtener_cuenta(self, tenant_id: str, cliente_id: str):
        cuenta = self._cuenta_repo.obtener_por_cliente_y_tenant(cliente_id, tenant_id)
        if not cuenta:
            raise CuentaNoEncontrada(
                f"El cliente '{cliente_id}' no tiene cuenta en esta tienda."
            )
        return cuenta
