"""
cupones/validador.py
--------------------
Valida si un cupón puede ser aplicado a un carrito de compra.
Todas las reglas de negocio de validación están centralizadas aquí.
"""

from datetime import datetime
from typing import List, Optional

from cupones_fidelizacion.modelos_base import Cupon, EstadoCupon, RegistroUsoCupon
from cupones_fidelizacion.repositorio import RepositorioBase
from cupones_fidelizacion.excepciones import (
    CuponExpirado, CuponAgotado, CuponRevocado,
    CuponMontoInsuficiente, CuponNoAplicaProducto, CuponYaUsadoPorCliente,
    CuponInvalido,
)


class RegistroUsoRepositorio(RepositorioBase[RegistroUsoCupon]):

    def usos_por_cupon(self, cupon_id: str) -> List[RegistroUsoCupon]:
        return self.filtrar(cupon_id=cupon_id)

    def usos_por_cliente_y_cupon(self, cliente_id: str, cupon_id: str) -> List[RegistroUsoCupon]:
        return self.filtrar(cliente_id=cliente_id, cupon_id=cupon_id)

    def es_primera_compra(self, tenant_id: str, cliente_id: str) -> bool:
        todos = self.filtrar(tenant_id=tenant_id, cliente_id=cliente_id)
        return len(todos) == 0


class CuponValidador:
    """
    Aplica todas las reglas de validación sobre un cupón antes de usarlo.
    """

    def __init__(self, uso_repo: Optional[RegistroUsoRepositorio] = None):
        self._uso_repo = uso_repo or RegistroUsoRepositorio()

    def validar(
        self,
        cupon: Cupon,
        monto_compra: float,
        cliente_id: str,
        productos_ids: Optional[List[str]] = None,
        categorias_ids: Optional[List[str]] = None,
        ahora: Optional[datetime] = None,
    ) -> None:
        """
        Ejecuta todas las validaciones en orden.
        Lanza la excepción correspondiente al primer fallo.
        """
        ahora = ahora or datetime.utcnow()
        productos_ids = productos_ids or []
        categorias_ids = categorias_ids or []

        self._validar_estado(cupon)
        self._validar_vigencia(cupon, ahora)
        self._validar_usos(cupon)
        self._validar_monto_minimo(cupon, monto_compra)
        self._validar_primera_compra(cupon, cliente_id)
        self._validar_uso_por_cliente(cupon, cliente_id)
        self._validar_productos(cupon, productos_ids, categorias_ids)

    # ------------------------------------------------------------------
    # Reglas individuales
    # ------------------------------------------------------------------

    def _validar_estado(self, cupon: Cupon) -> None:
        if cupon.estado == EstadoCupon.REVOCADO:
            raise CuponRevocado("Este cupón ha sido revocado y no puede usarse.")
        if cupon.estado == EstadoCupon.AGOTADO:
            raise CuponAgotado("Este cupón ya no tiene usos disponibles.")
        if cupon.estado == EstadoCupon.PAUSADO:
            raise CuponInvalido("Este cupón está temporalmente desactivado.")
        if cupon.estado == EstadoCupon.EXPIRADO:
            raise CuponExpirado("Este cupón ha expirado.")

    def _validar_vigencia(self, cupon: Cupon, ahora: datetime) -> None:
        if ahora < cupon.fecha_inicio:
            raise CuponInvalido(
                f"Este cupón aún no está vigente. Válido desde {cupon.fecha_inicio.date()}."
            )
        if ahora > cupon.fecha_fin:
            raise CuponExpirado(
                f"Este cupón expiró el {cupon.fecha_fin.date()}."
            )

    def _validar_usos(self, cupon: Cupon) -> None:
        if cupon.usos_maximos is not None:
            if cupon.usos_actuales >= cupon.usos_maximos:
                raise CuponAgotado("Este cupón ha alcanzado su límite de usos.")

    def _validar_monto_minimo(self, cupon: Cupon, monto: float) -> None:
        if monto < cupon.monto_minimo_compra:
            raise CuponMontoInsuficiente(
                f"El monto mínimo de compra es ${cupon.monto_minimo_compra:.2f}. "
                f"Tu carrito tiene ${monto:.2f}."
            )

    def _validar_primera_compra(self, cupon: Cupon, cliente_id: str) -> None:
        if cupon.solo_primera_compra:
            if not self._uso_repo.es_primera_compra(cupon.tenant_id, cliente_id):
                raise CuponYaUsadoPorCliente(
                    "Este cupón es válido únicamente para la primera compra."
                )

    def _validar_uso_por_cliente(self, cupon: Cupon, cliente_id: str) -> None:
        usos = self._uso_repo.usos_por_cliente_y_cupon(cliente_id, cupon.id)
        if len(usos) > 0 and cupon.usos_maximos == 1:
            raise CuponYaUsadoPorCliente("Ya has utilizado este cupón anteriormente.")

    def _validar_productos(
        self,
        cupon: Cupon,
        productos_ids: List[str],
        categorias_ids: List[str],
    ) -> None:
        # Verificar productos excluidos
        if cupon.productos_excluidos:
            excluidos_en_carrito = set(productos_ids) & set(cupon.productos_excluidos)
            if excluidos_en_carrito:
                raise CuponNoAplicaProducto(
                    "Tu carrito contiene productos excluidos de este cupón."
                )

        # Si el cupón aplica solo a categorías específicas, al menos una debe estar presente
        if cupon.categorias_aplicables:
            categorias_match = set(categorias_ids) & set(cupon.categorias_aplicables)
            if not categorias_match:
                raise CuponNoAplicaProducto(
                    "Este cupón no aplica a los productos de tu carrito."
                )
