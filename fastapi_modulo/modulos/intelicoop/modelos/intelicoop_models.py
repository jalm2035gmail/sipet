from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


VALID_CREDITO_ESTADOS = {
    "solicitado",
    "aprobado",
    "vigente",
    "liquidado",
    "rechazado",
    "mora",
    "reestructurado",
}


class IntelicoopMAINModel(BaseModel):
    model_config = ConfigDict(protected_namespaces=())


class SocioCreate(IntelicoopMAINModel):
    nombre: str = Field(min_length=1)
    email: str = Field(min_length=3)
    telefono: str = ""
    direccion: str = ""
    segmento: str = "inactivo"
    fecha_nacimiento: Optional[date] = None
    genero: str = ""
    estado_civil: str = ""
    nivel_educativo: str = ""
    ocupacion: str = ""
    sector_economico: str = ""
    ubicacion_estado: str = ""
    ubicacion_municipio: str = ""
    tipo_socio: str = "activo"


class CreditoCreate(IntelicoopMAINModel):
    socio_id: int
    monto: float = Field(ge=0)
    numero_abonos: int = Field(ge=1)
    periodicidad: str = "mensual"
    ingreso_mensual: float = Field(ge=0, default=0)
    deuda_actual: float = Field(ge=0, default=0)
    antiguedad_meses: int = Field(ge=0, default=0)
    tasa: float = Field(ge=0, default=0)
    estado: str = "solicitado"
    dias_mora_actual: int = Field(ge=0, default=0)
    max_dias_mora: int = Field(ge=0, default=0)
    num_reestructuras: int = Field(ge=0, default=0)
    fecha_desembolso: Optional[datetime] = None
    fecha_vencimiento: Optional[datetime] = None

    @field_validator("periodicidad")
    @classmethod
    def validate_periodicidad(cls, value: str) -> str:
        normalized = str(value or "mensual").strip().lower() or "mensual"
        if normalized not in {"mensual", "quincenal", "semanal", "bimestral"}:
            raise ValueError("Periodicidad invalida.")
        return normalized

    @field_validator("estado")
    @classmethod
    def validate_estado(cls, value: str) -> str:
        normalized = str(value or "solicitado").strip().lower() or "solicitado"
        if normalized not in VALID_CREDITO_ESTADOS:
            raise ValueError("Estado de credito invalido.")
        return normalized


class CampaniaCreate(IntelicoopMAINModel):
    nombre: str = Field(min_length=1)
    tipo: str = Field(min_length=1)
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    estado: str = "borrador"


class ProspectoCreate(IntelicoopMAINModel):
    nombre: str = Field(min_length=1)
    telefono: str = ""
    direccion: str = ""
    fuente: str = ""
    score_propension: float = Field(ge=0, le=1, default=0)


class ContactoCampaniaCreate(IntelicoopMAINModel):
    campania_id: int
    socio_id: int
    ejecutivo_id: str = "ejecutivo_general"
    canal: str = "telefono"
    estado_contacto: str = "pendiente"


class SeguimientoCampaniaCreate(IntelicoopMAINModel):
    campania_id: int
    socio_id: int
    lista: str = "general"
    etapa: str = "contactado"
    conversion: bool = False
    monto_colocado: float = Field(ge=0, default=0)


class CuentaCreate(IntelicoopMAINModel):
    socio_id: int
    tipo: str = "ahorro"
    saldo: float = Field(ge=0, default=0)


class TransaccionCreate(IntelicoopMAINModel):
    cuenta_id: int
    monto: float = Field(gt=0)
    tipo: str = "deposito"
    canal: str = ""


class HistorialPagoCreate(IntelicoopMAINModel):
    credito_id: int
    monto: float = Field(gt=0)
    pago_puntual: bool = True
    dias_atraso: int = Field(ge=0, default=0)


class ScoringEvaluateInput(IntelicoopMAINModel):
    solicitud_id: Optional[str] = None
    socio_id: Optional[int] = None
    credito_id: Optional[int] = None
    ingreso_mensual: float = Field(ge=0)
    deuda_actual: float = Field(ge=0, default=0)
    antiguedad_meses: int = Field(ge=0, default=0)


class FoundationMaterializeInput(IntelicoopMAINModel):
    cut_type: str = "daily_close"


class BatchExecuteInput(IntelicoopMAINModel):
    job_key: str = Field(min_length=1)


class ScoringResult(IntelicoopMAINModel):
    id: int
    solicitud_id: str
    socio_id: Optional[int] = None
    credito_id: Optional[int] = None
    ingreso_mensual: float
    deuda_actual: float
    antiguedad_meses: int
    score: float
    recomendacion: str
    riesgo: str
    model_version: str
    confianza: Optional[float] = None
    motor: str = "reglas"
    explicacion_json: dict = Field(default_factory=dict)
    traza_id: Optional[int] = None
    traza_version: Optional[str] = None
    fecha_creacion: datetime
