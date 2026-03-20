"""
Modelos SQLAlchemy para el módulo de Capacitación.

Define todas las entidades de la base de datos para el sistema de capacitación:
- Cursos y categorías
- Lecciones y evaluaciones
- Inscripciones y progreso
- Certificados y gamificación
- Presentaciones interactivas
- Auditoría y archivos
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Enum as SAEnum,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import relationship

from fastapi_modulo.core.db import MAIN
from fastapi_modulo.modulos.capacitacion.repositorios.common import get_engine
from fastapi_modulo.modulos.capacitacion.modelos.enums import (
    EstadoCurso,
    EstadoInscripcion,
    EstadoPresentacion,
    NivelCurso,
    TipoLeccion,
    TipoPregunta,
)


# ============================================================================
# MODELOS PRINCIPALES DE CURSOS
# ============================================================================

class CapCategoria(MAIN):
    """
    Categorías para organizar cursos.
    
    Ejemplos: Tecnología, Recursos Humanos, Ventas, Seguridad
    """
    __tablename__ = "cap_categoria"
    __table_args__ = (
        UniqueConstraint("tenant_id", "nombre", name="uq_cap_categoria_tenant_nombre"),
        Index("ix_cap_categoria_tenant", "tenant_id"),
    )

    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, index=True)
    descripcion = Column(Text, nullable=True)
    color = Column(String(30), nullable=True)
    creado_en = Column(DateTime, nullable=True, default=datetime.utcnow)

    # Relaciones
    cursos = relationship(
        "CapCurso",
        back_populates="categoria",
        cascade="save-update, merge"
    )


class CapCurso(MAIN):
    """
    Curso de capacitación.
    
    Contiene información del curso, configuración de evaluación,
    fechas, requisitos y opciones de certificación.
    """
    __tablename__ = "cap_curso"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_cap_curso_tenant_codigo"),
        Index("ix_cap_curso_tenant", "tenant_id"),
        Index("ix_cap_curso_estado", "estado"),
        Index("ix_cap_curso_categoria", "categoria_id"),
        Index("ix_cap_curso_rol", "rol_objetivo"),
        Index("ix_cap_curso_puesto", "puesto_objetivo"),
    )

    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(30), nullable=True, index=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    objetivo = Column(Text, nullable=True)
    categoria_id = Column(
        Integer,
        ForeignKey("cap_categoria.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    nivel = Column(
        SAEnum(NivelCurso),
        nullable=False,
        default=NivelCurso.BASICO
    )
    estado = Column(
        SAEnum(EstadoCurso),
        nullable=False,
        default=EstadoCurso.BORRADOR,
        index=True
    )
    responsable = Column(String(150), nullable=True)
    duracion_horas = Column(Float, nullable=True)
    puntaje_aprobacion = Column(Float, nullable=False, default=70.0)
    imagen_url = Column(String(400), nullable=True)
    fecha_inicio = Column(Date, nullable=True)
    fecha_fin = Column(Date, nullable=True)
    
    # Configuración de obligatoriedad y vencimiento
    es_obligatorio = Column(Boolean, nullable=False, default=False)
    vence_dias = Column(Integer, nullable=True)
    recordatorio_dias = Column(Integer, nullable=True, default=7)
    reinscripcion_automatica = Column(Boolean, nullable=False, default=False)
    
    # Segmentación y requisitos
    prerrequisitos_json = Column(Text, nullable=True)
    departamentos_json = Column(Text, nullable=True)
    rol_objetivo = Column(String(100), nullable=True, index=True)
    puesto_objetivo = Column(String(150), nullable=True, index=True)
    
    # Configuración de certificación
    bloquear_certificado_encuesta = Column(Boolean, nullable=False, default=False)
    requiere_encuesta_satisfaccion = Column(Boolean, nullable=False, default=False)
    
    # Versionamiento
    version_numero = Column(Integer, nullable=False, default=1)
    version_padre_id = Column(
        Integer,
        ForeignKey("cap_curso.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    version_actual = Column(Boolean, nullable=False, default=True)
    
    # Auditoría
    creado_por = Column(String(100), nullable=True, index=True)
    actualizado_por = Column(String(100), nullable=True, index=True)
    publicado_por = Column(String(100), nullable=True, index=True)
    publicado_en = Column(DateTime, nullable=True)
    creado_en = Column(DateTime, nullable=True, default=datetime.utcnow)
    actualizado_en = Column(
        DateTime,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relaciones
    categoria = relationship("CapCategoria", back_populates="cursos")
    lecciones = relationship(
        "CapLeccion",
        back_populates="curso",
        cascade="all, delete-orphan",
        order_by="CapLeccion.orden"
    )
    inscripciones = relationship(
        "CapInscripcion",
        back_populates="curso",
        cascade="all, delete-orphan"
    )
    evaluaciones = relationship(
        "CapEvaluacion",
        back_populates="curso",
        cascade="all, delete-orphan"
    )
    versiones = relationship(
        "CapCurso",
        remote_side=[id],
        foreign_keys=[version_padre_id]
    )


class CapLeccion(MAIN):
    """
    Lección dentro de un curso.
    
    Puede ser de diferentes tipos: texto, video, PDF, SCORM, etc.
    """
    __tablename__ = "cap_leccion"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "curso_id", "orden",
            name="uq_cap_leccion_tenant_curso_orden"
        ),
        Index("ix_cap_leccion_tenant", "tenant_id"),
        Index("ix_cap_leccion_orden", "curso_id", "orden"),
    )

    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    id = Column(Integer, primary_key=True, index=True)
    curso_id = Column(
        Integer,
        ForeignKey("cap_curso.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    titulo = Column(String(200), nullable=False)
    tipo = Column(
        SAEnum(TipoLeccion),
        nullable=False,
        default=TipoLeccion.TEXTO
    )
    contenido = Column(Text, nullable=True)
    url_archivo = Column(String(400), nullable=True)
    duracion_min = Column(Integer, nullable=True)
    orden = Column(Integer, nullable=False, default=0)
    es_obligatoria = Column(Boolean, nullable=False, default=True)
    creado_en = Column(DateTime, nullable=True, default=datetime.utcnow)

    # Relaciones
    curso = relationship("CapCurso", back_populates="lecciones")
    progresos = relationship(
        "CapProgresoLeccion",
        back_populates="leccion",
        cascade="all, delete-orphan"
    )


# ============================================================================
# MODELOS DE INSCRIPCIONES Y PROGRESO
# ============================================================================

class CapInscripcion(MAIN):
    """
    Inscripción de un colaborador a un curso.
    
    Registra el estado, avance, puntaje y fechas importantes.
    """
    __tablename__ = "cap_inscripcion"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "colaborador_key", "curso_id",
            name="uq_cap_inscripcion_colab_curso_tenant"
        ),
        Index("ix_cap_inscripcion_tenant", "tenant_id"),
        Index("ix_cap_inscripcion_colaborador", "colaborador_key"),
        Index("ix_cap_inscripcion_estado", "estado"),
        Index("ix_cap_inscripcion_vencimiento", "fecha_vencimiento"),
    )

    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    id = Column(Integer, primary_key=True, index=True)
    colaborador_key = Column(String(100), nullable=False, index=True)
    colaborador_nombre = Column(String(200), nullable=True)
    departamento = Column(String(150), nullable=True)
    rol = Column(String(100), nullable=True, index=True)
    puesto = Column(String(150), nullable=True, index=True)
    curso_id = Column(
        Integer,
        ForeignKey("cap_curso.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    estado = Column(
        SAEnum(EstadoInscripcion),
        nullable=False,
        default=EstadoInscripcion.PENDIENTE,
        index=True
    )
    pct_avance = Column(Float, nullable=False, default=0.0)
    puntaje_final = Column(Float, nullable=True)
    aprobado = Column(Boolean, nullable=True)
    fecha_inscripcion = Column(DateTime, nullable=True, default=datetime.utcnow)
    fecha_inicio_real = Column(DateTime, nullable=True)
    fecha_completado = Column(DateTime, nullable=True)
    fecha_vencimiento = Column(DateTime, nullable=True, index=True)
    recordatorio_enviado_en = Column(DateTime, nullable=True)
    origen_regla = Column(String(120), nullable=True)
    creado_en = Column(DateTime, nullable=True, default=datetime.utcnow)
    actualizado_en = Column(
        DateTime,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relaciones
    curso = relationship("CapCurso", back_populates="inscripciones")
    progresos = relationship(
        "CapProgresoLeccion",
        back_populates="inscripcion",
        cascade="all, delete-orphan"
    )
    intentos = relationship(
        "CapIntentoEvaluacion",
        back_populates="inscripcion",
        cascade="all, delete-orphan"
    )
    certificado = relationship(
        "CapCertificado",
        back_populates="inscripcion",
        uselist=False,
        cascade="all, delete-orphan"
    )
    satisfaccion = relationship(
        "CapEncuestaSatisfaccion",
        back_populates="inscripcion",
        uselist=False,
        cascade="all, delete-orphan"
    )


class CapProgresoLeccion(MAIN):
    """
    Progreso de un colaborador en una lección específica.
    """
    __tablename__ = "cap_progreso_leccion"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "inscripcion_id", "leccion_id",
            name="uq_cap_progreso_insc_lecc_tenant"
        ),
        Index("ix_cap_progreso_tenant", "tenant_id"),
        Index("ix_cap_progreso_inscripcion", "inscripcion_id"),
    )

    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    id = Column(Integer, primary_key=True, index=True)
    inscripcion_id = Column(
        Integer,
        ForeignKey("cap_inscripcion.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    leccion_id = Column(
        Integer,
        ForeignKey("cap_leccion.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    completada = Column(Boolean, nullable=False, default=False)
    intentos = Column(Integer, nullable=False, default=0)
    tiempo_seg = Column(Integer, nullable=True)
    fecha_completado = Column(DateTime, nullable=True)

    # Relaciones
    inscripcion = relationship("CapInscripcion", back_populates="progresos")
    leccion = relationship("CapLeccion", back_populates="progresos")


# ============================================================================
# MODELOS DE EVALUACIONES
# ============================================================================

class CapEvaluacion(MAIN):
    """
    Evaluación asociada a un curso.
    """
    __tablename__ = "cap_evaluacion"
    __table_args__ = (
        Index("ix_cap_evaluacion_tenant", "tenant_id"),
        Index("ix_cap_evaluacion_curso", "curso_id"),
    )

    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    id = Column(Integer, primary_key=True, index=True)
    curso_id = Column(
        Integer,
        ForeignKey("cap_curso.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    titulo = Column(String(200), nullable=False)
    instrucciones = Column(Text, nullable=True)
    puntaje_minimo = Column(Float, nullable=False, default=70.0)
    max_intentos = Column(Integer, nullable=False, default=3)
    preguntas_por_intento = Column(Integer, nullable=True)
    tiempo_limite_min = Column(Integer, nullable=True)
    creado_por = Column(String(100), nullable=True, index=True)
    actualizado_por = Column(String(100), nullable=True, index=True)
    publicado_por = Column(String(100), nullable=True, index=True)
    publicado_en = Column(DateTime, nullable=True)
    creado_en = Column(DateTime, nullable=True, default=datetime.utcnow)
    actualizado_en = Column(DateTime, nullable=True, default=datetime.utcnow)

    # Relaciones
    curso = relationship("CapCurso", back_populates="evaluaciones")
    preguntas = relationship(
        "CapPregunta",
        back_populates="evaluacion",
        cascade="all, delete-orphan",
        order_by="CapPregunta.orden"
    )
    intentos = relationship(
        "CapIntentoEvaluacion",
        back_populates="evaluacion",
        cascade="all, delete-orphan"
    )


class CapPregunta(MAIN):
    """
    Pregunta dentro de una evaluación.
    """
    __tablename__ = "cap_pregunta"
    __table_args__ = (
        Index("ix_cap_pregunta_tenant", "tenant_id"),
        Index("ix_cap_pregunta_evaluacion", "evaluacion_id"),
    )

    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    id = Column(Integer, primary_key=True, index=True)
    evaluacion_id = Column(
        Integer,
        ForeignKey("cap_evaluacion.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    enunciado = Column(Text, nullable=False)
    tipo = Column(
        SAEnum(TipoPregunta),
        nullable=False,
        default=TipoPregunta.OPCION_MULTIPLE
    )
    explicacion = Column(Text, nullable=True)
    puntaje = Column(Float, nullable=False, default=1.0)
    orden = Column(Integer, nullable=False, default=0)

    # Relaciones
    evaluacion = relationship("CapEvaluacion", back_populates="preguntas")
    opciones = relationship(
        "CapOpcion",
        back_populates="pregunta",
        cascade="all, delete-orphan",
        order_by="CapOpcion.orden"
    )


class CapOpcion(MAIN):
    """
    Opción de respuesta para una pregunta.
    """
    __tablename__ = "cap_opcion"
    __table_args__ = (
        Index("ix_cap_opcion_tenant", "tenant_id"),
        Index("ix_cap_opcion_pregunta", "pregunta_id"),
    )

    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    id = Column(Integer, primary_key=True, index=True)
    pregunta_id = Column(
        Integer,
        ForeignKey("cap_pregunta.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    texto = Column(Text, nullable=False)
    es_correcta = Column(Boolean, nullable=False, default=False)
    orden = Column(Integer, nullable=False, default=0)

    # Relaciones
    pregunta = relationship("CapPregunta", back_populates="opciones")


class CapIntentoEvaluacion(MAIN):
    """
    Intento de un colaborador en una evaluación.
    """
    __tablename__ = "cap_intento_evaluacion"
    __table_args__ = (
        Index("ix_cap_intento_tenant", "tenant_id"),
        Index("ix_cap_intento_inscripcion", "inscripcion_id"),
        Index("ix_cap_intento_evaluacion", "evaluacion_id"),
    )

    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    id = Column(Integer, primary_key=True, index=True)
    inscripcion_id = Column(
        Integer,
        ForeignKey("cap_inscripcion.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    evaluacion_id = Column(
        Integer,
        ForeignKey("cap_evaluacion.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    numero_intento = Column(Integer, nullable=False, default=1)
    puntaje = Column(Float, nullable=True)
    puntaje_maximo = Column(Float, nullable=True)
    aprobado = Column(Boolean, nullable=True)
    respuestas_json = Column(Text, nullable=True)
    fecha_inicio = Column(DateTime, nullable=True)
    fecha_fin = Column(DateTime, nullable=True)

    # Relaciones
    inscripcion = relationship("CapInscripcion", back_populates="intentos")
    evaluacion = relationship("CapEvaluacion", back_populates="intentos")


# ============================================================================
# MODELOS DE CERTIFICADOS
# ============================================================================

class CapCertificado(MAIN):
    """
    Certificado emitido por completar un curso.
    """
    __tablename__ = "cap_certificado"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "inscripcion_id",
            name="uq_cap_cert_inscripcion_tenant"
        ),
        UniqueConstraint(
            "tenant_id", "folio",
            name="uq_cap_cert_folio_tenant"
        ),
        Index("ix_cap_certificado_tenant", "tenant_id"),
        Index("ix_cap_certificado_folio", "folio"),
    )

    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    id = Column(Integer, primary_key=True, index=True)
    inscripcion_id = Column(
        Integer,
        ForeignKey("cap_inscripcion.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    folio = Column(String(50), nullable=False, index=True)
    puntaje_final = Column(Float, nullable=True)
    creado_por = Column(String(100), nullable=True, index=True)
    fecha_emision = Column(DateTime, nullable=True, default=datetime.utcnow)
    url_pdf = Column(String(400), nullable=True)
    revocado = Column(Boolean, nullable=False, default=False)
    motivo_revocacion = Column(Text, nullable=True)
    fecha_revocacion = Column(DateTime, nullable=True)
    revocado_por = Column(String(100), nullable=True)
    actualizado_en = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    # Relaciones
    inscripcion = relationship("CapInscripcion", back_populates="certificado")


# ============================================================================
# MODELOS DE RUTAS DE APRENDIZAJE
# ============================================================================

class CapRutaAprendizaje(MAIN):
    """
    Ruta de aprendizaje: secuencia de cursos relacionados.
    """
    __tablename__ = "cap_ruta_aprendizaje"
    __table_args__ = (
        Index("ix_cap_ruta_tenant", "tenant_id"),
        Index("ix_cap_ruta_rol", "rol_objetivo"),
        Index("ix_cap_ruta_puesto", "puesto_objetivo"),
    )

    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    rol_objetivo = Column(String(100), nullable=True, index=True)
    puesto_objetivo = Column(String(150), nullable=True, index=True)
    departamentos_json = Column(Text, nullable=True)
    creada_en = Column(DateTime, nullable=True, default=datetime.utcnow)

    # Relaciones
    cursos = relationship(
        "CapRutaCurso",
        back_populates="ruta",
        cascade="all, delete-orphan",
        order_by="CapRutaCurso.orden"
    )


class CapRutaCurso(MAIN):
    """
    Relación entre ruta de aprendizaje y curso.
    """
    __tablename__ = "cap_ruta_curso"
    __table_args__ = (
        Index("ix_cap_ruta_curso_tenant", "tenant_id"),
        Index("ix_cap_ruta_curso_ruta", "ruta_id"),
    )

    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    id = Column(Integer, primary_key=True, index=True)
    ruta_id = Column(
        Integer,
        ForeignKey("cap_ruta_aprendizaje.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    curso_id = Column(
        Integer,
        ForeignKey("cap_curso.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    orden = Column(Integer, nullable=False, default=0)
    obligatorio = Column(Boolean, nullable=False, default=True)

    # Relaciones
    ruta = relationship("CapRutaAprendizaje", back_populates="cursos")




# ============================================================================
# MODELOS DE ENCUESTAS
# ============================================================================

class CapEncuestaSatisfaccion(MAIN):
    """
    Encuesta de satisfacción de un curso.
    """
    __tablename__ = "cap_encuesta_satisfaccion"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "inscripcion_id",
            name="uq_cap_satisfaccion_inscripcion_tenant"
        ),
        Index("ix_cap_satisfaccion_tenant", "tenant_id"),
    )

    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    id = Column(Integer, primary_key=True, index=True)
    inscripcion_id = Column(
        Integer,
        ForeignKey("cap_inscripcion.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    calificacion = Column(Integer, nullable=False, default=5)
    comentario = Column(Text, nullable=True)
    respondida_en = Column(DateTime, nullable=True, default=datetime.utcnow)

    # Relaciones
    inscripcion = relationship("CapInscripcion", back_populates="satisfaccion")


# ============================================================================
# MODELOS DE GAMIFICACIÓN
# ============================================================================

class CapPuntosLog(MAIN):
    """
    Registro de puntos otorgados a colaboradores.
    """
    __tablename__ = "cap_puntos_log"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "colaborador_key", "motivo",
            "referencia_tipo", "referencia_id",
            name="uq_cap_puntos_motivo_ref_tenant"
        ),
        Index("ix_cap_puntos_tenant", "tenant_id"),
        Index("ix_cap_puntos_colaborador", "colaborador_key"),
        Index("ix_cap_puntos_motivo", "motivo"),
    )

    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    id = Column(Integer, primary_key=True, index=True)
    colaborador_key = Column(String(100), nullable=False, index=True)
    puntos = Column(Integer, nullable=False, default=0)
    motivo = Column(String(100), nullable=False, index=True)
    referencia_tipo = Column(String(50), nullable=True)
    referencia_id = Column(Integer, nullable=True)
    fecha = Column(DateTime, nullable=True, default=datetime.utcnow)


class CapInsignia(MAIN):
    """
    Insignia/badge que se puede obtener.
    """
    __tablename__ = "cap_insignia"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "nombre",
            name="uq_cap_insignia_tenant_nombre"
        ),
        Index("ix_cap_insignia_tenant", "tenant_id"),
    )

    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=True)
    icono_emoji = Column(String(10), nullable=True)
    condicion_tipo = Column(String(50), nullable=False)
    condicion_valor = Column(Integer, nullable=False, default=1)
    color = Column(String(30), nullable=True)
    orden = Column(Integer, nullable=False, default=0)

    # Relaciones
    obtenidas = relationship(
        "CapColaboradorInsignia",
        back_populates="insignia",
        cascade="all, delete-orphan"
    )


class CapColaboradorInsignia(MAIN):
    """
    Insignia obtenida por un colaborador.
    """
    __tablename__ = "cap_colaborador_insignia"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "colaborador_key", "insignia_id",
            name="uq_cap_colab_insignia_tenant"
        ),
        Index("ix_cap_colab_insignia_tenant", "tenant_id"),
        Index("ix_cap_colab_insignia_colaborador", "colaborador_key"),
    )

    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    id = Column(Integer, primary_key=True, index=True)
    colaborador_key = Column(String(100), nullable=False, index=True)
    insignia_id = Column(
        Integer,
        ForeignKey("cap_insignia.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    fecha_obtencion = Column(DateTime, nullable=True, default=datetime.utcnow)

    # Relaciones
    insignia = relationship("CapInsignia", back_populates="obtenidas")


# ============================================================================
# MODELOS DE PRESENTACIONES INTERACTIVAS
# ============================================================================

class CapPresentacion(MAIN):
    """
    Presentación interactiva tipo Genially.
    """
    __tablename__ = "cap_presentacion"
    __table_args__ = (
        Index("ix_cap_presentacion_tenant", "tenant_id"),
        Index("ix_cap_presentacion_estado", "estado"),
        Index("ix_cap_presentacion_autor", "autor_key"),
    )

    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    autor_key = Column(String(100), nullable=True, index=True)
    template_key = Column(String(100), nullable=True, index=True)
    theme_key = Column(String(100), nullable=True, index=True)
    responsive_mode = Column(String(30), nullable=True, default="desktop")
    autosave_json = Column(Text, nullable=True)
    estado = Column(
        SAEnum(EstadoPresentacion),
        nullable=False,
        default=EstadoPresentacion.BORRADOR,
        index=True
    )
    curso_id = Column(
        Integer,
        ForeignKey("cap_curso.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    miniatura_url = Column(String(400), nullable=True)
    creado_por = Column(String(100), nullable=True, index=True)
    actualizado_por = Column(String(100), nullable=True, index=True)
    publicado_por = Column(String(100), nullable=True, index=True)
    publicado_en = Column(DateTime, nullable=True)
    creado_en = Column(DateTime, nullable=True, default=datetime.utcnow)
    actualizado_en = Column(
        DateTime,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relaciones
    diapositivas = relationship(
        "CapDiapositiva",
        back_populates="presentacion",
        cascade="all, delete-orphan",
        order_by="CapDiapositiva.orden"
    )
    versiones = relationship(
        "CapPresentacionVersion",
        back_populates="presentacion",
        cascade="all, delete-orphan",
        order_by="CapPresentacionVersion.creado_en"
    )
    assets = relationship(
        "CapAssetBiblioteca",
        back_populates="presentacion",
        cascade="all, delete-orphan"
    )


class CapDiapositiva(MAIN):
    """
    Diapositiva dentro de una presentación.
    """
    __tablename__ = "cap_diapositiva"
    __table_args__ = (
        Index("ix_cap_diap_tenant", "tenant_id"),
        Index("ix_cap_diap_pres_orden", "presentacion_id", "orden"),
    )

    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    id = Column(Integer, primary_key=True, index=True)
    presentacion_id = Column(
        Integer,
        ForeignKey("cap_presentacion.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    orden = Column(Integer, nullable=False, default=0)
    titulo = Column(String(200), nullable=True)
    layout_key = Column(String(100), nullable=True, index=True)
    transition_key = Column(String(100), nullable=True)
    animation_json = Column(Text, nullable=True)
    responsive_json = Column(Text, nullable=True)
    bg_color = Column(String(30), nullable=True, default="#ffffff")
    bg_image_url = Column(String(400), nullable=True)
    notas = Column(Text, nullable=True)
    creado_en = Column(DateTime, nullable=True, default=datetime.utcnow)

    # Relaciones
    presentacion = relationship("CapPresentacion", back_populates="diapositivas")
    elementos = relationship(
        "CapElemento",
        back_populates="diapositiva",
        cascade="all, delete-orphan",
        order_by="CapElemento.z_index"
    )


class CapElemento(MAIN):
    """
    Elemento interactivo dentro de una diapositiva.
    """
    __tablename__ = "cap_elemento"
    __table_args__ = (
        Index("ix_cap_elemento_tenant", "tenant_id"),
        Index("ix_cap_elemento_diapositiva", "diapositiva_id"),
    )

    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    id = Column(Integer, primary_key=True, index=True)
    diapositiva_id = Column(
        Integer,
        ForeignKey("cap_diapositiva.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    tipo = Column(String(30), nullable=False)
    contenido_json = Column(Text, nullable=True)
    asset_id = Column(
        Integer,
        ForeignKey("cap_asset_biblioteca.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    animation_json = Column(Text, nullable=True)
    hotspot_key = Column(String(100), nullable=True, index=True)
    pos_x = Column(Float, nullable=False, default=10.0)
    pos_y = Column(Float, nullable=False, default=10.0)
    width = Column(Float, nullable=False, default=30.0)
    height = Column(Float, nullable=False, default=20.0)
    z_index = Column(Integer, nullable=False, default=1)
    creado_en = Column(DateTime, nullable=True, default=datetime.utcnow)

    # Relaciones
    diapositiva = relationship("CapDiapositiva", back_populates="elementos")
    asset = relationship("CapAssetBiblioteca", back_populates="elementos")


class CapPresentacionVersion(MAIN):
    """
    Versión/snapshot de una presentación.
    """
    __tablename__ = "cap_presentacion_version"
    __table_args__ = (
        Index("ix_cap_pres_version_tenant", "tenant_id"),
        Index("ix_cap_pres_version_presentacion", "presentacion_id"),
        Index("ix_cap_pres_version_fecha", "creado_en"),
    )

    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    id = Column(Integer, primary_key=True, index=True)
    presentacion_id = Column(
        Integer,
        ForeignKey("cap_presentacion.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    tipo = Column(String(30), nullable=False, default="snapshot", index=True)
    etiqueta = Column(String(120), nullable=True)
    contenido_json = Column(Text, nullable=True)
    actor_key = Column(String(100), nullable=True, index=True)
    creado_en = Column(DateTime, nullable=True, default=datetime.utcnow, index=True)

    # Relaciones
    presentacion = relationship("CapPresentacion", back_populates="versiones")


class CapAssetBiblioteca(MAIN):
    """
    Asset (imagen, video, etc.) en la biblioteca.
    """
    __tablename__ = "cap_asset_biblioteca"
    __table_args__ = (
        Index("ix_cap_asset_tenant", "tenant_id"),
        Index("ix_cap_asset_tipo", "tipo"),
    )

    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    id = Column(Integer, primary_key=True, index=True)
    presentacion_id = Column(
        Integer,
        ForeignKey("cap_presentacion.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    nombre = Column(String(200), nullable=False)
    tipo = Column(String(50), nullable=False, default="imagen", index=True)
    url = Column(String(500), nullable=False)
    thumb_url = Column(String(500), nullable=True)
    tags_json = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
    creado_por = Column(String(100), nullable=True, index=True)
    creado_en = Column(DateTime, nullable=True, default=datetime.utcnow)

    # Relaciones
    presentacion = relationship("CapPresentacion", back_populates="assets")
    elementos = relationship("CapElemento", back_populates="asset")


# ============================================================================
# MODELOS DE ARCHIVOS Y AUDITORÍA
# ============================================================================

class CapArchivo(MAIN):
    """
    Archivo subido al sistema.
    """
    __tablename__ = "cap_archivo"
    __table_args__ = (
        Index("ix_cap_archivo_tenant", "tenant_id"),
        Index("ix_cap_archivo_entidad", "entidad_tipo", "entidad_id"),
        Index("ix_cap_archivo_categoria", "categoria"),
    )

    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    id = Column(Integer, primary_key=True, index=True)
    entidad_tipo = Column(String(50), nullable=True, index=True)
    entidad_id = Column(Integer, nullable=True, index=True)
    categoria = Column(String(50), nullable=False, index=True)
    nombre_original = Column(String(255), nullable=False)
    nombre_archivo = Column(String(255), nullable=False, index=True)
    ruta_relativa = Column(String(500), nullable=False)
    public_url = Column(String(500), nullable=False)
    mime_type = Column(String(120), nullable=True)
    size_bytes = Column(Integer, nullable=True)
    creado_por = Column(String(100), nullable=True, index=True)
    metadata_json = Column(Text, nullable=True)
    creado_en = Column(DateTime, nullable=True, default=datetime.utcnow, index=True)


class CapEventoEntidad(MAIN):
    """
    Evento de auditoría para entidades.
    """
    __tablename__ = "cap_evento_entidad"
    __table_args__ = (
        Index(
            "ix_cap_evento_entidad_lookup",
            "tenant_id", "entidad_tipo", "entidad_id", "creado_en"
        ),
        Index("ix_cap_evento_tenant", "tenant_id"),
        Index("ix_cap_evento_tipo", "entidad_tipo"),
        Index("ix_cap_evento_accion", "accion"),
    )

    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    id = Column(Integer, primary_key=True, index=True)
    entidad_tipo = Column(String(50), nullable=False, index=True)
    entidad_id = Column(Integer, nullable=False, index=True)
    accion = Column(String(50), nullable=False, index=True)
    actor_key = Column(String(100), nullable=True, index=True)
    actor_nombre = Column(String(200), nullable=True)
    detalle_json = Column(Text, nullable=True)
    creado_en = Column(DateTime, nullable=True, default=datetime.utcnow, index=True)


# ============================================================================
# FUNCIÓN DE INICIALIZACIÓN DEL ESQUEMA
# ============================================================================

def ensure_capacitacion_tenant_schema(host: str = None) -> None:
    """
    Asegura que el esquema de capacitación esté creado y actualizado.
    
    Crea todas las tablas y añade columnas faltantes en instalaciones antiguas.
    
    Args:
        host: Host de la base de datos (opcional)
    """
    engine = get_engine(host)
    
    # Crear todas las tablas
    MAIN.metadata.create_all(bind=engine, checkfirst=True)
    
    # Statements para añadir columnas que podrían faltar en instalaciones antiguas
    alter_statements = [
        "ALTER TABLE cap_categoria ADD COLUMN tenant_id VARCHAR(100) NOT NULL DEFAULT 'default'",
        "ALTER TABLE cap_curso ADD COLUMN tenant_id VARCHAR(100) NOT NULL DEFAULT 'default'",
        "ALTER TABLE cap_leccion ADD COLUMN tenant_id VARCHAR(100) NOT NULL DEFAULT 'default'",
        "ALTER TABLE cap_inscripcion ADD COLUMN tenant_id VARCHAR(100) NOT NULL DEFAULT 'default'",
        "ALTER TABLE cap_progreso_leccion ADD COLUMN tenant_id VARCHAR(100) NOT NULL DEFAULT 'default'",
        "ALTER TABLE cap_evaluacion ADD COLUMN tenant_id VARCHAR(100) NOT NULL DEFAULT 'default'",
        "ALTER TABLE cap_pregunta ADD COLUMN tenant_id VARCHAR(100) NOT NULL DEFAULT 'default'",
        "ALTER TABLE cap_opcion ADD COLUMN tenant_id VARCHAR(100) NOT NULL DEFAULT 'default'",
        "ALTER TABLE cap_intento_evaluacion ADD COLUMN tenant_id VARCHAR(100) NOT NULL DEFAULT 'default'",
        "ALTER TABLE cap_certificado ADD COLUMN tenant_id VARCHAR(100) NOT NULL DEFAULT 'default'",
        "ALTER TABLE cap_certificado ADD COLUMN revocado BOOLEAN NOT NULL DEFAULT 0",
        "ALTER TABLE cap_certificado ADD COLUMN motivo_revocacion TEXT",
        "ALTER TABLE cap_certificado ADD COLUMN fecha_revocacion TIMESTAMP",
        "ALTER TABLE cap_certificado ADD COLUMN revocado_por VARCHAR(100)",
        "ALTER TABLE cap_certificado ADD COLUMN actualizado_en TIMESTAMP",
        "ALTER TABLE cap_curso ADD COLUMN vence_dias INTEGER",
        "ALTER TABLE cap_curso ADD COLUMN recordatorio_dias INTEGER DEFAULT 7",
        "ALTER TABLE cap_curso ADD COLUMN reinscripcion_automatica BOOLEAN NOT NULL DEFAULT 0",
        "ALTER TABLE cap_evaluacion ADD COLUMN actualizado_en TIMESTAMP",
    ]
    
    # Ejecutar alteraciones
    with engine.begin() as conn:
        for stmt in alter_statements:
            try:
                conn.execute(text(stmt))
            except Exception:
                # La columna ya existe o no se puede añadir
                pass
            
