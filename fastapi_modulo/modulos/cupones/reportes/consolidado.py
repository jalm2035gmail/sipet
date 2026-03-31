"""
reportes/consolidado.py
------------------------
Vista agregada de toda la plataforma para el administrador.
NUNCA exponer estos datos a los dueños de tiendas individuales.
"""

from typing import List, Dict, Optional

from cupones_fidelizacion.multitienda.tenant import TenantService
from cupones_fidelizacion.reportes.metricas_cupones import MetricasCuponesService
from cupones_fidelizacion.reportes.metricas_fidelizacion import MetricasFidelizacionService
from cupones_fidelizacion.modelos_base import EstadoGeneral


class ReporteConsolidado:
    """
    Agrega métricas de todos los tenants para el operador de la plataforma.
    """

    def __init__(
        self,
        tenant_service: TenantService,
        metricas_cupones: MetricasCuponesService,
        metricas_fidelizacion: MetricasFidelizacionService,
    ):
        self._tenant_svc = tenant_service
        self._cupones_svc = metricas_cupones
        self._fidelizacion_svc = metricas_fidelizacion

    def resumen_plataforma(self) -> Dict:
        """Agrega métricas de todas las tiendas activas."""
        tiendas = self._tenant_svc.listar_activas()
        total_miembros = 0
        total_usos_cupones = 0
        total_descuento = 0.0
        total_puntos_emitidos = 0
        total_puntos_canjeados = 0
        resumen_tiendas = []

        for tienda in tiendas:
            try:
                mc = self._cupones_svc.resumen(tienda.id)
                mf = self._fidelizacion_svc.resumen(tienda.id)

                total_miembros += mf.get("total_miembros", 0)
                total_usos_cupones += mc.get("total_usos", 0)
                total_descuento += mc.get("total_descuento_otorgado", 0)
                total_puntos_emitidos += mf.get("puntos_emitidos_total", 0)
                total_puntos_canjeados += mf.get("puntos_canjeados_total", 0)

                resumen_tiendas.append({
                    "tenant_id": tienda.id,
                    "nombre": tienda.nombre,
                    "miembros": mf.get("total_miembros", 0),
                    "usos_cupones": mc.get("total_usos", 0),
                    "descuento_otorgado": mc.get("total_descuento_otorgado", 0),
                    "puntos_emitidos": mf.get("puntos_emitidos_total", 0),
                })
            except Exception:
                # Si una tienda no tiene plan configurado, no la saltamos
                resumen_tiendas.append({
                    "tenant_id": tienda.id,
                    "nombre": tienda.nombre,
                    "error": "sin datos suficientes",
                })

        return {
            "total_tiendas_activas": len(tiendas),
            "total_miembros_plataforma": total_miembros,
            "total_usos_cupones": total_usos_cupones,
            "total_descuento_otorgado": round(total_descuento, 2),
            "total_puntos_emitidos": total_puntos_emitidos,
            "total_puntos_canjeados": total_puntos_canjeados,
            "tasa_canje_global_pct": round(
                (total_puntos_canjeados / total_puntos_emitidos * 100)
                if total_puntos_emitidos > 0 else 0,
                2,
            ),
            "por_tienda": resumen_tiendas,
        }

    def tiendas_por_actividad(self, top: int = 10) -> List[Dict]:
        """Ranking de tiendas por usos de cupones."""
        tiendas = self._tenant_svc.listar_activas()
        ranking = []
        for tienda in tiendas:
            try:
                mc = self._cupones_svc.resumen(tienda.id)
                ranking.append({
                    "tenant_id": tienda.id,
                    "nombre": tienda.nombre,
                    "usos_cupones": mc.get("total_usos", 0),
                    "descuento_total": mc.get("total_descuento_otorgado", 0),
                })
            except Exception:
                pass
        ranking.sort(key=lambda x: x["usos_cupones"], reverse=True)
        return ranking[:top]
