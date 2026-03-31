"""
clientes/cuenta.py
------------------
Gestión de la cuenta de fidelización del cliente en cada tienda.
Un cliente puede tener cuentas en múltiples tiendas (registros independientes).
"""

from typing import List, Optional
from datetime import datetime

from cupones_fidelizacion.modelos_base import CuentaFidelizacion, NivelFidelizacion
from cupones_fidelizacion.fidelizacion.acumulador import CuentaRepositorio, MovimientoRepositorio
from cupones_fidelizacion.fidelizacion.nivel_motor import NivelMotor
from cupones_fidelizacion.fidelizacion.configurador import PlanFidelizacionService
from cupones_fidelizacion.excepciones import CuentaNoEncontrada


class CuentaClienteService:
    """
    Vista del cliente sobre su cuenta de fidelización en una tienda específica.
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
        self._nivel_motor = NivelMotor(plan_service, self._cuenta_repo)

    def obtener_cuenta(self, tenant_id: str, cliente_id: str) -> CuentaFidelizacion:
        cuenta = self._cuenta_repo.obtener_por_cliente_y_tenant(cliente_id, tenant_id)
        if not cuenta:
            raise CuentaNoEncontrada(
                f"El cliente '{cliente_id}' no tiene cuenta en esta tienda."
            )
        return cuenta

    def resumen(self, tenant_id: str, cliente_id: str) -> dict:
        """Retorna un resumen completo de la cuenta del cliente."""
        cuenta = self.obtener_cuenta(tenant_id, cliente_id)
        plan = self._plan.obtener_plan(tenant_id)

        siguiente = self._nivel_motor.puntos_para_siguiente_nivel(
            tenant_id, cuenta.puntos_acumulados_total
        )
        valor_saldo = cuenta.puntos_actuales * plan.valor_punto_en_moneda

        return {
            "cliente_id": cliente_id,
            "tenant_id": tenant_id,
            "nivel": cuenta.nivel.value,
            "puntos_actuales": cuenta.puntos_actuales,
            "valor_saldo_moneda": round(valor_saldo, 2),
            "puntos_acumulados_total": cuenta.puntos_acumulados_total,
            "puntos_canjeados_total": cuenta.puntos_canjeados_total,
            "siguiente_nivel": siguiente,
            "ultima_actividad": cuenta.ultima_actividad.isoformat(),
            "miembro_desde": cuenta.creado_en.isoformat(),
        }

    def listar_tiendas_del_cliente(self, cliente_id: str) -> List[dict]:
        """Retorna todas las tiendas donde el cliente tiene cuenta."""
        todas = self._cuenta_repo.filtrar(cliente_id=cliente_id)
        return [
            {
                "tenant_id": c.tenant_id,
                "nivel": c.nivel.value,
                "puntos_actuales": c.puntos_actuales,
            }
            for c in todas
        ]

    def ajuste_manual(
        self,
        tenant_id: str,
        cliente_id: str,
        puntos: int,
        motivo: str,
        operador_id: str,
    ) -> dict:
        """
        Permite a un administrador de tienda ajustar el saldo manualmente.
        puntos puede ser positivo (agregar) o negativo (quitar).
        """
        from cupones_fidelizacion.modelos_base import MovimientoPuntos, TipoMovimientoPuntos
        cuenta = self.obtener_cuenta(tenant_id, cliente_id)
        nuevo_saldo = max(0, cuenta.puntos_actuales + puntos)

        self._cuenta_repo.actualizar(cuenta.id, puntos_actuales=nuevo_saldo)

        movimiento = MovimientoPuntos(
            cuenta_id=cuenta.id,
            tenant_id=tenant_id,
            tipo=TipoMovimientoPuntos.AJUSTE_MANUAL,
            puntos=puntos,
            saldo_resultante=nuevo_saldo,
            descripcion=f"Ajuste manual por {operador_id}: {motivo}",
        )
        self._movimiento_repo.guardar(movimiento)

        return {
            "puntos_ajustados": puntos,
            "saldo_anterior": cuenta.puntos_actuales,
            "saldo_nuevo": nuevo_saldo,
            "motivo": motivo,
        }
