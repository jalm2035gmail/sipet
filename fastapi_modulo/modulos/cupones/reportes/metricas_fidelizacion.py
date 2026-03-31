"""
reportes/metricas_fidelizacion.py
-----------------------------------
Métricas del programa de fidelización por tenant.
"""

from typing import Dict, List, Optional
from datetime import datetime

from cupones_fidelizacion.fidelizacion.acumulador import (
    CuentaRepositorio, MovimientoRepositorio
)
from cupones_fidelizacion.modelos_base import NivelFidelizacion, TipoMovimientoPuntos
from cupones_fidelizacion.fidelizacion.configurador import PlanFidelizacionService


class MetricasFidelizacionService:

    def __init__(
        self,
        plan_service: PlanFidelizacionService,
        cuenta_repo: Optional[CuentaRepositorio] = None,
        movimiento_repo: Optional[MovimientoRepositorio] = None,
    ):
        self._plan = plan_service
        self._cuenta_repo = cuenta_repo or CuentaRepositorio()
        self._movimiento_repo = movimiento_repo or MovimientoRepositorio()

    # ------------------------------------------------------------------
    # Resumen general del programa
    # ------------------------------------------------------------------

    def resumen(self, tenant_id: str) -> Dict:
        cuentas = self._cuenta_repo.filtrar(tenant_id=tenant_id)
        movimientos = self._movimiento_repo.filtrar(tenant_id=tenant_id)

        puntos_emitidos = sum(
            m.puntos for m in movimientos
            if m.tipo == TipoMovimientoPuntos.ACUMULACION
        )
        puntos_canjeados = abs(sum(
            m.puntos for m in movimientos
            if m.tipo == TipoMovimientoPuntos.CANJE
        ))
        puntos_expirados = abs(sum(
            m.puntos for m in movimientos
            if m.tipo == TipoMovimientoPuntos.EXPIRACION
        ))
        puntos_vigentes = sum(c.puntos_actuales for c in cuentas)

        plan = None
        try:
            plan = self._plan.obtener_plan(tenant_id)
        except Exception:
            pass

        valor_puntos_vigentes = (
            puntos_vigentes * plan.valor_punto_en_moneda if plan else 0
        )

        return {
            "tenant_id": tenant_id,
            "total_miembros": len(cuentas),
            "puntos_emitidos_total": puntos_emitidos,
            "puntos_canjeados_total": puntos_canjeados,
            "puntos_expirados_total": puntos_expirados,
            "puntos_vigentes": puntos_vigentes,
            "valor_puntos_vigentes_moneda": round(valor_puntos_vigentes, 2),
            "tasa_canje_pct": round(
                (puntos_canjeados / puntos_emitidos * 100) if puntos_emitidos > 0 else 0,
                2,
            ),
        }

    # ------------------------------------------------------------------
    # Distribución por nivel
    # ------------------------------------------------------------------

    def distribucion_niveles(self, tenant_id: str) -> Dict:
        """Cuántos clientes hay en cada nivel."""
        cuentas = self._cuenta_repo.filtrar(tenant_id=tenant_id)
        dist = {nivel.value: 0 for nivel in NivelFidelizacion}
        for cuenta in cuentas:
            dist[cuenta.nivel.value] += 1
        total = len(cuentas)
        return {
            "total": total,
            "distribucion": {
                nivel: {
                    "cantidad": cantidad,
                    "porcentaje": round((cantidad / total * 100) if total > 0 else 0, 2),
                }
                for nivel, cantidad in dist.items()
            },
        }

    # ------------------------------------------------------------------
    # Ranking de clientes
    # ------------------------------------------------------------------

    def top_clientes(self, tenant_id: str, top: int = 10) -> List[Dict]:
        """Top clientes por puntos acumulados históricamente."""
        cuentas = self._cuenta_repo.filtrar(tenant_id=tenant_id)
        cuentas.sort(key=lambda c: c.puntos_acumulados_total, reverse=True)
        return [
            {
                "cliente_id": c.cliente_id,
                "nivel": c.nivel.value,
                "puntos_actuales": c.puntos_actuales,
                "puntos_acumulados_total": c.puntos_acumulados_total,
                "puntos_canjeados_total": c.puntos_canjeados_total,
                "miembro_desde": c.creado_en.isoformat(),
            }
            for c in cuentas[:top]
        ]

    def clientes_inactivos(
        self, tenant_id: str, dias_sin_actividad: int = 90
    ) -> List[Dict]:
        """Clientes sin movimientos en los últimos N días."""
        from datetime import timedelta
        limite = datetime.utcnow() - timedelta(days=dias_sin_actividad)
        cuentas = self._cuenta_repo.filtrar(tenant_id=tenant_id)
        inactivos = [
            {
                "cliente_id": c.cliente_id,
                "puntos_actuales": c.puntos_actuales,
                "ultima_actividad": c.ultima_actividad.isoformat(),
                "nivel": c.nivel.value,
            }
            for c in cuentas
            if c.ultima_actividad < limite
        ]
        return sorted(inactivos, key=lambda x: x["ultima_actividad"])

    # ------------------------------------------------------------------
    # Análisis temporal
    # ------------------------------------------------------------------

    def movimientos_por_periodo(
        self,
        tenant_id: str,
        desde: datetime,
        hasta: datetime,
    ) -> Dict:
        movimientos = [
            m for m in self._movimiento_repo.filtrar(tenant_id=tenant_id)
            if desde <= m.creado_en <= hasta
        ]
        acumulaciones = [m for m in movimientos if m.tipo == TipoMovimientoPuntos.ACUMULACION]
        canjes = [m for m in movimientos if m.tipo == TipoMovimientoPuntos.CANJE]
        return {
            "desde": desde.isoformat(),
            "hasta": hasta.isoformat(),
            "total_movimientos": len(movimientos),
            "puntos_acumulados": sum(m.puntos for m in acumulaciones),
            "puntos_canjeados": abs(sum(m.puntos for m in canjes)),
            "clientes_activos": len({m.cuenta_id for m in movimientos}),
        }
