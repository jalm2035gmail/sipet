"""
validacion/reglas_negocio.py
-----------------------------
Reglas de negocio compartidas y configurables por tenant.
Implementa el patrón Strategy para que las reglas sean inyectables y extensibles.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from cupones_fidelizacion.modelos_base import Cupon, TipoDescuento


# ---------------------------------------------------------------------------
# Interfaz base de regla
# ---------------------------------------------------------------------------

class ReglaValidacion(ABC):
    """
    Cada regla de negocio implementa esta interfaz.
    Si la regla no se cumple, lanza la excepción correspondiente.
    """

    @property
    @abstractmethod
    def nombre(self) -> str:
        pass

    @abstractmethod
    def validar(self, contexto: dict) -> None:
        """
        contexto puede contener:
            cupon, monto_compra, cliente_id, productos_ids,
            categorias_ids, ahora, tenant_id, ...
        """
        pass


# ---------------------------------------------------------------------------
# Reglas concretas
# ---------------------------------------------------------------------------

class ReglaMontominimo(ReglaValidacion):
    @property
    def nombre(self):
        return "monto_minimo"

    def validar(self, ctx: dict) -> None:
        cupon: Cupon = ctx["cupon"]
        monto: float = ctx.get("monto_compra", 0)
        if monto < cupon.monto_minimo_compra:
            from cupones_fidelizacion.excepciones import CuponMontoInsuficiente
            raise CuponMontoInsuficiente(
                f"Monto mínimo requerido: ${cupon.monto_minimo_compra:.2f}. "
                f"Monto actual: ${monto:.2f}."
            )


class ReglaVigencia(ReglaValidacion):
    @property
    def nombre(self):
        return "vigencia"

    def validar(self, ctx: dict) -> None:
        cupon: Cupon = ctx["cupon"]
        ahora: datetime = ctx.get("ahora", datetime.utcnow())
        from cupones_fidelizacion.excepciones import CuponExpirado, CuponInvalido
        if ahora < cupon.fecha_inicio:
            raise CuponInvalido("El cupón aún no está vigente.")
        if ahora > cupon.fecha_fin:
            raise CuponExpirado("El cupón ha expirado.")


class ReglaUnica(ReglaValidacion):
    """Impide que el mismo cliente use más de una vez un cupón de uso único."""

    def __init__(self, uso_repo):
        self._uso_repo = uso_repo

    @property
    def nombre(self):
        return "uso_unico"

    def validar(self, ctx: dict) -> None:
        cupon: Cupon = ctx["cupon"]
        cliente_id: str = ctx.get("cliente_id", "")
        if cupon.usos_maximos == 1:
            usos = self._uso_repo.usos_por_cliente_y_cupon(cliente_id, cupon.id)
            if usos:
                from cupones_fidelizacion.excepciones import CuponYaUsadoPorCliente
                raise CuponYaUsadoPorCliente("Ya usaste este cupón anteriormente.")


class ReglaPrimeraCompra(ReglaValidacion):
    def __init__(self, uso_repo):
        self._uso_repo = uso_repo

    @property
    def nombre(self):
        return "primera_compra"

    def validar(self, ctx: dict) -> None:
        cupon: Cupon = ctx["cupon"]
        if not cupon.solo_primera_compra:
            return
        cliente_id: str = ctx.get("cliente_id", "")
        if not self._uso_repo.es_primera_compra(cupon.tenant_id, cliente_id):
            from cupones_fidelizacion.excepciones import CuponYaUsadoPorCliente
            raise CuponYaUsadoPorCliente(
                "Este cupón es válido únicamente para la primera compra."
            )


class ReglaProductosExcluidos(ReglaValidacion):
    @property
    def nombre(self):
        return "productos_excluidos"

    def validar(self, ctx: dict) -> None:
        cupon: Cupon = ctx["cupon"]
        productos_ids: List[str] = ctx.get("productos_ids", [])
        if cupon.productos_excluidos:
            excluidos = set(productos_ids) & set(cupon.productos_excluidos)
            if excluidos:
                from cupones_fidelizacion.excepciones import CuponNoAplicaProducto
                raise CuponNoAplicaProducto(
                    "El carrito contiene productos excluidos de este cupón."
                )


class ReglaCategorias(ReglaValidacion):
    @property
    def nombre(self):
        return "categorias"

    def validar(self, ctx: dict) -> None:
        cupon: Cupon = ctx["cupon"]
        if not cupon.categorias_aplicables:
            return  # Aplica a todas
        categorias_ids: List[str] = ctx.get("categorias_ids", [])
        match = set(categorias_ids) & set(cupon.categorias_aplicables)
        if not match:
            from cupones_fidelizacion.excepciones import CuponNoAplicaProducto
            raise CuponNoAplicaProducto(
                "Este cupón no aplica a las categorías de tu carrito."
            )


# ---------------------------------------------------------------------------
# Motor de reglas
# ---------------------------------------------------------------------------

class MotorReglas:
    """
    Ejecuta una lista ordenada de reglas sobre un contexto.
    Las reglas pueden ser configuradas por tenant o globalmente.
    """

    def __init__(self, reglas: Optional[List[ReglaValidacion]] = None):
        self._reglas: List[ReglaValidacion] = reglas or []

    def agregar_regla(self, regla: ReglaValidacion) -> None:
        self._reglas.append(regla)

    def remover_regla(self, nombre: str) -> None:
        self._reglas = [r for r in self._reglas if r.nombre != nombre]

    def ejecutar(self, contexto: dict) -> None:
        """Ejecuta todas las reglas en orden. Falla en la primera que no pase."""
        for regla in self._reglas:
            regla.validar(contexto)

    @classmethod
    def default(cls, uso_repo) -> "MotorReglas":
        """Crea el motor con el conjunto estándar de reglas."""
        return cls(reglas=[
            ReglaVigencia(),
            ReglaMontominimo(),
            ReglaUnica(uso_repo),
            ReglaPrimeraCompra(uso_repo),
            ReglaProductosExcluidos(),
            ReglaCategorias(),
        ])
