"""
fidelizacion/vencimiento.py
----------------------------
Maneja la caducidad de puntos inactivos según la política del tenant.
"""

from datetime import datetime, timedelta
from typing import List

from cupones_fidelizacion.modelos_base import MovimientoPuntos, TipoMovimientoPuntos
from cupones_fidelizacion.fidelizacion.configurador import PlanFidelizacionService
from cupones_fidelizacion.fidelizacion.acumulador import (
    CuentaRepositorio, MovimientoRepositorio
)


class VencimientoPuntos:
    """
    Expira puntos de cuentas inactivas según la configuración del plan.
    Debe ejecutarse periódicamente (job diario o semanal).
    """

    def __init__(
        self,
        plan_service: PlanFidelizacionService,
        cuenta_repo: CuentaRepositorio,
        movimiento_repo: MovimientoRepositorio,
    ):
        self._plan = plan_service
        self._cuenta_repo = cuenta_repo
        self._movimiento_repo = movimiento_repo

    def ejecutar(self, tenant_id: str, ahora: datetime = None) -> List[dict]:
        """
        Aplica la política de expiración para el tenant.
        Retorna lista de cuentas afectadas.
        """
        ahora = ahora or datetime.utcnow()
        plan = self._plan.obtener_plan(tenant_id)

        if plan.dias_expiracion_puntos is None:
            return []  # Este tenant no tiene expiración configurada

        limite = ahora - timedelta(days=plan.dias_expiracion_puntos)
        cuentas = self._cuenta_repo.filtrar(tenant_id=tenant_id)
        afectadas = []

        for cuenta in cuentas:
            if cuenta.ultima_actividad < limite and cuenta.puntos_actuales > 0:
                puntos_a_expirar = cuenta.puntos_actuales

                self._cuenta_repo.actualizar(cuenta.id, puntos_actuales=0)

                movimiento = MovimientoPuntos(
                    cuenta_id=cuenta.id,
                    tenant_id=tenant_id,
                    tipo=TipoMovimientoPuntos.EXPIRACION,
                    puntos=-puntos_a_expirar,
                    saldo_resultante=0,
                    descripcion=(
                        f"Expiración por inactividad mayor a "
                        f"{plan.dias_expiracion_puntos} días"
                    ),
                )
                self._movimiento_repo.guardar(movimiento)

                afectadas.append({
                    "cliente_id": cuenta.cliente_id,
                    "puntos_expirados": puntos_a_expirar,
                    "ultima_actividad": cuenta.ultima_actividad.isoformat(),
                })

        return afectadas
