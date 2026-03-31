"""
reportes/metricas_cupones.py
-----------------------------
Métricas y estadísticas de cupones para el dueño de una tienda.
Toda consulta está restringida al tenant indicado.
"""

from datetime import datetime
from typing import List, Optional, Dict

from cupones_fidelizacion.cupones.generador import CuponRepositorio
from cupones_fidelizacion.cupones.validador import RegistroUsoRepositorio
from cupones_fidelizacion.modelos_base import EstadoCupon, TipoDescuento


class MetricasCuponesService:

    def __init__(
        self,
        cupon_repo: Optional[CuponRepositorio] = None,
        uso_repo: Optional[RegistroUsoRepositorio] = None,
    ):
        self._cupon_repo = cupon_repo or CuponRepositorio()
        self._uso_repo = uso_repo or RegistroUsoRepositorio()

    # ------------------------------------------------------------------
    # Resumen general
    # ------------------------------------------------------------------

    def resumen(self, tenant_id: str) -> Dict:
        """Resumen completo del estado de cupones de la tienda."""
        cupones = self._cupon_repo.listar_por_tenant(tenant_id)
        usos = self._uso_repo.filtrar(tenant_id=tenant_id)

        total_descuento = sum(u.descuento_aplicado for u in usos)
        total_ventas_con_cupon = sum(u.monto_original for u in usos)

        por_estado = {estado.value: 0 for estado in EstadoCupon}
        for c in cupones:
            por_estado[c.estado.value] += 1

        return {
            "tenant_id": tenant_id,
            "total_cupones": len(cupones),
            "por_estado": por_estado,
            "total_usos": len(usos),
            "total_descuento_otorgado": round(total_descuento, 2),
            "total_ventas_con_cupon": round(total_ventas_con_cupon, 2),
            "tasa_descuento_promedio": round(
                (total_descuento / total_ventas_con_cupon * 100)
                if total_ventas_con_cupon > 0 else 0,
                2,
            ),
        }

    # ------------------------------------------------------------------
    # Ranking de cupones
    # ------------------------------------------------------------------

    def cupones_mas_usados(self, tenant_id: str, top: int = 10) -> List[Dict]:
        """Top N cupones por número de usos."""
        cupones = self._cupon_repo.listar_por_tenant(tenant_id)
        resultado = []
        for cupon in cupones:
            usos = self._uso_repo.filtrar(cupon_id=cupon.id)
            descuento_total = sum(u.descuento_aplicado for u in usos)
            resultado.append({
                "cupon_id": cupon.id,
                "codigo": cupon.codigo,
                "tipo": cupon.tipo_descuento.value,
                "valor": cupon.valor,
                "estado": cupon.estado.value,
                "usos": len(usos),
                "descuento_total_otorgado": round(descuento_total, 2),
            })
        resultado.sort(key=lambda x: x["usos"], reverse=True)
        return resultado[:top]

    def cupones_sin_uso(self, tenant_id: str) -> List[Dict]:
        """Cupones activos que no han sido usados ninguna vez."""
        cupones = self._cupon_repo.listar_activos_por_tenant(tenant_id)
        sin_uso = []
        for cupon in cupones:
            usos = self._uso_repo.filtrar(cupon_id=cupon.id)
            if not usos:
                sin_uso.append({
                    "cupon_id": cupon.id,
                    "codigo": cupon.codigo,
                    "tipo": cupon.tipo_descuento.value,
                    "valor": cupon.valor,
                    "fecha_fin": cupon.fecha_fin.isoformat(),
                })
        return sin_uso

    # ------------------------------------------------------------------
    # Análisis temporal
    # ------------------------------------------------------------------

    def usos_por_periodo(
        self,
        tenant_id: str,
        desde: datetime,
        hasta: datetime,
    ) -> Dict:
        """Usos y descuentos acumulados en un rango de fechas."""
        usos = [
            u for u in self._uso_repo.filtrar(tenant_id=tenant_id)
            if desde <= u.creado_en <= hasta
        ]
        return {
            "desde": desde.isoformat(),
            "hasta": hasta.isoformat(),
            "total_usos": len(usos),
            "total_descuento": round(sum(u.descuento_aplicado for u in usos), 2),
            "clientes_unicos": len({u.cliente_id for u in usos}),
        }

    def tasa_conversion(self, tenant_id: str) -> Dict:
        """
        Calcula qué porcentaje de cupones activos han sido usados al menos una vez.
        """
        cupones = self._cupon_repo.listar_por_tenant(tenant_id)
        if not cupones:
            return {"tasa_conversion": 0, "total": 0, "con_usos": 0}

        con_usos = sum(1 for c in cupones if c.usos_actuales > 0)
        return {
            "total_cupones": len(cupones),
            "con_al_menos_un_uso": con_usos,
            "tasa_conversion_pct": round((con_usos / len(cupones)) * 100, 2),
        }

    # ------------------------------------------------------------------
    # Análisis por tipo
    # ------------------------------------------------------------------

    def descuento_por_tipo(self, tenant_id: str) -> Dict:
        """Agrupa el descuento total otorgado por tipo de cupón."""
        usos = self._uso_repo.filtrar(tenant_id=tenant_id)
        cupones_map = {
            c.id: c for c in self._cupon_repo.listar_por_tenant(tenant_id)
        }
        por_tipo: Dict[str, float] = {t.value: 0.0 for t in TipoDescuento}
        for uso in usos:
            cupon = cupones_map.get(uso.cupon_id)
            if cupon:
                por_tipo[cupon.tipo_descuento.value] += uso.descuento_aplicado
        return {k: round(v, 2) for k, v in por_tipo.items()}
