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
    # Fase lead
    NUEVO_LEAD = "nuevo_lead"
    POR_CONTACTAR = "por_contactar"
    CONTACTADO = "contactado"
    CALIFICADO = "calificado"
    NO_CALIFICADO = "no_calificado"
    # Fase oportunidad
    DIAGNOSTICO = "diagnostico"
    NEGOCIACION = "negociacion"
    PROPUESTA_ENVIADA = "propuesta_enviada"
    SEGUIMIENTO_PROPUESTA = "seguimiento_propuesta"
    DECISION = "decision"
    # Cierre
    CERRADO_GANADO = "cerrado_ganado"
    CERRADO_PERDIDO = "cerrado_perdido"
    CONGELADO = "congelado"
    SIN_RESPUESTA = "sin_respuesta"
    # Legado (compatibilidad con datos anteriores)
    PROSPECTO = "prospecto"
    PROPUESTA = "propuesta"


# Etapas que están activas/abiertas (no cerradas)
ETAPAS_ABIERTAS: set[str] = {
    EtapaOportunidad.NUEVO_LEAD.value,
    EtapaOportunidad.POR_CONTACTAR.value,
    EtapaOportunidad.CONTACTADO.value,
    EtapaOportunidad.CALIFICADO.value,
    EtapaOportunidad.NO_CALIFICADO.value,
    EtapaOportunidad.DIAGNOSTICO.value,
    EtapaOportunidad.NEGOCIACION.value,
    EtapaOportunidad.PROPUESTA_ENVIADA.value,
    EtapaOportunidad.SEGUIMIENTO_PROPUESTA.value,
    EtapaOportunidad.DECISION.value,
    # Legado
    EtapaOportunidad.PROSPECTO.value,
    EtapaOportunidad.PROPUESTA.value,
}

ETAPAS_CERRADAS: set[str] = {
    EtapaOportunidad.CERRADO_GANADO.value,
    EtapaOportunidad.CERRADO_PERDIDO.value,
    EtapaOportunidad.CONGELADO.value,
    EtapaOportunidad.SIN_RESPUESTA.value,
}

# Orden lógico del embudo para reporting
ORDEN_EMBUDO: list[str] = [
    EtapaOportunidad.NUEVO_LEAD.value,
    EtapaOportunidad.POR_CONTACTAR.value,
    EtapaOportunidad.CONTACTADO.value,
    EtapaOportunidad.CALIFICADO.value,
    EtapaOportunidad.DIAGNOSTICO.value,
    EtapaOportunidad.NEGOCIACION.value,
    EtapaOportunidad.PROPUESTA_ENVIADA.value,
    EtapaOportunidad.SEGUIMIENTO_PROPUESTA.value,
    EtapaOportunidad.DECISION.value,
    EtapaOportunidad.CERRADO_GANADO.value,
    EtapaOportunidad.CERRADO_PERDIDO.value,
    EtapaOportunidad.CONGELADO.value,
    EtapaOportunidad.SIN_RESPUESTA.value,
    EtapaOportunidad.NO_CALIFICADO.value,
    # Legado
    EtapaOportunidad.PROSPECTO.value,
    EtapaOportunidad.PROPUESTA.value,
]


class TipoActividad(str, Enum):
    TAREA = "tarea"
    LLAMADA = "llamada"
    REUNION = "reunion"
    EMAIL = "email"
    VISITA = "visita"


class PrioridadActividad(str, Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class EstadoActividad(str, Enum):
    PENDIENTE = "pendiente"
    EN_PROCESO = "en_proceso"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"
    VENCIDA = "vencida"
    REPROGRAMADA = "reprogramada"


class TipoResultadoActividad(str, Enum):
    NO_CONTESTO = "no_contesto"
    INTERESADO = "interesado"
    NO_INTERESADO = "no_interesado"
    REAGENDAR = "reagendar"
    ENVIO_DOCUMENTOS = "envio_documentos"
    PENDIENTE_PROPUESTA = "pendiente_propuesta"
    OTRO = "otro"


# SLA en horas por tipo de actividad (predeterminado)
SLA_POR_TIPO: dict[str, int] = {
    TipoActividad.LLAMADA.value: 2,
    TipoActividad.EMAIL.value: 4,
    TipoActividad.TAREA.value: 24,
    TipoActividad.REUNION.value: 48,
    TipoActividad.VISITA.value: 48,
}


class TipoCampania(str, Enum):
    EMAIL = "email"
    LLAMADA = "llamada"
    EVENTO = "evento"
    PROMOCION = "promocion"


class TipoObjetivoCampania(str, Enum):
    CAPTACION = "captacion"
    REACTIVACION = "reactivacion"
    REFERIDOS = "referidos"
    PROMOCION = "promocion"
    COBRANZA_PREVENTIVA = "cobranza_preventiva"
    COLOCACION = "colocacion"
    FIDELIZACION = "fidelizacion"
    EVENTO = "evento"


class EstadoCampania(str, Enum):
    BORRADOR = "borrador"
    ACTIVA = "activa"
    FINALIZADA = "finalizada"


class EstadoContactoCampania(str, Enum):
    PENDIENTE = "pendiente"
    CONTACTADO = "contactado"
    CONVERTIDO = "convertido"
