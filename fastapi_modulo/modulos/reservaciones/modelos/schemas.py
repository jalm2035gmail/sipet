from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class EjecutivoCreate(BaseModel):
    name: str
    email: str = ""
    phone: str = ""
    especialidad: str = ""
    disponible: bool = True
    tiempo_promedio_cita: int = 30
    tiempo_descanso_sesiones: int = 0
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
    name: str
    duracion: float = 1.0
    color: str = "#1a6b3c"


class TipoCitaRead(BaseModel):
    id: int
    name: str
    duracion: float
    color: str
    active: bool

    class Config:
        from_attributes = True


class CitaCreate(BaseModel):
    name: str = "Nueva Cita"
    nombre_persona: str
    celular_persona: str = ""
    email_persona: str = ""
    start_datetime: datetime
    ejecutivo_id: Optional[int] = None
    tipo_id: Optional[int] = None
    notes: str = ""


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
    ejecutivo_id: Optional[int]
    tipo_id: Optional[int]
    state: str
    notes: str
    created_at: datetime

    class Config:
        from_attributes = True


class SlotInfo(BaseModel):
    datetime_str: str
    hora: str
    disponible: bool
