from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from fastapi_modulo.modulos.crm.modelos.enums import (
    EstadoCampania,
    EstadoContactoCampania,
    EtapaOportunidad,
    FuenteContacto,
    TipoActividad,
    TipoCampania,
    TipoContacto,
)


class CrmMAIN(BaseModel):
    model_config = ConfigDict(protected_namespaces=())


class ContactoCreate(CrmMAIN):
    nombre: str = Field(min_length=3)
    email: Optional[str] = None
    telefono: str = ""
    empresa: str = ""
    puesto: str = ""
    sucursal: str = ""
    tipo: TipoContacto = TipoContacto.PROSPECTO
    fuente: FuenteContacto = FuenteContacto.MANUAL
    fuente_detalle: str = ""
    notas: Optional[str] = None
    asignado_a: str = ""

    @field_validator("nombre")
    @classmethod
    def validate_nombre(cls, value: str) -> str:
        normalized = " ".join(str(value or "").split()).strip()
        if len(normalized) < 3:
            raise ValueError("El nombre debe tener al menos 3 caracteres")
        return normalized

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = str(value).strip().lower()
        if not normalized:
            return None
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("Email inválido")
        local, _, domain = normalized.partition("@")
        if "." not in domain or not local or domain.startswith(".") or domain.endswith("."):
            raise ValueError("Email inválido")
        return normalized

    @field_validator("tipo")
    @classmethod
    def validate_tipo(cls, value: TipoContacto | str) -> str:
        return value.value if isinstance(value, TipoContacto) else value

    @field_validator("fuente")
    @classmethod
    def validate_fuente(cls, value: FuenteContacto | str) -> str:
        return value.value if isinstance(value, FuenteContacto) else value


class ContactoUpdate(CrmMAIN):
    nombre: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    empresa: Optional[str] = None
    puesto: Optional[str] = None
    sucursal: Optional[str] = None
    tipo: Optional[TipoContacto] = None
    fuente: Optional[FuenteContacto] = None
    fuente_detalle: Optional[str] = None
    notas: Optional[str] = None
    asignado_a: Optional[str] = None

    @field_validator("nombre")
    @classmethod
    def validate_nombre(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = " ".join(str(value or "").split()).strip()
        if len(normalized) < 3:
            raise ValueError("El nombre debe tener al menos 3 caracteres")
        return normalized

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = str(value).strip().lower()
        if not normalized:
            return None
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("Email inválido")
        local, _, domain = normalized.partition("@")
        if "." not in domain or not local or domain.startswith(".") or domain.endswith("."):
            raise ValueError("Email inválido")
        return normalized

    @field_validator("tipo")
    @classmethod
    def validate_tipo(cls, value: Optional[TipoContacto | str]) -> Optional[str]:
        if value is None:
            return None
        return value.value if isinstance(value, TipoContacto) else value

    @field_validator("fuente")
    @classmethod
    def validate_fuente(cls, value: Optional[FuenteContacto | str]) -> Optional[str]:
        if value is None:
            return None
        return value.value if isinstance(value, FuenteContacto) else value


class OportunidadCreate(CrmMAIN):
    contacto_id: int
    nombre: str = Field(min_length=1)
    sucursal: str = ""
    etapa: EtapaOportunidad = EtapaOportunidad.PROSPECTO
    valor_estimado: float = Field(ge=0, default=0.0)
    probabilidad: int = Field(ge=0, le=100, default=0)
    fecha_cierre_est: Optional[date] = None
    fecha_cierre_real: Optional[date] = None
    asignado_a: str = ""
    responsable: str = ""
    descripcion: Optional[str] = None

    @field_validator("nombre")
    @classmethod
    def validate_nombre(cls, value: str) -> str:
        normalized = " ".join(str(value or "").split()).strip()
        if len(normalized) < 3:
            raise ValueError("El nombre de la oportunidad debe tener al menos 3 caracteres")
        return normalized

    @field_validator("etapa")
    @classmethod
    def validate_etapa(cls, value: EtapaOportunidad | str) -> str:
        return value.value if isinstance(value, EtapaOportunidad) else value

    @model_validator(mode="after")
    def validate_cierre(self):
        if self.etapa in {EtapaOportunidad.CERRADO_GANADO.value, EtapaOportunidad.CERRADO_PERDIDO.value} and self.fecha_cierre_real is None:
            self.fecha_cierre_real = date.today()
        return self


class OportunidadUpdate(CrmMAIN):
    nombre: Optional[str] = None
    sucursal: Optional[str] = None
    etapa: Optional[EtapaOportunidad] = None
    valor_estimado: Optional[float] = None
    probabilidad: Optional[int] = None
    fecha_cierre_est: Optional[date] = None
    fecha_cierre_real: Optional[date] = None
    asignado_a: Optional[str] = None
    responsable: Optional[str] = None
    descripcion: Optional[str] = None

    @field_validator("nombre")
    @classmethod
    def validate_nombre(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = " ".join(str(value or "").split()).strip()
        if len(normalized) < 3:
            raise ValueError("El nombre de la oportunidad debe tener al menos 3 caracteres")
        return normalized

    @field_validator("etapa")
    @classmethod
    def validate_etapa(cls, value: Optional[EtapaOportunidad | str]) -> Optional[str]:
        if value is None:
            return None
        return value.value if isinstance(value, EtapaOportunidad) else value


class ActividadCreate(CrmMAIN):
    contacto_id: Optional[int] = None
    oportunidad_id: Optional[int] = None
    tipo: TipoActividad = TipoActividad.TAREA
    titulo: str = Field(min_length=1)
    descripcion: Optional[str] = None
    fecha: datetime = Field(default_factory=datetime.utcnow)
    completada: bool = False
    fecha_completada: Optional[datetime] = None
    asignado_a: str = ""
    responsable: str = ""

    @field_validator("tipo")
    @classmethod
    def validate_tipo(cls, value: TipoActividad | str) -> str:
        return value.value if isinstance(value, TipoActividad) else value

    @field_validator("titulo")
    @classmethod
    def validate_titulo(cls, value: str) -> str:
        normalized = " ".join(str(value or "").split()).strip()
        if len(normalized) < 3:
            raise ValueError("El título debe tener al menos 3 caracteres")
        return normalized

    @model_validator(mode="after")
    def validate_relations(self):
        if self.contacto_id is None and self.oportunidad_id is None:
            raise ValueError("La actividad requiere contacto u oportunidad")
        if self.fecha is None:
            raise ValueError("La actividad requiere fecha")
        if self.completada and self.fecha_completada is None:
            self.fecha_completada = datetime.utcnow()
        return self


class ActividadUpdate(CrmMAIN):
    tipo: Optional[TipoActividad] = None
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    fecha: Optional[datetime] = None
    completada: Optional[bool] = None
    fecha_completada: Optional[datetime] = None
    asignado_a: Optional[str] = None
    responsable: Optional[str] = None

    @field_validator("tipo")
    @classmethod
    def validate_tipo(cls, value: Optional[TipoActividad | str]) -> Optional[str]:
        if value is None:
            return None
        return value.value if isinstance(value, TipoActividad) else value

    @field_validator("titulo")
    @classmethod
    def validate_titulo(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = " ".join(str(value or "").split()).strip()
        if len(normalized) < 3:
            raise ValueError("El título debe tener al menos 3 caracteres")
        return normalized


class NotaCreate(CrmMAIN):
    contacto_id: Optional[int] = None
    oportunidad_id: Optional[int] = None
    contenido: str = Field(min_length=1)
    autor: str = ""


class CampaniaCreate(CrmMAIN):
    nombre: str = Field(min_length=1)
    tipo: TipoCampania = TipoCampania.EMAIL
    estado: EstadoCampania = EstadoCampania.BORRADOR
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    asignado_a: str = ""
    descripcion: Optional[str] = None
    resultado: Optional[str] = None

    @field_validator("nombre")
    @classmethod
    def validate_nombre(cls, value: str) -> str:
        normalized = " ".join(str(value or "").split()).strip()
        if len(normalized) < 3:
            raise ValueError("El nombre de campaña debe tener al menos 3 caracteres")
        return normalized

    @field_validator("tipo")
    @classmethod
    def validate_tipo(cls, value: TipoCampania | str) -> str:
        return value.value if isinstance(value, TipoCampania) else value

    @field_validator("estado")
    @classmethod
    def validate_estado(cls, value: EstadoCampania | str) -> str:
        return value.value if isinstance(value, EstadoCampania) else value

    @model_validator(mode="after")
    def validate_dates(self):
        if self.fecha_inicio and self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise ValueError("La fecha fin no puede ser menor que la fecha inicio")
        return self


class CampaniaUpdate(CrmMAIN):
    nombre: Optional[str] = None
    tipo: Optional[TipoCampania] = None
    estado: Optional[EstadoCampania] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    asignado_a: Optional[str] = None
    descripcion: Optional[str] = None
    resultado: Optional[str] = None

    @field_validator("nombre")
    @classmethod
    def validate_nombre(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = " ".join(str(value or "").split()).strip()
        if len(normalized) < 3:
            raise ValueError("El nombre de campaña debe tener al menos 3 caracteres")
        return normalized

    @field_validator("tipo")
    @classmethod
    def validate_tipo(cls, value: Optional[TipoCampania | str]) -> Optional[str]:
        if value is None:
            return None
        return value.value if isinstance(value, TipoCampania) else value

    @field_validator("estado")
    @classmethod
    def validate_estado(cls, value: Optional[EstadoCampania | str]) -> Optional[str]:
        if value is None:
            return None
        return value.value if isinstance(value, EstadoCampania) else value


class ContactoCampaniaCreate(CrmMAIN):
    contacto_id: int
    campania_id: int
    estado: EstadoContactoCampania = EstadoContactoCampania.PENDIENTE

    @field_validator("estado")
    @classmethod
    def validate_estado(cls, value: EstadoContactoCampania | str) -> str:
        return value.value if isinstance(value, EstadoContactoCampania) else value


class OportunidadEtapaUpdate(CrmMAIN):
    etapa: EtapaOportunidad

    @field_validator("etapa")
    @classmethod
    def validate_etapa(cls, value: EtapaOportunidad | str) -> str:
        return value.value if isinstance(value, EtapaOportunidad) else value


class ActividadReprogramar(CrmMAIN):
    fecha: datetime


class CampaniaResultadoUpdate(CrmMAIN):
    resultado: str = Field(min_length=3)
