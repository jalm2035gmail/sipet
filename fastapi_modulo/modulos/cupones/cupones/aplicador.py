"""
cupones/aplicador.py
--------------------
Calcula el descuento real y registra el uso del cupón.
Opera siempre después de que el Validador haya dado el OK.
"""

from datetime import datetime
from typing import Dict, Optional, List

from cupones_fidelizacion.modelos_base import (
    Cupon, TipoDescuento, EstadoCupon, RegistroUsoCupon
)
from cupones_fidelizacion.cupones.validador import CuponValidador, RegistroUsoRepositorio
from cupones_fidelizacion.cupones.generador import CuponRepositorio


class ResultadoAplicacion:
    """Resultado de aplicar un cupón a un carrito."""

    def __init__(
        self,
        cupon_id: str,
        codigo: str,
        tipo_descuento: TipoDescuento,
        monto_original: float,
        descuento_calculado: float,
        monto_final: float,
        envio_gratis: bool = False,
    ):
        self.cupon_id = cupon_id
        self.codigo = codigo
        self.tipo_descuento = tipo_descuento
        self.monto_original = monto_original
        self.descuento_calculado = descuento_calculado
        self.monto_final = monto_final
        self.envio_gratis = envio_gratis

    def to_dict(self) -> Dict:
        return {
            "cupon_id": self.cupon_id,
            "codigo": self.codigo,
            "tipo_descuento": self.tipo_descuento.value,
            "monto_original": round(self.monto_original, 2),
            "descuento_calculado": round(self.descuento_calculado, 2),
            "monto_final": round(self.monto_final, 2),
            "envio_gratis": self.envio_gratis,
        }


class CuponAplicador:
    """
    Orquesta la validación, cálculo y registro de uso de un cupón.
    """

    def __init__(
        self,
        cupon_repo: Optional[CuponRepositorio] = None,
        uso_repo: Optional[RegistroUsoRepositorio] = None,
    ):
        self._cupon_repo = cupon_repo or CuponRepositorio()
        self._uso_repo = uso_repo or RegistroUsoRepositorio()
        self._validador = CuponValidador(self._uso_repo)

    # ------------------------------------------------------------------
    # Aplicación
    # ------------------------------------------------------------------

    def aplicar(
        self,
        tenant_id: str,
        codigo: str,
        cliente_id: str,
        monto_compra: float,
        transaccion_id: str,
        productos_ids: Optional[List[str]] = None,
        categorias_ids: Optional[List[str]] = None,
    ) -> ResultadoAplicacion:
        """
        Valida y aplica el cupón.
        Registra el uso y actualiza contadores.
        Retorna el resultado con el descuento calculado.
        """
        cupon = self._cupon_repo.obtener_por_codigo(tenant_id, codigo.upper())
        if not cupon:
            from cupones_fidelizacion.excepciones import CuponNoEncontrado
            raise CuponNoEncontrado(f"Cupón '{codigo}' no encontrado en esta tienda.")

        # Validación completa
        self._validador.validar(
            cupon=cupon,
            monto_compra=monto_compra,
            cliente_id=cliente_id,
            productos_ids=productos_ids,
            categorias_ids=categorias_ids,
        )

        # Cálculo del descuento
        resultado = self._calcular_descuento(cupon, monto_compra)

        # Registro de uso
        self._registrar_uso(cupon, cliente_id, transaccion_id, resultado)

        # Actualizar contadores del cupón
        self._incrementar_uso(cupon)

        return resultado

    def preview(
        self,
        tenant_id: str,
        codigo: str,
        monto_compra: float,
    ) -> ResultadoAplicacion:
        """
        Calcula el descuento sin aplicarlo ni registrar uso.
        Útil para mostrar al cliente el ahorro antes de confirmar.
        """
        cupon = self._cupon_repo.obtener_por_codigo(tenant_id, codigo.upper())
        if not cupon:
            from cupones_fidelizacion.excepciones import CuponNoEncontrado
            raise CuponNoEncontrado(f"Cupón '{codigo}' no encontrado.")
        return self._calcular_descuento(cupon, monto_compra)

    # ------------------------------------------------------------------
    # Privados
    # ------------------------------------------------------------------

    def _calcular_descuento(self, cupon: Cupon, monto: float) -> ResultadoAplicacion:
        descuento = 0.0
        envio_gratis = False

        if cupon.tipo_descuento == TipoDescuento.PORCENTAJE:
            descuento = monto * (cupon.valor / 100)
        elif cupon.tipo_descuento == TipoDescuento.MONTO_FIJO:
            descuento = min(cupon.valor, monto)  # No puede ser mayor al total
        elif cupon.tipo_descuento == TipoDescuento.ENVIO_GRATIS:
            envio_gratis = True

        monto_final = max(0.0, monto - descuento)

        return ResultadoAplicacion(
            cupon_id=cupon.id,
            codigo=cupon.codigo,
            tipo_descuento=cupon.tipo_descuento,
            monto_original=monto,
            descuento_calculado=descuento,
            monto_final=monto_final,
            envio_gratis=envio_gratis,
        )

    def _registrar_uso(
        self,
        cupon: Cupon,
        cliente_id: str,
        transaccion_id: str,
        resultado: ResultadoAplicacion,
    ) -> None:
        registro = RegistroUsoCupon(
            cupon_id=cupon.id,
            tenant_id=cupon.tenant_id,
            cliente_id=cliente_id,
            transaccion_id=transaccion_id,
            descuento_aplicado=resultado.descuento_calculado,
            monto_original=resultado.monto_original,
        )
        self._uso_repo.guardar(registro)

    def _incrementar_uso(self, cupon: Cupon) -> None:
        nuevos_usos = cupon.usos_actuales + 1
        actualizado = self._cupon_repo.actualizar(
            cupon.id, usos_actuales=nuevos_usos
        )
        # Si alcanzó el límite, marcarlo como agotado
        if actualizado.usos_maximos and nuevos_usos >= actualizado.usos_maximos:
            self._cupon_repo.actualizar(cupon.id, estado=EstadoCupon.AGOTADO)
