from __future__ import annotations
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
import re

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


class EjecutivoCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: str = Field(default="", max_length=255)
    phone: str = Field(default="", max_length=50)
    especialidad: str = Field(default="", max_length=255)
    disponible: bool = True
    tiempo_promedio_cita: int = Field(default=30, gt=0, le=480)
    tiempo_descanso_sesiones: int = Field(default=0, ge=0, le=120)
    hora_inicial_lunes: float = 9.0
    hora_final_lunes: float = 17.0
    hora_inicial_martes: float = 9.0
    hora_final_martes: float = 17.0
    hora_inicial_miercoles: float = 9.0
    hora_final_miercoles: float = 17.0
    hora_inicial_jueves: float = 9.0
    hora_final_jueves: float = 17.0
    hora_inicial_viernes: float = 9.0
    hora_final_viernes: float = 17.0
    hora_inicial_sabado: float = 9.0
    hora_final_sabado: float = 13.0
    descanso_lunes: bool = False
    descanso_martes: bool = False
    descanso_miercoles: bool = False
    descanso_jueves: bool = False
    descanso_viernes: bool = False
    descanso_sabado: bool = True
    descanso_domingo: bool = True
    notas: str = ""

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if v and not _EMAIL_RE.match(v):
            raise ValueError('Correo electrónico inválido')
        return v

    @model_validator(mode='after')
    def validate_horarios(self) -> 'EjecutivoCreate':
        dias = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
        for dia in dias:
            descanso = getattr(self, f'descanso_{dia}', True)
            if not descanso:
                ini = getattr(self, f'hora_inicial_{dia}', 0.0)
                fin = getattr(self, f'hora_final_{dia}', 0.0)
                if fin <= ini:
                    raise ValueError(f'hora_final_{dia} debe ser mayor que hora_inicial_{dia}')
        return self


class EjecutivoUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    especialidad: Optional[str] = None
    disponible: Optional[bool] = None
    tiempo_promedio_cita: Optional[int] = None
    tiempo_descanso_sesiones: Optional[int] = None
    hora_inicial_lunes: Optional[float] = None
    hora_final_lunes: Optional[float] = None
    hora_inicial_martes: Optional[float] = None
    hora_final_martes: Optional[float] = None
    hora_inicial_miercoles: Optional[float] = None
    hora_final_miercoles: Optional[float] = None
    hora_inicial_jueves: Optional[float] = None
    hora_final_jueves: Optional[float] = None
    hora_inicial_viernes: Optional[float] = None
    hora_final_viernes: Optional[float] = None
    hora_inicial_sabado: Optional[float] = None
    hora_final_sabado: Optional[float] = None
    descanso_lunes: Optional[bool] = None
    descanso_martes: Optional[bool] = None
    descanso_miercoles: Optional[bool] = None
    descanso_jueves: Optional[bool] = None
    descanso_viernes: Optional[bool] = None
    descanso_sabado: Optional[bool] = None
    descanso_domingo: Optional[bool] = None
    notas: Optional[str] = None


class EjecutivoRead(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    especialidad: str
    disponible: bool
    active: bool
    tiempo_promedio_cita: int
    tiempo_descanso_sesiones: int
    hora_inicial_lunes: float
    hora_final_lunes: float
    hora_inicial_martes: float
    hora_final_martes: float
    hora_inicial_miercoles: float
    hora_final_miercoles: float
    hora_inicial_jueves: float
    hora_final_jueves: float
    hora_inicial_viernes: float
    hora_final_viernes: float
    hora_inicial_sabado: float
    hora_final_sabado: float
    descanso_lunes: bool
    descanso_martes: bool
    descanso_miercoles: bool
    descanso_jueves: bool
    descanso_viernes: bool
    descanso_sabado: bool
    descanso_domingo: bool
    notas: str

    class Config:
        from_attributes = True


class TipoCitaCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    duracion_minutos: int = Field(default=30, gt=0, le=480)
    color: str = Field(default="#1a6b3c", max_length=20)


class TipoCitaRead(BaseModel):
    id: int
    name: str
    duracion_minutos: int
    color: str
    active: bool

    class Config:
        from_attributes = True


class CitaCreate(BaseModel):
    name: str = Field(default="Nueva Cita", max_length=255)
    nombre_persona: str = Field(..., min_length=2, max_length=255)
    celular_persona: str = Field(default="", max_length=50)
    email_persona: str = Field(default="", max_length=255)
    start_datetime: datetime
    ejecutivo_id: Optional[int] = None
    tipo_id: Optional[int] = None
    notes: str = ""

    @field_validator('email_persona')
    @classmethod
    def validate_email_persona(cls, v: str) -> str:
        if v and not _EMAIL_RE.match(v):
            raise ValueError('Correo electrónico inválido')
        return v

    @field_validator('start_datetime')
    @classmethod
    def validate_start_futuro(cls, v: datetime) -> datetime:
        if v < datetime.now():
            raise ValueError('La fecha de la cita no puede ser en el pasado')
        return v


class CitaUpdate(BaseModel):
    state: Optional[str] = None
    notes: Optional[str] = None
    start_datetime: Optional[datetime] = None
    ejecutivo_id: Optional[int] = None


class CitaRead(BaseModel):
    id: int
    name: str
    nombre_persona: str
    celular_persona: str
    email_persona: str
    start_datetime: datetime
    end_datetime: Optional[datetime] = None
    ejecutivo_id: Optional[int]
    tipo_id: Optional[int]
    state: str
    source: str
    notes: str
    confirmed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SlotInfo(BaseModel):
    datetime_str: str
    hora: str
    disponible: bool


class CitaEstadoUpdate(BaseModel):
    state: Literal['draft', 'confirmed', 'in_progress', 'completed', 'cancelled', 'no_show']
    motivo: Optional[str] = None


class ReprogramarCita(BaseModel):
    new_start_datetime: datetime
    motivo: Optional[str] = None

    @field_validator('new_start_datetime')
    @classmethod
    def validate_nueva_fecha(cls, v: datetime) -> datetime:
        if v < datetime.now():
            raise ValueError('La nueva fecha no puede ser en el pasado')
        return v


class CitaReadDetail(CitaRead):
    ejecutivo_name: Optional[str] = None
    tipo_name: Optional[str] = None
    tipo_duracion_minutos: Optional[int] = None


# ── Bloqueos de agenda ────────────────────────────────────────────────────────

class BloqueoCreate(BaseModel):
    ejecutivo_id: int
    start_datetime: datetime
    end_datetime: datetime
    motivo: str = ""

    @model_validator(mode='after')
    def validate_rango(self) -> 'BloqueoCreate':
        if self.end_datetime <= self.start_datetime:
            raise ValueError('end_datetime debe ser posterior a start_datetime')
        return self


class BloqueoRead(BaseModel):
    id: int
    ejecutivo_id: int
    start_datetime: datetime
    end_datetime: datetime
    motivo: str
    active: bool

    class Config:
        from_attributes = True


# ── Excepciones por fecha ─────────────────────────────────────────────────────

class ExcepcionCreate(BaseModel):
    fecha: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')
    ejecutivo_id: Optional[int] = None
    motivo: str = ""


class ExcepcionRead(BaseModel):
    id: int
    ejecutivo_id: Optional[int]
    fecha: str
    motivo: str
    active: bool

    class Config:
        from_attributes = True


# ── Franjas horarias semanales ────────────────────────────────────────────────

class FranjaCreate(BaseModel):
    dia_semana: int = Field(..., ge=0, le=6)
    hora_ini: float = Field(..., ge=0.0, lt=24.0)
    hora_fin: float = Field(..., ge=0.0, le=24.0)

    @model_validator(mode='after')
    def validate_rango(self) -> 'FranjaCreate':
        if self.hora_fin <= self.hora_ini:
            raise ValueError('hora_fin debe ser posterior a hora_ini')
        return self


class FranjaRead(BaseModel):
    id: int
    ejecutivo_id: int
    dia_semana: int
    hora_ini: float
    hora_fin: float
    active: bool

    class Config:
        from_attributes = True
