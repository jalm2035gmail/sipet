"""
cupones/generador.py
--------------------
Genera cupones de descuento para un tenant específico.
Cada cupón queda vinculado al tenant y es inválido en cualquier otra tienda.
"""

import random
import string
from datetime import datetime
from typing import List, Optional

from cupones_fidelizacion.modelos_base import Cupon, TipoDescuento, EstadoCupon
from cupones_fidelizacion.repositorio import RepositorioBase
from cupones_fidelizacion.excepciones import CodigoCuponDuplicado
from cupones_fidelizacion.multitienda.contexto import verificar_pertenencia


class CuponRepositorio(RepositorioBase[Cupon]):

    def obtener_por_codigo(self, tenant_id: str, codigo: str) -> Optional[Cupon]:
        resultados = self.filtrar(tenant_id=tenant_id, codigo=codigo.upper())
        return resultados[0] if resultados else None

    def listar_por_tenant(self, tenant_id: str) -> List[Cupon]:
        return self.filtrar(tenant_id=tenant_id)

    def listar_activos_por_tenant(self, tenant_id: str) -> List[Cupon]:
        return [
            c for c in self.filtrar(tenant_id=tenant_id)
            if c.estado == EstadoCupon.ACTIVO
        ]


class CuponGenerador:
    """
    Crea y administra cupones de descuento para una tienda específica.
    """

    LONGITUD_CODIGO_DEFAULT = 8

    def __init__(self, repositorio: Optional[CuponRepositorio] = None):
        self._repo = repositorio or CuponRepositorio()

    # ------------------------------------------------------------------
    # Generación de código
    # ------------------------------------------------------------------

    def generar_codigo_aleatorio(self, longitud: int = LONGITUD_CODIGO_DEFAULT) -> str:
        """Genera un código alfanumérico en mayúsculas."""
        chars = string.ascii_uppercase + string.digits
        return "".join(random.choices(chars, k=longitud))

    def _codigo_disponible(self, tenant_id: str, codigo: str) -> bool:
        return self._repo.obtener_por_codigo(tenant_id, codigo) is None

    # ------------------------------------------------------------------
    # Creación de cupones
    # ------------------------------------------------------------------

    def crear_cupon(
        self,
        tenant_id: str,
        tipo_descuento: TipoDescuento,
        valor: float,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        codigo: Optional[str] = None,
        usos_maximos: Optional[int] = None,
        monto_minimo_compra: float = 0.0,
        categorias_aplicables: Optional[List[str]] = None,
        productos_excluidos: Optional[List[str]] = None,
        solo_primera_compra: bool = False,
        descripcion: str = "",
    ) -> Cupon:
        """Crea un cupón nuevo para el tenant indicado."""
        if fecha_fin <= fecha_inicio:
            raise ValueError("La fecha de fin debe ser posterior a la de inicio.")
        if tipo_descuento == TipoDescuento.PORCENTAJE and not (0 < valor <= 100):
            raise ValueError("El porcentaje debe estar entre 0 y 100.")
        if tipo_descuento == TipoDescuento.MONTO_FIJO and valor <= 0:
            raise ValueError("El monto fijo debe ser positivo.")

        if codigo:
            codigo = codigo.upper()
            if not self._codigo_disponible(tenant_id, codigo):
                raise CodigoCuponDuplicado(
                    f"El código '{codigo}' ya existe en esta tienda."
                )
        else:
            # Genera código único automáticamente
            codigo = self.generar_codigo_aleatorio()
            while not self._codigo_disponible(tenant_id, codigo):
                codigo = self.generar_codigo_aleatorio()

        cupon = Cupon(
            tenant_id=tenant_id,
            codigo=codigo,
            tipo_descuento=tipo_descuento,
            valor=valor,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            usos_maximos=usos_maximos,
            monto_minimo_compra=monto_minimo_compra,
            categorias_aplicables=categorias_aplicables or [],
            productos_excluidos=productos_excluidos or [],
            solo_primera_compra=solo_primera_compra,
            descripcion=descripcion,
        )
        return self._repo.guardar(cupon)

    def crear_lote(
        self,
        tenant_id: str,
        cantidad: int,
        tipo_descuento: TipoDescuento,
        valor: float,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        usos_maximos_por_cupon: int = 1,
        **kwargs,
    ) -> List[Cupon]:
        """Genera múltiples cupones de un solo uso (ej. para campañas)."""
        cupones = []
        for _ in range(cantidad):
            c = self.crear_cupon(
                tenant_id=tenant_id,
                tipo_descuento=tipo_descuento,
                valor=valor,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                usos_maximos=usos_maximos_por_cupon,
                **kwargs,
            )
            cupones.append(c)
        return cupones

    # ------------------------------------------------------------------
    # Consulta
    # ------------------------------------------------------------------

    def obtener(self, tenant_id: str, cupon_id: str) -> Cupon:
        from cupones_fidelizacion.excepciones import CuponNoEncontrado
        cupon = self._repo.obtener(cupon_id)
        if not cupon:
            raise CuponNoEncontrado(f"Cupón '{cupon_id}' no encontrado.")
        verificar_pertenencia(tenant_id, cupon.tenant_id)
        return cupon

    def obtener_por_codigo(self, tenant_id: str, codigo: str) -> Cupon:
        from cupones_fidelizacion.excepciones import CuponNoEncontrado
        cupon = self._repo.obtener_por_codigo(tenant_id, codigo.upper())
        if not cupon:
            raise CuponNoEncontrado(
                f"Cupón con código '{codigo}' no encontrado en esta tienda."
            )
        return cupon

    def listar_cupones(self, tenant_id: str, solo_activos: bool = False) -> List[Cupon]:
        if solo_activos:
            return self._repo.listar_activos_por_tenant(tenant_id)
        return self._repo.listar_por_tenant(tenant_id)
