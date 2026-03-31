"""
facade.py
---------
Fachadas de alto nivel que conectan todos los servicios del módulo.
Punto de entrada recomendado para integrar el módulo en tu aplicación.

Cada fachada recibe un tenant_id y agrupa las operaciones más comunes
en métodos claros y directos.

Ejemplo de uso:
    from cupones_fidelizacion import CuponFacade, FidelizacionFacade

    # Configurar tienda
    from cupones_fidelizacion.multitienda.tenant import TenantService
    ts = TenantService()
    tienda = ts.registrar_tienda("Mi Tienda")

    # Cupones
    cupones = CuponFacade(tienda.id)
    cupon = cupones.crear_porcentaje("BIENVENIDO", 15, fecha_inicio, fecha_fin)
    resultado = cupones.aplicar("BIENVENIDO", cliente_id="c1", monto=500, transaccion_id="t1")

    # Fidelización
    fidelizacion = FidelizacionFacade(tienda.id)
    fidelizacion.configurar(nombre="Mi Programa", puntos_por_peso=0.1)
    fidelizacion.registrar_compra(cliente_id="c1", monto=500, referencia="t1")
    saldo = fidelizacion.saldo("c1")
"""

from datetime import datetime
from typing import Optional, List

from cupones_fidelizacion.modelos_base import TipoDescuento, Cupon
from cupones_fidelizacion.cupones.generador import CuponGenerador, CuponRepositorio
from cupones_fidelizacion.cupones.aplicador import CuponAplicador, ResultadoAplicacion
from cupones_fidelizacion.cupones.ciclo_de_vida import CuponCicloDeVida
from cupones_fidelizacion.cupones.validador import RegistroUsoRepositorio
from cupones_fidelizacion.fidelizacion.configurador import PlanFidelizacionService
from cupones_fidelizacion.fidelizacion.acumulador import (
    PuntosAcumulador, CuentaRepositorio, MovimientoRepositorio
)
from cupones_fidelizacion.fidelizacion.canjeador import PuntosCanjeador, ResultadoCanje
from cupones_fidelizacion.fidelizacion.nivel_motor import NivelMotor
from cupones_fidelizacion.clientes.cuenta import CuentaClienteService
from cupones_fidelizacion.clientes.historial import HistorialClienteService
from cupones_fidelizacion.reportes.metricas_cupones import MetricasCuponesService
from cupones_fidelizacion.reportes.metricas_fidelizacion import MetricasFidelizacionService


# ---------------------------------------------------------------------------
# Repositorios compartidos (singleton por proceso — reemplazar con DI en prod)
# ---------------------------------------------------------------------------
_cupon_repo = CuponRepositorio()
_uso_repo = RegistroUsoRepositorio()
_cuenta_repo = CuentaRepositorio()
_movimiento_repo = MovimientoRepositorio()
_plan_service = PlanFidelizacionService()


class CuponFacade:
    """
    API de alto nivel para cupones de una tienda específica.
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self._generador = CuponGenerador(_cupon_repo)
        self._aplicador = CuponAplicador(_cupon_repo, _uso_repo)
        self._ciclo = CuponCicloDeVida(_cupon_repo)
        self._metricas = MetricasCuponesService(_cupon_repo, _uso_repo)

    # --- Creación ---

    def crear_porcentaje(
        self,
        codigo: str,
        porcentaje: float,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        **kwargs,
    ) -> Cupon:
        return self._generador.crear_cupon(
            self.tenant_id,
            TipoDescuento.PORCENTAJE,
            porcentaje,
            fecha_inicio,
            fecha_fin,
            codigo=codigo,
            **kwargs,
        )

    def crear_monto_fijo(
        self,
        codigo: str,
        monto: float,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        **kwargs,
    ) -> Cupon:
        return self._generador.crear_cupon(
            self.tenant_id,
            TipoDescuento.MONTO_FIJO,
            monto,
            fecha_inicio,
            fecha_fin,
            codigo=codigo,
            **kwargs,
        )

    def crear_envio_gratis(
        self,
        codigo: str,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        **kwargs,
    ) -> Cupon:
        return self._generador.crear_cupon(
            self.tenant_id,
            TipoDescuento.ENVIO_GRATIS,
            0,
            fecha_inicio,
            fecha_fin,
            codigo=codigo,
            **kwargs,
        )

    def crear_lote(
        self,
        cantidad: int,
        tipo: TipoDescuento,
        valor: float,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        **kwargs,
    ) -> List[Cupon]:
        return self._generador.crear_lote(
            self.tenant_id, cantidad, tipo, valor, fecha_inicio, fecha_fin, **kwargs
        )

    # --- Aplicación ---

    def aplicar(
        self,
        codigo: str,
        cliente_id: str,
        monto: float,
        transaccion_id: str,
        productos_ids: Optional[List[str]] = None,
        categorias_ids: Optional[List[str]] = None,
    ) -> ResultadoAplicacion:
        return self._aplicador.aplicar(
            self.tenant_id, codigo, cliente_id, monto, transaccion_id,
            productos_ids, categorias_ids,
        )

    def preview(self, codigo: str, monto: float) -> ResultadoAplicacion:
        return self._aplicador.preview(self.tenant_id, codigo, monto)

    # --- Ciclo de vida ---

    def pausar(self, cupon_id: str) -> Cupon:
        return self._ciclo.pausar(self.tenant_id, cupon_id)

    def reactivar(self, cupon_id: str) -> Cupon:
        return self._ciclo.reactivar(self.tenant_id, cupon_id)

    def revocar(self, cupon_id: str) -> Cupon:
        return self._ciclo.revocar(self.tenant_id, cupon_id)

    def sincronizar_expiraciones(self) -> List[Cupon]:
        return self._ciclo.sincronizar_expiraciones(self.tenant_id)

    # --- Consulta ---

    def listar(self, solo_activos: bool = False) -> List[Cupon]:
        return self._generador.listar_cupones(self.tenant_id, solo_activos)

    def obtener_por_codigo(self, codigo: str) -> Cupon:
        return self._generador.obtener_por_codigo(self.tenant_id, codigo)

    # --- Reportes ---

    def resumen(self) -> dict:
        return self._metricas.resumen(self.tenant_id)

    def top_cupones(self, top: int = 10) -> List[dict]:
        return self._metricas.cupones_mas_usados(self.tenant_id, top)

    def tasa_conversion(self) -> dict:
        return self._metricas.tasa_conversion(self.tenant_id)


class FidelizacionFacade:
    """
    API de alto nivel para el programa de fidelización de una tienda.
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self._acumulador = PuntosAcumulador(_plan_service, _cuenta_repo, _movimiento_repo)
        self._canjeador = PuntosCanjeador(_plan_service, _cuenta_repo, _movimiento_repo)
        self._nivel_motor = NivelMotor(_plan_service, _cuenta_repo)
        self._cuenta_svc = CuentaClienteService(_plan_service, _cuenta_repo, _movimiento_repo)
        self._historial_svc = HistorialClienteService(_cuenta_repo, _movimiento_repo)
        self._metricas = MetricasFidelizacionService(_plan_service, _cuenta_repo, _movimiento_repo)

    # --- Configuración ---

    def configurar(
        self,
        nombre: str,
        puntos_por_peso: float = 0.1,
        unidad_moneda: float = 10.0,
        puntos_para_canje: int = 100,
        valor_punto: float = 0.10,
        dias_expiracion: Optional[int] = None,
    ):
        return _plan_service.configurar_plan(
            self.tenant_id,
            nombre=nombre,
            puntos_por_unidad_moneda=puntos_por_peso,
            unidad_moneda=unidad_moneda,
            puntos_para_canje=puntos_para_canje,
            valor_punto_en_moneda=valor_punto,
            dias_expiracion_puntos=dias_expiracion,
        )

    # --- Operaciones de cliente ---

    def registrar_compra(
        self,
        cliente_id: str,
        monto: float,
        referencia: Optional[str] = None,
    ):
        movimiento = self._acumulador.acreditar(
            self.tenant_id, cliente_id, monto, referencia
        )
        self._nivel_motor.evaluar_y_actualizar(self.tenant_id, cliente_id)
        return movimiento

    def saldo(self, cliente_id: str) -> int:
        return self._acumulador.obtener_saldo(self.tenant_id, cliente_id)

    def canjear_puntos(
        self,
        cliente_id: str,
        puntos: int,
        referencia: Optional[str] = None,
    ) -> ResultadoCanje:
        resultado = self._canjeador.canjear(
            self.tenant_id, cliente_id, puntos, referencia
        )
        return resultado

    def preview_canje(self, cliente_id: str, puntos: int) -> ResultadoCanje:
        return self._canjeador.preview_canje(self.tenant_id, cliente_id, puntos)

    # --- Consulta de cuenta ---

    def resumen_cliente(self, cliente_id: str) -> dict:
        return self._cuenta_svc.resumen(self.tenant_id, cliente_id)

    def historial(
        self,
        cliente_id: str,
        pagina: int = 1,
        por_pagina: int = 20,
    ) -> dict:
        return self._historial_svc.obtener_historial(
            self.tenant_id, cliente_id, pagina=pagina, por_pagina=por_pagina
        )

    def ajuste_manual(
        self,
        cliente_id: str,
        puntos: int,
        motivo: str,
        operador_id: str,
    ) -> dict:
        return self._cuenta_svc.ajuste_manual(
            self.tenant_id, cliente_id, puntos, motivo, operador_id
        )

    # --- Reportes ---

    def resumen_programa(self) -> dict:
        return self._metricas.resumen(self.tenant_id)

    def distribucion_niveles(self) -> dict:
        return self._metricas.distribucion_niveles(self.tenant_id)

    def top_clientes(self, top: int = 10) -> List[dict]:
        return self._metricas.top_clientes(self.tenant_id, top)

    def clientes_inactivos(self, dias: int = 90) -> List[dict]:
        return self._metricas.clientes_inactivos(self.tenant_id, dias)
