"""
clientes/historial.py
---------------------
Retorna el historial de movimientos de puntos de un cliente en una tienda,
con soporte de filtros y paginación básica.
"""

from datetime import datetime
from typing import List, Optional

from cupones_fidelizacion.modelos_base import MovimientoPuntos, TipoMovimientoPuntos
from cupones_fidelizacion.fidelizacion.acumulador import (
    CuentaRepositorio, MovimientoRepositorio
)
from cupones_fidelizacion.excepciones import CuentaNoEncontrada


class HistorialClienteService:

    def __init__(
        self,
        cuenta_repo: Optional[CuentaRepositorio] = None,
        movimiento_repo: Optional[MovimientoRepositorio] = None,
    ):
        self._cuenta_repo = cuenta_repo or CuentaRepositorio()
        self._movimiento_repo = movimiento_repo or MovimientoRepositorio()

    def obtener_historial(
        self,
        tenant_id: str,
        cliente_id: str,
        tipo: Optional[TipoMovimientoPuntos] = None,
        desde: Optional[datetime] = None,
        hasta: Optional[datetime] = None,
        pagina: int = 1,
        por_pagina: int = 20,
    ) -> dict:
        """
        Retorna el historial paginado de movimientos del cliente en el tenant.
        """
        cuenta = self._cuenta_repo.obtener_por_cliente_y_tenant(cliente_id, tenant_id)
        if not cuenta:
            raise CuentaNoEncontrada(
                f"El cliente '{cliente_id}' no tiene cuenta en esta tienda."
            )

        movimientos = self._movimiento_repo.listar_por_cuenta(cuenta.id)

        # Filtros
        if tipo:
            movimientos = [m for m in movimientos if m.tipo == tipo]
        if desde:
            movimientos = [m for m in movimientos if m.creado_en >= desde]
        if hasta:
            movimientos = [m for m in movimientos if m.creado_en <= hasta]

        # Ordenar por fecha desc
        movimientos.sort(key=lambda m: m.creado_en, reverse=True)

        total = len(movimientos)
        inicio = (pagina - 1) * por_pagina
        fin = inicio + por_pagina
        pagina_actual = movimientos[inicio:fin]

        return {
            "total": total,
            "pagina": pagina,
            "por_pagina": por_pagina,
            "total_paginas": max(1, -(-total // por_pagina)),
            "movimientos": [self._movimiento_a_dict(m) for m in pagina_actual],
        }

    @staticmethod
    def _movimiento_a_dict(m: MovimientoPuntos) -> dict:
        return {
            "id": m.id,
            "tipo": m.tipo.value,
            "puntos": m.puntos,
            "saldo_resultante": m.saldo_resultante,
            "descripcion": m.descripcion,
            "referencia": m.referencia_transaccion,
            "fecha": m.creado_en.isoformat(),
        }
