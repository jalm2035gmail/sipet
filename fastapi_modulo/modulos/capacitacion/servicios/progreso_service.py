from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from fastapi_modulo.modulos.capacitacion.modelos.db_models import (
    CapCurso,
    CapInscripcion,
    CapLeccion,
    CapProgresoLeccion,
    CapEncuestaSatisfaccion
)
from fastapi_modulo.modulos.capacitacion.controladores.dependencies import load_colab_meta
from fastapi_modulo.modulos.capacitacion.repositorios import inscripciones_repository as repo
from fastapi_modulo.modulos.capacitacion.repositorios import cursos_repository as cursos_repo


# ============================================================================
# FUNCIONES AUXILIARES DE SERIALIZACIÓN
# ============================================================================

def _dt(value: Optional[datetime]) -> Optional[str]:
    """
    Convierte un datetime a formato ISO string.
    
    Args:
        value: Objeto datetime o None
        
    Returns:
        String ISO 8601 o None
    """
    if value is None:
        return None
    return value.isoformat() if isinstance(value, datetime) else str(value)


def _loads_list(value: Optional[str]) -> List[Any]:
    """
    Deserializa un JSON string a lista.
    
    Args:
        value: String JSON o None
        
    Returns:
        Lista deserializada o lista vacía
    """
    if not value:
        return []
    if isinstance(value, list):
        return value
    try:
        data = json.loads(value)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


# ============================================================================
# FUNCIONES DE SERIALIZACIÓN DE MODELOS
# ============================================================================

def _insc_dict(obj: CapInscripcion) -> Dict[str, Any]:
    """
    Convierte un objeto CapInscripcion a diccionario.
    
    Args:
        obj: Objeto CapInscripcion
        
    Returns:
        Diccionario con datos de la inscripción
    """
    return {
        "id": obj.id,
        "colaborador_key": obj.colaborador_key,
        "colaborador_nombre": obj.colaborador_nombre,
        "departamento": obj.departamento,
        "rol": getattr(obj, "rol", None),
        "puesto": getattr(obj, "puesto", None),
        "curso_id": obj.curso_id,
        "curso_nombre": obj.curso.nombre if obj.curso else None,
        "estado": obj.estado,
        "pct_avance": obj.pct_avance,
        "puntaje_final": obj.puntaje_final,
        "aprobado": obj.aprobado,
        "fecha_inscripcion": _dt(obj.fecha_inscripcion),
        "fecha_inicio_real": _dt(obj.fecha_inicio_real),
        "fecha_completado": _dt(obj.fecha_completado),
        "fecha_vencimiento": _dt(getattr(obj, "fecha_vencimiento", None)),
        "recordatorio_enviado_en": _dt(getattr(obj, "recordatorio_enviado_en", None)),
        "origen_regla": getattr(obj, "origen_regla", None),
        "encuesta_satisfaccion_completa": bool(getattr(obj, "satisfaccion", None)),
    }


def _progreso_dict(obj: CapProgresoLeccion) -> Dict[str, Any]:
    """
    Convierte un objeto CapProgresoLeccion a diccionario.
    
    Args:
        obj: Objeto CapProgresoLeccion
        
    Returns:
        Diccionario con datos del progreso
    """
    return {
        "id": obj.id,
        "inscripcion_id": obj.inscripcion_id,
        "leccion_id": obj.leccion_id,
        "completada": obj.completada,
        "intentos": obj.intentos,
        "tiempo_seg": obj.tiempo_seg,
        "fecha_completado": _dt(obj.fecha_completado),
    }


# ============================================================================
# FUNCIONES AUXILIARES DE LÓGICA DE NEGOCIO
# ============================================================================

def _recalcular_avance(db: Session, insc: CapInscripcion) -> None:
    """
    Recalcula el porcentaje de avance de una inscripción.
    
    Args:
        db: Sesión de base de datos
        insc: Objeto CapInscripcion a recalcular
    """
    lecciones_obl = repo.count_lecciones_obligatorias(db, insc.curso_id)
    
    if lecciones_obl == 0:
        insc.pct_avance = 100.0
    else:
        completadas = repo.count_lecciones_obligatorias_completadas(db, insc.id)
        insc.pct_avance = round((completadas / lecciones_obl) * 100, 2)
    
    # Actualizar estado si hay progreso
    if insc.estado == "pendiente" and insc.pct_avance > 0:
        insc.estado = "en_progreso"
        insc.fecha_inicio_real = insc.fecha_inicio_real or datetime.utcnow()
    
    insc.actualizado_en = datetime.utcnow()


def _fecha_vencimiento(curso: CapCurso, base_dt: datetime) -> Optional[datetime]:
    """
    Calcula la fecha de vencimiento de una inscripción.
    
    Args:
        curso: Objeto CapCurso
        base_dt: Fecha base para el cálculo
        
    Returns:
        Fecha de vencimiento o None
    """
    if getattr(curso, "vence_dias", None):
        return base_dt + timedelta(days=int(curso.vence_dias))
    
    if getattr(curso, "fecha_fin", None):
        return datetime.combine(curso.fecha_fin, datetime.min.time())
    
    return None


def _course_rules_match(curso: CapCurso, payload: Dict[str, Any]) -> bool:
    """
    Verifica si un colaborador cumple las reglas de segmentación del curso.
    
    Args:
        curso: Objeto CapCurso
        payload: Datos del colaborador
        
    Returns:
        True si cumple las reglas, False en caso contrario
    """
    # Validar departamentos
    departamentos = [
        str(item).strip().lower() 
        for item in _loads_list(getattr(curso, "departamentos_json", None)) 
        if str(item).strip()
    ]
    
    if departamentos:
        colab_dept = str(payload.get("departamento", "")).strip().lower()
        if colab_dept not in departamentos:
            return False
    
    # Validar rol objetivo
    if getattr(curso, "rol_objetivo", None):
        curso_rol = str(curso.rol_objetivo).strip().lower()
        colab_rol = str(payload.get("rol", "")).strip().lower()
        if colab_rol != curso_rol:
            return False
    
    # Validar puesto objetivo
    if getattr(curso, "puesto_objetivo", None):
        curso_puesto = str(curso.puesto_objetivo).strip().lower()
        colab_puesto = str(payload.get("puesto", "")).strip().lower()
        if colab_puesto != curso_puesto:
            return False
    
    return True


def _prerequisitos_cumplidos(
    db: Session,
    colaborador_key: str,
    curso: CapCurso
) -> Tuple[bool, List[int]]:
    """
    Verifica si un colaborador cumple los prerrequisitos de un curso.
    
    Args:
        db: Sesión de base de datos
        colaborador_key: Identificador del colaborador
        curso: Objeto CapCurso
        
    Returns:
        Tupla (cumple_requisitos, lista_de_cursos_faltantes)
    """
    prereqs = _loads_list(getattr(curso, "prerrequisitos_json", None))
    
    if not prereqs:
        return True, []
    
    # Obtener cursos completados por el colaborador
    completados_rows = cursos_repo.list_cursos_completados_por_colaborador(
        db, 
        colaborador_key
    )
    completados = {row[0] for row in completados_rows}
    
    # Identificar prerrequisitos faltantes
    faltantes = [curso_id for curso_id in prereqs if curso_id not in completados]
    
    return not faltantes, faltantes


# ============================================================================
# SERVICIOS DE INSCRIPCIONES
# ============================================================================

def list_inscripciones(
    curso_id: Optional[int] = None,
    colaborador_key: Optional[str] = None,
    estado: Optional[str] = None,
    departamento: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Lista inscripciones con filtros opcionales.
    
    Args:
        curso_id: ID del curso
        colaborador_key: Identificador del colaborador
        estado: Estado de la inscripción
        departamento: Departamento del colaborador
        fecha_desde: Fecha inicial del filtro
        fecha_hasta: Fecha final del filtro
        
    Returns:
        Lista de inscripciones como diccionarios
    """
    db = repo.get_db()
    try:
        inscripciones = repo.list_inscripciones(
            db, 
            curso_id, 
            colaborador_key, 
            estado, 
            departamento, 
            fecha_desde, 
            fecha_hasta
        )
        return [_insc_dict(item) for item in inscripciones]
    finally:
        db.close()


def get_inscripcion(insc_id: int) -> Optional[Dict[str, Any]]:
    """
    Obtiene una inscripción por ID.
    
    Args:
        insc_id: ID de la inscripción
        
    Returns:
        Diccionario con datos de la inscripción o None
    """
    db = repo.get_db()
    try:
        obj = repo.get_inscripcion(db, insc_id)
        return _insc_dict(obj) if obj else None
    finally:
        db.close()


def inscribir_colaborador(data: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    """
    Inscribe un colaborador a un curso.
    
    Args:
        data: Datos de la inscripción incluyendo curso_id y colaborador_key
        
    Returns:
        Tupla (inscripcion_dict, fue_creada)
        
    Raises:
        ValueError: Si el curso no existe, no cumple reglas o faltan prerrequisitos
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        # Validar que el curso existe
        curso = cursos_repo.get_curso(db, data["curso_id"])
        if not curso:
            raise ValueError("Curso no encontrado")
        
        # Validar reglas de segmentación
        if not _course_rules_match(curso, data):
            raise ValueError("El colaborador no cumple la segmentación del curso")
        
        # Validar prerrequisitos
        prereqs_ok, faltantes = _prerequisitos_cumplidos(
            db, 
            data["colaborador_key"], 
            curso
        )
        if not prereqs_ok:
            raise ValueError(
                f"Faltan prerrequisitos para inscribirse. Cursos faltantes: {faltantes}"
            )
        
        # Verificar si ya existe inscripción
        existing = repo.get_existing_inscripcion(
            db, 
            data["colaborador_key"], 
            data["curso_id"]
        )
        if existing:
            return _insc_dict(existing), False
        
        # Crear nueva inscripción
        payload = dict(data)
        payload["fecha_vencimiento"] = _fecha_vencimiento(curso, datetime.utcnow())
        payload.setdefault("estado", "pendiente")
        payload.setdefault("pct_avance", 0.0)
        payload.setdefault("fecha_inscripcion", datetime.utcnow())
        
        obj = repo.create_inscripcion(db, payload)
        db.commit()
        db.refresh(obj)
        
        return _insc_dict(obj), True
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def inscribir_masivo(
    curso_id: int,
    colaboradores: List[Dict[str, Any]]
) -> Dict[str, int]:
    """
    Inscribe múltiples colaboradores a un curso.
    
    Args:
        curso_id: ID del curso
        colaboradores: Lista de diccionarios con datos de colaboradores
        
    Returns:
        Diccionario con contadores de creados, ya_inscritos y errores
    """
    creados = 0
    ya_inscritos = 0
    errores = 0
    
    for colab in colaboradores:
        try:
            payload = {**colab, "curso_id": curso_id}
            _, created = inscribir_colaborador(payload)
            
            if created:
                creados += 1
            else:
                ya_inscritos += 1
        except Exception:
            errores += 1
    
    return {
        "creados": creados,
        "ya_inscritos": ya_inscritos,
        "errores": errores
    }


def asignar_por_reglas(curso_id: int) -> Dict[str, int]:
    """
    Asigna automáticamente un curso a colaboradores que cumplen las reglas.
    
    Args:
        curso_id: ID del curso
        
    Returns:
        Diccionario con contadores de creados, ya_inscritos y errores
    """
    # Validar que el curso existe
    db = repo.get_db()
    try:
        curso = cursos_repo.get_curso(db, curso_id)
        if not curso:
            return {"creados": 0, "ya_inscritos": 0, "errores": 1}
    finally:
        db.close()
    
    # Cargar metadata de colaboradores
    meta = load_colab_meta()
    candidatos = []
    
    if isinstance(meta, dict):
        for key, row in meta.items():
            payload = {
                "colaborador_key": str(key),
                "colaborador_nombre": (
                    row.get("full_name") or 
                    row.get("nombre") or 
                    str(key)
                ),
                "departamento": row.get("departamento"),
                "rol": row.get("role") or row.get("rol"),
                "puesto": row.get("puesto"),
                "curso_id": curso_id,
                "origen_regla": "regla_automatica",
            }
            candidatos.append(payload)
    
    return inscribir_masivo(curso_id, candidatos)


# ============================================================================
# SERVICIOS DE PROGRESO
# ============================================================================

def marcar_leccion_completada(
    inscripcion_id: int,
    leccion_id: int,
    tiempo_seg: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Marca una lección como completada y actualiza el progreso.
    
    Args:
        inscripcion_id: ID de la inscripción
        leccion_id: ID de la lección
        tiempo_seg: Tiempo en segundos empleado en la lección
        
    Returns:
        Diccionario con datos del progreso o None si no existe
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        # Validar inscripción
        insc = repo.get_inscripcion(db, inscripcion_id)
        if not insc:
            return None
        
        # Validar lección
        leccion = repo.get_leccion(db, leccion_id)
        if not leccion or leccion.curso_id != insc.curso_id:
            return None
        
        # Obtener o crear progreso
        prog = repo.get_progreso(db, inscripcion_id, leccion_id)
        es_primera_vez = (not prog) or (not prog.completada)
        
        if not prog:
            # Crear nuevo progreso
            prog = repo.create_progreso(
                db,
                {
                    "inscripcion_id": inscripcion_id,
                    "leccion_id": leccion_id,
                    "completada": True,
                    "intentos": 1,
                    "tiempo_seg": tiempo_seg,
                    "fecha_completado": datetime.utcnow()
                }
            )
        else:
            # Actualizar progreso existente
            if not prog.completada:
                prog.completada = True
                prog.fecha_completado = datetime.utcnow()
            
            prog.intentos += 1
            
            if tiempo_seg is not None:
                prog.tiempo_seg = (prog.tiempo_seg or 0) + tiempo_seg
        
        # Recalcular avance de la inscripción
        _recalcular_avance(db, insc)
        
        db.commit()
        db.refresh(prog)
        
        # Otorgar gamificación si es primera vez
        if es_primera_vez:
            try:
                from fastapi_modulo.modulos.capacitacion.servicios.gamificacion_service import (
                    check_y_otorgar_insignias,
                    otorgar_puntos
                )
                
                otorgar_puntos(
                    insc.colaborador_key,
                    "leccion_completada",
                    10,
                    "leccion",
                    leccion_id
                )
                check_y_otorgar_insignias(insc.colaborador_key)
            except Exception:
                # No fallar si hay error en gamificación
                pass
        
        return _progreso_dict(prog)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def get_progreso_curso(inscripcion_id: int) -> List[Dict[str, Any]]:
    """
    Obtiene el progreso de todas las lecciones de una inscripción.
    
    Args:
        inscripcion_id: ID de la inscripción
        
    Returns:
        Lista de progreso de lecciones como diccionarios
    """
    db = repo.get_db()
    try:
        progresos = repo.list_progreso_curso(db, inscripcion_id)
        return [_progreso_dict(item) for item in progresos]
    finally:
        db.close()


# ============================================================================
# SERVICIOS DE ENCUESTAS
# ============================================================================

def registrar_encuesta_satisfaccion(
    inscripcion_id: int,
    calificacion: int,
    comentario: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Registra o actualiza una encuesta de satisfacción.
    
    Args:
        inscripcion_id: ID de la inscripción
        calificacion: Calificación numérica
        comentario: Comentario opcional
        
    Returns:
        Diccionario con datos de la encuesta o None
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        # Validar inscripción
        insc = repo.get_inscripcion(db, inscripcion_id)
        if not insc:
            return None
        
        # Obtener o crear encuesta
        obj = repo.get_satisfaccion(db, inscripcion_id)
        
        if obj:
            # Actualizar encuesta existente
            obj.calificacion = calificacion
            obj.comentario = comentario
            obj.respondida_en = datetime.utcnow()
        else:
            # Crear nueva encuesta
            obj = repo.create_satisfaccion(
                db,
                {
                    "tenant_id": insc.tenant_id,
                    "inscripcion_id": inscripcion_id,
                    "calificacion": calificacion,
                    "comentario": comentario,
                    "respondida_en": datetime.utcnow(),
                },
            )
        
        db.commit()
        
        return {
            "inscripcion_id": inscripcion_id,
            "calificacion": obj.calificacion,
            "comentario": obj.comentario,
            "respondida_en": _dt(obj.respondida_en)
        }
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


# ============================================================================
# SERVICIOS DE DASHBOARD Y ESTADÍSTICAS
# ============================================================================

def get_dashboard_stats() -> Dict[str, Any]:
    """
    Obtiene estadísticas completas del dashboard de capacitación.
    
    Returns:
        Diccionario con métricas y estadísticas del dashboard
    """
    db = repo.get_db()
    try:
        counts = repo.dashboard_counts(db)
        
        # Calcular métricas básicas
        total_inscs = counts["total_inscs"]
        completadas = counts["completadas"]
        aprobadas = total_inscs - counts["reprobadas"] if total_inscs else 0
        
        tasa_completado = round(
            (completadas / total_inscs) * 100, 
            1
        ) if total_inscs else 0.0
        
        tasa_aprobacion = round(
            (aprobadas / total_inscs) * 100, 
            1
        ) if total_inscs else 0.0
        
        return {
            # Métricas generales
            "total_inscripciones": total_inscs,
            "completadas": completadas,
            "en_progreso": counts["en_progreso"],
            "reprobadas": counts["reprobadas"],
            "pendientes": counts["pendientes"],
            "cursos_publicados": counts["cursos_publicados"],
            "cursos_archivados": counts["cursos_archivados"],
            "certificados_emitidos": counts["certificados"],
            "colaboradores_unicos": counts["colaboradores_unicos"],
            "tasa_completado": tasa_completado,
            "tasa_aprobacion": tasa_aprobacion,
            "promedio_finalizacion_dias": counts["promedio_finalizacion_dias"],
            
            # Cursos obligatorios vencidos
            "obligatorios_vencidos_total": sum(
                int(row[2] or 0) 
                for row in counts["obligatorios_vencidos"]
            ),
            
            # Top cursos
            "top_cursos_completados": [
                {
                    "curso_id": row[0],
                    "nombre": row[1],
                    "total": row[2]
                }
                for row in counts["top_completados"]
            ],
            
            "top_cursos_abandonados": [
                {
                    "curso_id": row[0],
                    "nombre": row[1],
                    "total": row[2]
                }
                for row in counts["top_abandonados"]
            ],
            
            # Cursos sin avance
            "sin_avance": [
                {
                    "colaborador_key": row[0],
                    "colaborador_nombre": row[1],
                    "curso_nombre": row[2],
                    "departamento": row[3]
                }
                for row in counts["cursos_sin_avance"]
            ],
            
            # Cursos con peor aprobación
            "cursos_peor_aprobacion": [
                {
                    "curso_id": row[0],
                    "nombre": row[1],
                    "total": int(row[2] or 0),
                    "aprobados": int(row[3] or 0),
                    "tasa_aprobacion": round(
                        (float(row[3] or 0) / float(row[2] or 1)) * 100, 
                        1
                    ),
                }
                for row in counts["aprobacion_baja"]
            ],
            
            # Inscripciones por curso
            "inscripciones_por_curso": [
                {
                    "curso_id": row[0],
                    "nombre": row[1],
                    "total": row[2]
                }
                for row in counts["inscripcion_por_curso"]
            ],
            
            # Distribuciones
            "estados": [
                {
                    "estado": row[0],
                    "n": row[1]
                }
                for row in counts["estados_dist"]
            ],
            
            "departamentos": [
                {
                    "departamento": row[0] or "Sin departamento",
                    "n": row[1]
                }
                for row in counts["dept_dist"]
            ],
            
            "avance_departamento": [
                {
                    "departamento": row[0] or "Sin departamento",
                    "avance": round(float(row[1] or 0.0), 1)
                }
                for row in counts["dept_avance"]
            ],
            
            # Certificados por periodo
            "certificados_por_periodo": [
                {
                    "periodo": str(row[0]),
                    "total": int(row[1] or 0)
                }
                for row in counts["certificados_periodo"]
            ],
            
            # Obligatorios vencidos detalle
            "obligatorios_vencidos": [
                {
                    "curso_id": row[0],
                    "nombre": row[1],
                    "total": int(row[2] or 0)
                }
                for row in counts["obligatorios_vencidos"]
            ],
        }
    finally:
        db.close()


# ============================================================================
# SERVICIOS DE OPERACIONES PROGRAMADAS
# ============================================================================

def ejecutar_operacion_cursos() -> Dict[str, Any]:
    """
    Ejecuta operaciones programadas: recordatorios y reinscripciones.
    
    Returns:
        Diccionario con recordatorios enviados y reinscripciones realizadas
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        now = datetime.utcnow()
        recordatorios = []
        reinscripciones = 0
        
        # Procesar recordatorios pendientes
        for insc in repo.list_recordatorios_pendientes(db, now):
            dias = int((insc.fecha_vencimiento - now).total_seconds() // 86400)
            recordatorio_dias = int(
                getattr(insc.curso, "recordatorio_dias", 7) or 7
            )
            
            if dias <= recordatorio_dias:
                insc.recordatorio_enviado_en = now
                recordatorios.append({
                    "inscripcion_id": insc.id,
                    "curso_id": insc.curso_id,
                    "colaborador_key": insc.colaborador_key,
                    "vence_en_dias": dias
                })
        
        # Procesar inscripciones vencidas
        for insc in repo.list_inscripciones_vencibles(db, now):
            # Marcar como reprobado si no está completado
            if insc.estado != "completado":
                insc.estado = "reprobado"
            
            # Reinscripción automática si está habilitada
            if getattr(insc.curso, "reinscripcion_automatica", False):
                # Verificar que no haya una inscripción más reciente
                existing = repo.get_existing_inscripcion(
                    db,
                    insc.colaborador_key,
                    insc.curso_id
                )
                
                if existing and existing.id != insc.id:
                    if (existing.fecha_inscripcion and 
                        insc.fecha_inscripcion and
                        existing.fecha_inscripcion > insc.fecha_inscripcion):
                        continue
                
                # Reiniciar inscripción
                insc.estado = "pendiente"
                insc.pct_avance = 0.0
                insc.aprobado = None
                insc.puntaje_final = None
                insc.fecha_inscripcion = now
                insc.fecha_inicio_real = None
                insc.fecha_completado = None
                insc.fecha_vencimiento = _fecha_vencimiento(insc.curso, now)
                insc.origen_regla = "reinscripcion_automatica"
                reinscripciones += 1
        
        db.commit()
        
        return {
            "recordatorios": recordatorios,
            "reinscripciones": reinscripciones
        }
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()
        