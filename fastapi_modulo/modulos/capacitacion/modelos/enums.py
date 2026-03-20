from enum import Enum


class NivelCurso(str, Enum):
    BASICO = "basico"
    INTERMEDIO = "intermedio"
    AVANZADO = "avanzado"


class EstadoCurso(str, Enum):
    BORRADOR = "borrador"
    PUBLICADO = "publicado"
    ARCHIVADO = "archivado"


class TipoLeccion(str, Enum):
    TEXTO = "texto"
    VIDEO = "video"
    DOCUMENTO = "documento"
    ENLACE = "enlace"


class EstadoInscripcion(str, Enum):
    PENDIENTE = "pendiente"
    EN_PROGRESO = "en_progreso"
    COMPLETADO = "completado"
    REPROBADO = "reprobado"


class TipoPregunta(str, Enum):
    OPCION_MULTIPLE = "opcion_multiple"
    VERDADERO_FALSO = "verdadero_falso"
    TEXTO_LIBRE = "texto_libre"


class EstadoPresentacion(str, Enum):
    BORRADOR = "borrador"
    PUBLICADO = "publicado"


class RolCapacitacion(str, Enum):
    ADMIN = "admin"
    COORDINADOR = "coordinador"
    INSTRUCTOR = "instructor"
    COLABORADOR = "colaborador"
    LECTOR = "lector"


class PermisoCapacitacion(str, Enum):
    VER = "capacitacion.ver"
    CATALOGO_VER = "capacitacion.catalogo.ver"
    CATALOGO_EDITAR = "capacitacion.catalogo.editar"
    DASHBOARD_VER = "capacitacion.dashboard.ver"
    INSCRIPCIONES_GESTIONAR = "capacitacion.inscripciones.gestionar"
    AUTOGESTION_INSCRIBIRSE = "capacitacion.autogestion.inscribirse"
    AUTOGESTION_PROGRESO = "capacitacion.autogestion.progreso"
    AUTOGESTION_EVALUACIONES = "capacitacion.autogestion.evaluaciones"
    EVALUACIONES_GESTIONAR = "capacitacion.evaluaciones.gestionar"
    PRESENTACIONES_VER = "capacitacion.presentaciones.ver"
    PRESENTACIONES_GESTIONAR = "capacitacion.presentaciones.gestionar"
    GAMIFICACION_GESTIONAR = "capacitacion.gamificacion.gestionar"
    CERTIFICADOS_VER = "capacitacion.certificados.ver"
    AUDITORIA_VER = "capacitacion.auditoria.ver"
