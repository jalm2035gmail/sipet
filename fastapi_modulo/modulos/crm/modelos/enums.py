from __future__ import annotations

from enum import Enum


class TipoContacto(str, Enum):
    PROSPECTO = "prospecto"
    CLIENTE = "cliente"
    INACTIVO = "inactivo"


class FuenteContacto(str, Enum):
    MANUAL = "manual"
    BACKEND = "backend"
    REFERIDO = "referido"
    CAMPANIA = "campania"


class EtapaOportunidad(str, Enum):
    PROSPECTO = "prospecto"
    NEGOCIACION = "negociacion"
    PROPUESTA = "propuesta"
    CERRADO_GANADO = "cerrado_ganado"
    CERRADO_PERDIDO = "cerrado_perdido"


class TipoActividad(str, Enum):
    TAREA = "tarea"
    LLAMADA = "llamada"
    REUNION = "reunion"
    EMAIL = "email"
    VISITA = "visita"


class TipoCampania(str, Enum):
    EMAIL = "email"
    LLAMADA = "llamada"
    EVENTO = "evento"
    PROMOCION = "promocion"


class EstadoCampania(str, Enum):
    BORRADOR = "borrador"
    ACTIVA = "activa"
    FINALIZADA = "finalizada"


class EstadoContactoCampania(str, Enum):
    PENDIENTE = "pendiente"
    CONTACTADO = "contactado"
    CONVERTIDO = "convertido"
