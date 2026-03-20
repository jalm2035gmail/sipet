from typing import Optional, List, Dict, Any
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import func, case, or_, and_

from fastapi_modulo.modulos.capacitacion.repositorios.common import get_db
from fastapi_modulo.modulos.capacitacion.modelos.db_models import (
    CapCertificado,
    CapCurso,
    CapEncuestaSatisfaccion,
    CapInscripcion,
    CapLeccion,
    CapProgresoLeccion
)


def list_inscripciones(
    db: Session,
    curso_id: Optional[int] = None,
    colaborador_key: Optional[str] = None,
    estado: Optional[str] = None,
    departamento: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None
) -> List[CapInscripcion]:
    """
    Lista inscripciones con filtros opcionales.
    
    Args:
        db: Sesión de base de datos
        curso_id: ID del curso
        colaborador_key: Identificador del colaborador
        estado: Estado de la inscripción
        departamento: Departamento del colaborador
        fecha_desde: Fecha inicial del filtro
        fecha_hasta: Fecha final del filtro
        
    Returns:
        Lista de inscripciones ordenadas por ID descendente
    """
    query = db.query(CapInscripcion)
    
    if curso_id:
        query = query.filter(CapInscripcion.curso_id == curso_id)
    if colaborador_key:
        query = query.filter(CapInscripcion.colaborador_key == colaborador_key)
    if estado:
        query = query.filter(CapInscripcion.estado == estado)
    if departamento:
        query = query.filter(CapInscripcion.departamento == departamento)
    if fecha_desde:
        query = query.filter(CapInscripcion.fecha_inscripcion >= fecha_desde)
    if fecha_hasta:
        # Incluir todo el día hasta las 23:59:59
        query = query.filter(CapInscripcion.fecha_inscripcion <= f"{fecha_hasta}T23:59:59")
    
    return query.order_by(CapInscripcion.id.desc()).all()


def get_inscripcion(db: Session, insc_id: int) -> Optional[CapInscripcion]:
    """
    Obtiene una inscripción por ID.
    
    Args:
        db: Sesión de base de datos
        insc_id: ID de la inscripción
        
    Returns:
        Inscripción encontrada o None
    """
    return db.query(CapInscripcion).filter(CapInscripcion.id == insc_id).first()


def get_existing_inscripcion(
    db: Session,
    colaborador_key: str,
    curso_id: int
) -> Optional[CapInscripcion]:
    """
    Verifica si ya existe una inscripción para un colaborador en un curso.
    
    Args:
        db: Sesión de base de datos
        colaborador_key: Identificador del colaborador
        curso_id: ID del curso
        
    Returns:
        Inscripción existente o None
    """
    return db.query(CapInscripcion).filter(
        CapInscripcion.colaborador_key == colaborador_key,
        CapInscripcion.curso_id == curso_id
    ).first()


def create_inscripcion(db: Session, data: Dict[str, Any]) -> CapInscripcion:
    """
    Crea una nueva inscripción.
    
    Args:
        db: Sesión de base de datos
        data: Diccionario con los datos de la inscripción
        
    Returns:
        Inscripción creada
    """
    obj = CapInscripcion(**data)
    db.add(obj)
    db.flush()
    return obj


def list_inscripciones_activas_por_curso(db: Session, curso_id: int) -> List[CapInscripcion]:
    """
    Lista todas las inscripciones activas de un curso.
    
    Args:
        db: Sesión de base de datos
        curso_id: ID del curso
        
    Returns:
        Lista de inscripciones activas
    """
    estados_activos = ["pendiente", "en_progreso", "completado"]
    return db.query(CapInscripcion).filter(
        CapInscripcion.curso_id == curso_id,
        CapInscripcion.estado.in_(estados_activos)
    ).all()


def list_inscripciones_vencibles(db: Session, now: datetime) -> List[CapInscripcion]:
    """
    Lista inscripciones de cursos obligatorios que están vencidas.
    
    Args:
        db: Sesión de base de datos
        now: Fecha/hora actual
        
    Returns:
        Lista de inscripciones vencidas
    """
    return (
        db.query(CapInscripcion)
        .join(CapCurso, CapInscripcion.curso_id == CapCurso.id)
        .filter(
            CapCurso.es_obligatorio == True,
            CapInscripcion.fecha_vencimiento != None,
            CapInscripcion.fecha_vencimiento <= now
        )
        .all()
    )


def list_recordatorios_pendientes(db: Session, now: datetime) -> List[CapInscripcion]:
    """
    Lista inscripciones que requieren envío de recordatorio.
    
    Args:
        db: Sesión de base de datos
        now: Fecha/hora actual
        
    Returns:
        Lista de inscripciones que necesitan recordatorio
    """
    return (
        db.query(CapInscripcion)
        .join(CapCurso, CapInscripcion.curso_id == CapCurso.id)
        .filter(
            CapCurso.es_obligatorio == True,
            CapInscripcion.fecha_vencimiento != None,
            CapInscripcion.fecha_vencimiento > now,
            CapCurso.recordatorio_dias != None,
            or_(
                CapInscripcion.recordatorio_enviado_en == None,
                CapInscripcion.recordatorio_enviado_en < CapInscripcion.fecha_vencimiento
            )
        )
        .all()
    )


def get_satisfaccion(db: Session, inscripcion_id: int) -> Optional[CapEncuestaSatisfaccion]:
    """
    Obtiene la encuesta de satisfacción de una inscripción.
    
    Args:
        db: Sesión de base de datos
        inscripcion_id: ID de la inscripción
        
    Returns:
        Encuesta de satisfacción o None
    """
    return db.query(CapEncuestaSatisfaccion).filter(
        CapEncuestaSatisfaccion.inscripcion_id == inscripcion_id
    ).first()


def create_satisfaccion(db: Session, data: Dict[str, Any]) -> CapEncuestaSatisfaccion:
    """
    Crea una encuesta de satisfacción.
    
    Args:
        db: Sesión de base de datos
        data: Diccionario con los datos de la encuesta
        
    Returns:
        Encuesta de satisfacción creada
    """
    obj = CapEncuestaSatisfaccion(**data)
    db.add(obj)
    db.flush()
    return obj


def get_leccion(db: Session, leccion_id: int) -> Optional[CapLeccion]:
    """
    Obtiene una lección por ID.
    
    Args:
        db: Sesión de base de datos
        leccion_id: ID de la lección
        
    Returns:
        Lección encontrada o None
    """
    return db.query(CapLeccion).filter(CapLeccion.id == leccion_id).first()


def get_progreso(
    db: Session,
    inscripcion_id: int,
    leccion_id: int
) -> Optional[CapProgresoLeccion]:
    """
    Obtiene el progreso de una lección específica en una inscripción.
    
    Args:
        db: Sesión de base de datos
        inscripcion_id: ID de la inscripción
        leccion_id: ID de la lección
        
    Returns:
        Progreso de la lección o None
    """
    return db.query(CapProgresoLeccion).filter(
        CapProgresoLeccion.inscripcion_id == inscripcion_id,
        CapProgresoLeccion.leccion_id == leccion_id
    ).first()


def create_progreso(db: Session, data: Dict[str, Any]) -> CapProgresoLeccion:
    """
    Crea un registro de progreso de lección.
    
    Args:
        db: Sesión de base de datos
        data: Diccionario con los datos del progreso
        
    Returns:
        Progreso de lección creado
    """
    obj = CapProgresoLeccion(**data)
    db.add(obj)
    db.flush()
    return obj


def list_progreso_curso(db: Session, inscripcion_id: int) -> List[CapProgresoLeccion]:
    """
    Lista todo el progreso de lecciones de una inscripción.
    
    Args:
        db: Sesión de base de datos
        inscripcion_id: ID de la inscripción
        
    Returns:
        Lista de progreso de lecciones
    """
    return db.query(CapProgresoLeccion).filter(
        CapProgresoLeccion.inscripcion_id == inscripcion_id
    ).all()


def count_lecciones_obligatorias(db: Session, curso_id: int) -> int:
    """
    Cuenta las lecciones obligatorias de un curso.
    
    Args:
        db: Sesión de base de datos
        curso_id: ID del curso
        
    Returns:
        Número de lecciones obligatorias
    """
    return db.query(CapLeccion).filter(
        CapLeccion.curso_id == curso_id,
        CapLeccion.es_obligatoria == True
    ).count()


def count_lecciones_obligatorias_completadas(db: Session, inscripcion_id: int) -> int:
    """
    Cuenta las lecciones obligatorias completadas en una inscripción.
    
    Args:
        db: Sesión de base de datos
        inscripcion_id: ID de la inscripción
        
    Returns:
        Número de lecciones obligatorias completadas
    """
    return (
        db.query(CapProgresoLeccion)
        .join(CapLeccion, CapProgresoLeccion.leccion_id == CapLeccion.id)
        .filter(
            CapProgresoLeccion.inscripcion_id == inscripcion_id,
            CapProgresoLeccion.completada == True,
            CapLeccion.es_obligatoria == True
        )
        .count()
    )


def dashboard_counts(db: Session) -> Dict[str, Any]:
    """
    Obtiene métricas y estadísticas del dashboard de capacitación.
    
    Args:
        db: Sesión de base de datos
        
    Returns:
        Diccionario con todas las métricas del dashboard
    """
    # Calcular promedio de días para finalización
    promedio_finalizacion = db.query(
        func.avg(
            func.julianday(CapInscripcion.fecha_completado) - 
            func.julianday(CapInscripcion.fecha_inscripcion)
        )
    ).filter(
        CapInscripcion.estado == "completado",
        CapInscripcion.fecha_completado != None,
        CapInscripcion.fecha_inscripcion != None
    ).scalar()
    
    return {
        # Conteos básicos
        "total_inscs": db.query(CapInscripcion).count(),
        "completadas": db.query(CapInscripcion).filter(
            CapInscripcion.estado == "completado"
        ).count(),
        "en_progreso": db.query(CapInscripcion).filter(
            CapInscripcion.estado == "en_progreso"
        ).count(),
        "reprobadas": db.query(CapInscripcion).filter(
            CapInscripcion.estado == "reprobado"
        ).count(),
        "pendientes": db.query(CapInscripcion).filter(
            CapInscripcion.estado == "pendiente"
        ).count(),
        
        # Estadísticas de cursos
        "cursos_publicados": db.query(CapCurso).filter(
            CapCurso.estado == "publicado"
        ).count(),
        "cursos_archivados": db.query(CapCurso).filter(
            CapCurso.estado == "archivado"
        ).count(),
        
        # Certificados y colaboradores
        "certificados": db.query(CapCertificado).count(),
        "colaboradores_unicos": db.query(
            func.count(func.distinct(CapInscripcion.colaborador_key))
        ).scalar() or 0,
        
        # Promedio de finalización
        "promedio_finalizacion_dias": round(float(promedio_finalizacion or 0.0), 1),
        
        # Top 5 cursos más completados
        "top_completados": (
            db.query(
                CapInscripcion.curso_id,
                CapCurso.nombre,
                func.count(CapInscripcion.id).label("total")
            )
            .join(CapCurso, CapInscripcion.curso_id == CapCurso.id)
            .filter(CapInscripcion.estado == "completado")
            .group_by(CapInscripcion.curso_id, CapCurso.nombre)
            .order_by(func.count(CapInscripcion.id).desc())
            .limit(5)
            .all()
        ),
        
        # Top 5 cursos con más abandonos
        "top_abandonados": (
            db.query(
                CapInscripcion.curso_id,
                CapCurso.nombre,
                func.count(CapInscripcion.id).label("total")
            )
            .join(CapCurso, CapInscripcion.curso_id == CapCurso.id)
            .filter(CapInscripcion.estado.in_(["pendiente", "en_progreso"]))
            .group_by(CapInscripcion.curso_id, CapCurso.nombre)
            .order_by(func.count(CapInscripcion.id).desc())
            .limit(5)
            .all()
        ),
        
        # Cursos sin avance (últimos 10)
        "cursos_sin_avance": (
            db.query(
                CapInscripcion.colaborador_key,
                CapInscripcion.colaborador_nombre,
                CapCurso.nombre,
                CapInscripcion.departamento
            )
            .join(CapCurso, CapInscripcion.curso_id == CapCurso.id)
            .filter(CapInscripcion.pct_avance <= 0.0)
            .order_by(CapInscripcion.fecha_inscripcion.desc())
            .limit(10)
            .all()
        ),
        
        # Cursos con baja tasa de aprobación
        "aprobacion_baja": (
            db.query(
                CapCurso.id,
                CapCurso.nombre,
                func.count(CapInscripcion.id).label("total"),
                func.sum(case((CapInscripcion.aprobado == True, 1), else_=0)).label("aprobados")
            )
            .join(CapInscripcion, CapInscripcion.curso_id == CapCurso.id)
            .group_by(CapCurso.id, CapCurso.nombre)
            .having(func.count(CapInscripcion.id) > 0)
            .order_by(
                (func.sum(case((CapInscripcion.aprobado == True, 1), else_=0)) * 1.0 / 
                 func.count(CapInscripcion.id)).asc()
            )
            .limit(5)
            .all()
        ),
        
        # Inscripciones por curso (top 8)
        "inscripcion_por_curso": (
            db.query(
                CapCurso.id,
                CapCurso.nombre,
                func.count(CapInscripcion.id).label("total")
            )
            .outerjoin(CapInscripcion, CapInscripcion.curso_id == CapCurso.id)
            .group_by(CapCurso.id, CapCurso.nombre)
            .order_by(func.count(CapInscripcion.id).desc())
            .limit(8)
            .all()
        ),
        
        # Distribución de estados
        "estados_dist": db.query(
            CapInscripcion.estado,
            func.count(CapInscripcion.id).label("n")
        ).group_by(CapInscripcion.estado).all(),
        
        # Distribución por departamento (top 10)
        "dept_dist": (
            db.query(
                CapInscripcion.departamento,
                func.count(CapInscripcion.id).label("n")
            )
            .filter(CapInscripcion.departamento != None)
            .group_by(CapInscripcion.departamento)
            .order_by(func.count(CapInscripcion.id).desc())
            .limit(10)
            .all()
        ),
        
        # Avance promedio por departamento (top 10)
        "dept_avance": (
            db.query(
                CapInscripcion.departamento,
                func.avg(CapInscripcion.pct_avance).label("avance")
            )
            .filter(CapInscripcion.departamento != None)
            .group_by(CapInscripcion.departamento)
            .order_by(func.avg(CapInscripcion.pct_avance).desc())
            .limit(10)
            .all()
        ),
        
        # Certificados emitidos por periodo (últimos 8)
        "certificados_periodo": (
            db.query(
                func.date(CapCertificado.fecha_emision).label("periodo"),
                func.count(CapCertificado.id).label("total")
            )
            .filter(CapCertificado.fecha_emision != None)
            .group_by(func.date(CapCertificado.fecha_emision))
            .order_by(func.date(CapCertificado.fecha_emision).desc())
            .limit(8)
            .all()
        ),
        
        # Cursos obligatorios vencidos no completados
        "obligatorios_vencidos": (
            db.query(
                CapCurso.id,
                CapCurso.nombre,
                func.count(CapInscripcion.id).label("total")
            )
            .join(CapInscripcion, CapInscripcion.curso_id == CapCurso.id)
            .filter(
                CapCurso.es_obligatorio == True,
                CapCurso.fecha_fin != None,
                CapCurso.fecha_fin < func.current_date(),
                CapInscripcion.estado != "completado"
            )
            .group_by(CapCurso.id, CapCurso.nombre)
            .order_by(func.count(CapInscripcion.id).desc())
            .all()
        ),
    }

    