"""
programa_grupo/puntos_compartidos.py
--------------------------------------
Acumulación y canje de puntos válidos en cualquier tienda del mismo grupo.
"""

import math
from typing import Optional

from cupones_fidelizacion.programa_grupo.grupo_tenant import GrupoTenantService
from cupones_fidelizacion.fidelizacion.configurador import PlanFidelizacionService
from cupones_fidelizacion.fidelizacion.acumulador import (
    CuentaRepositorio, MovimientoRepositorio, PuntosAcumulador
)
from cupones_fidelizacion.fidelizacion.canjeador import PuntosCanjeador, ResultadoCanje
from cupones_fidelizacion.modelos_base import (
    CuentaFidelizacion, MovimientoPuntos, TipoMovimientoPuntos
)
from cupones_fidelizacion.excepciones import (
    PuntosInsuficientes, CanjeMinimNoAlcanzado, CuentaNoEncontrada
)

# Tenant especial que representa la cuenta de grupo del cliente
GRUPO_TENANT_PREFIX = "grupo:"


class PuntosCompartidosService:
    """
    Gestiona puntos acumulados en el contexto de un grupo de tiendas.
    El cliente tiene UNA cuenta de grupo (independiente de las cuentas por tienda).
    """

    def __init__(
        self,
        grupo_service: GrupoTenantService,
        plan_service: PlanFidelizacionService,
        cuenta_repo: Optional[CuentaRepositorio] = None,
        movimiento_repo: Optional[MovimientoRepositorio] = None,
    ):
        self._grupo_svc = grupo_service
        self._plan_svc = plan_service
        self._cuenta_repo = cuenta_repo or CuentaRepositorio()
        self._movimiento_repo = movimiento_repo or MovimientoRepositorio()

    # ------------------------------------------------------------------
    # Acumulación grupal
    # ------------------------------------------------------------------

    def acreditar_compra(
        self,
        tenant_id_origen: str,
        cliente_id: str,
        monto_compra: float,
        referencia: Optional[str] = None,
    ) -> Optional[MovimientoPuntos]:
        """
        Acredita puntos de grupo después de una compra en cualquier tienda miembro.
        Si la tienda no pertenece a ningún grupo, retorna None sin error.
        """
        grupo = self._grupo_svc.obtener_grupo_de_tienda(tenant_id_origen)
        if not grupo:
            return None  # Tienda no participa en ningún grupo

        # Usar el plan del tenant de origen para calcular los puntos
        plan = self._plan_svc.obtener_plan(tenant_id_origen)
        proporcion = grupo.proporcion_puntos.get(tenant_id_origen, 1.0)
        puntos_base = math.floor((monto_compra / plan.unidad_moneda) * plan.puntos_por_unidad_moneda)
        puntos_grupo = math.floor(puntos_base * proporcion)

        if puntos_grupo <= 0:
            return None

        tenant_grupo = f"{GRUPO_TENANT_PREFIX}{grupo.id}"
        cuenta = self._obtener_o_crear_cuenta_grupo(tenant_grupo, cliente_id)

        nuevo_saldo = cuenta.puntos_actuales + puntos_grupo
        self._cuenta_repo.actualizar(
            cuenta.id,
            puntos_actuales=nuevo_saldo,
            puntos_acumulados_total=cuenta.puntos_acumulados_total + puntos_grupo,
        )

        movimiento = MovimientoPuntos(
            cuenta_id=cuenta.id,
            tenant_id=tenant_grupo,
            tipo=TipoMovimientoPuntos.ACUMULACION,
            puntos=puntos_grupo,
            saldo_resultante=nuevo_saldo,
            referencia_transaccion=referencia,
            descripcion=(
                f"Compra ${monto_compra:.2f} en tienda '{tenant_id_origen}' "
                f"(proporción {proporcion}) → {puntos_grupo} pts grupo"
            ),
        )
        return self._movimiento_repo.guardar(movimiento)

    # ------------------------------------------------------------------
    # Canje grupal
    # ------------------------------------------------------------------

    def canjear(
        self,
        grupo_id: str,
        tenant_id_canje: str,
        cliente_id: str,
        puntos_a_canjear: int,
        referencia: Optional[str] = None,
    ) -> ResultadoCanje:
        """
        Canjea puntos grupales en cualquier tienda del grupo.
        Valida que la tienda de canje pertenezca al grupo.
        """
        grupo = self._grupo_svc._repo.obtener(grupo_id)
        if not grupo or tenant_id_canje not in grupo.tenant_ids:
            raise ValueError(
                f"La tienda '{tenant_id_canje}' no pertenece al grupo '{grupo_id}'."
            )

        plan = self._plan_svc.obtener_plan(tenant_id_canje)
        tenant_grupo = f"{GRUPO_TENANT_PREFIX}{grupo_id}"
        cuenta = self._cuenta_repo.obtener_por_cliente_y_tenant(cliente_id, tenant_grupo)

        if not cuenta:
            raise CuentaNoEncontrada("El cliente no tiene cuenta en este grupo.")
        if puntos_a_canjear < plan.puntos_para_canje:
            raise CanjeMinimNoAlcanzado(
                f"Mínimo de canje: {plan.puntos_para_canje} puntos."
            )
        if puntos_a_canjear > cuenta.puntos_actuales:
            raise PuntosInsuficientes(
                f"Saldo insuficiente. Disponible: {cuenta.puntos_actuales}."
            )

        valor_descuento = puntos_a_canjear * plan.valor_punto_en_moneda
        nuevo_saldo = cuenta.puntos_actuales - puntos_a_canjear

        self._cuenta_repo.actualizar(
            cuenta.id,
            puntos_actuales=nuevo_saldo,
            puntos_canjeados_total=cuenta.puntos_canjeados_total + puntos_a_canjear,
        )

        movimiento = MovimientoPuntos(
            cuenta_id=cuenta.id,
            tenant_id=tenant_grupo,
            tipo=TipoMovimientoPuntos.CANJE,
            puntos=-puntos_a_canjear,
            saldo_resultante=nuevo_saldo,
            referencia_transaccion=referencia,
            descripcion=(
                f"Canje grupal en tienda '{tenant_id_canje}': "
                f"{puntos_a_canjear} pts → ${valor_descuento:.2f}"
            ),
        )
        self._movimiento_repo.guardar(movimiento)

        return ResultadoCanje(
            puntos_canjeados=puntos_a_canjear,
            valor_descuento=valor_descuento,
            saldo_restante=nuevo_saldo,
        )

    def saldo_grupo(self, grupo_id: str, cliente_id: str) -> int:
        tenant_grupo = f"{GRUPO_TENANT_PREFIX}{grupo_id}"
        cuenta = self._cuenta_repo.obtener_por_cliente_y_tenant(cliente_id, tenant_grupo)
        return cuenta.puntos_actuales if cuenta else 0

    # ------------------------------------------------------------------
    # Privados
    # ------------------------------------------------------------------

    def _obtener_o_crear_cuenta_grupo(
        self, tenant_grupo: str, cliente_id: str
    ) -> CuentaFidelizacion:
        cuenta = self._cuenta_repo.obtener_por_cliente_y_tenant(cliente_id, tenant_grupo)
        if not cuenta:
            cuenta = CuentaFidelizacion(tenant_id=tenant_grupo, cliente_id=cliente_id)
            self._cuenta_repo.guardar(cuenta)
        return cuenta
