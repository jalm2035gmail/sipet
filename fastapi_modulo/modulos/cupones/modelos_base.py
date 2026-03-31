"""
modelos_base.py
---------------
Modelos de datos compartidos en todo el módulo.
Usa dataclasses para mantener independencia de cualquier ORM.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


# ---------------------------------------------------------------------------
# Enums globales
# ---------------------------------------------------------------------------

class EstadoGeneral(str, Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"
    SUSPENDIDO = "suspendido"
    ELIMINADO = "eliminado"


class TipoDescuento(str, Enum):
    PORCENTAJE = "porcentaje"
    MONTO_FIJO = "monto_fijo"
    ENVIO_GRATIS = "envio_gratis"


class EstadoCupon(str, Enum):
    ACTIVO = "activo"
    PAUSADO = "pausado"
    EXPIRADO = "expirado"
    AGOTADO = "agotado"
    REVOCADO = "revocado"


class TipoMovimientoPuntos(str, Enum):
    ACUMULACION = "acumulacion"
    CANJE = "canje"
    EXPIRACION = "expiracion"
    AJUSTE_MANUAL = "ajuste_manual"
    DEVOLUCION = "devolucion"


class NivelFidelizacion(str, Enum):
    BRONCE = "bronce"
    PLATA = "plata"
    ORO = "oro"
    PLATINO = "platino"


# ---------------------------------------------------------------------------
# Modelos base
# ---------------------------------------------------------------------------

@dataclass
class Tienda:
    nombre: str
    moneda: str = "MXN"
    zona_horaria: str = "America/Mexico_City"
    estado: EstadoGeneral = EstadoGeneral.ACTIVO
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    creado_en: datetime = field(default_factory=datetime.utcnow)
    configuracion_extra: dict = field(default_factory=dict)


@dataclass
class ConfiguracionPlan:
    """Define las reglas del programa de fidelización de una tienda."""
    tenant_id: str
    nombre: str
    puntos_por_unidad_moneda: float          # ej. 1 punto por cada $10
    unidad_moneda: float = 10.0              # cada cuántos pesos se otorga 1 punto
    puntos_para_canje: int = 100             # puntos mínimos para poder canjear
    valor_punto_en_moneda: float = 0.10      # valor de 1 punto en moneda local
    dias_expiracion_puntos: Optional[int] = None   # None = no expiran
    tiers: dict = field(default_factory=lambda: {
        NivelFidelizacion.BRONCE: 0,
        NivelFidelizacion.PLATA: 1000,
        NivelFidelizacion.ORO: 5000,
        NivelFidelizacion.PLATINO: 15000,
    })
    activo: bool = True
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    creado_en: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Cupon:
    tenant_id: str
    codigo: str
    tipo_descuento: TipoDescuento
    valor: float                              # % o monto fijo
    fecha_inicio: datetime
    fecha_fin: datetime
    usos_maximos: Optional[int] = None        # None = ilimitado
    usos_actuales: int = 0
    monto_minimo_compra: float = 0.0
    categorias_aplicables: list = field(default_factory=list)   # [] = todas
    productos_excluidos: list = field(default_factory=list)
    solo_primera_compra: bool = False
    estado: EstadoCupon = EstadoCupon.ACTIVO
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    creado_en: datetime = field(default_factory=datetime.utcnow)
    descripcion: str = ""


@dataclass
class CuentaFidelizacion:
    tenant_id: str
    cliente_id: str
    puntos_actuales: int = 0
    puntos_acumulados_total: int = 0
    puntos_canjeados_total: int = 0
    nivel: NivelFidelizacion = NivelFidelizacion.BRONCE
    activo: bool = True
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    creado_en: datetime = field(default_factory=datetime.utcnow)
    ultima_actividad: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MovimientoPuntos:
    cuenta_id: str
    tenant_id: str
    tipo: TipoMovimientoPuntos
    puntos: int                               # positivo = ganancia, negativo = débito
    saldo_resultante: int
    referencia_transaccion: Optional[str] = None
    descripcion: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    creado_en: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RegistroUsoCupon:
    cupon_id: str
    tenant_id: str
    cliente_id: str
    transaccion_id: str
    descuento_aplicado: float
    monto_original: float
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    creado_en: datetime = field(default_factory=datetime.utcnow)
