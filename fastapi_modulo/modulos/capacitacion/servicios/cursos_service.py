from __future__ import annotations

import json
import random
import string
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from fastapi_modulo.modulos.capacitacion.modelos.db_models import (
    CapCategoria,
    CapCurso,
    CapLeccion,
    CapRutaAprendizaje,
    CapRutaCurso
)
from fastapi_modulo.modulos.capacitacion.repositorios import cursos_repository as repo
from fastapi_modulo.modulos.capacitacion.servicios.audit_service import registrar_evento


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
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _d(value: Optional[date]) -> Optional[str]:
    """
    Convierte una fecha a string.
    
    Args:
        value: Objeto date o None
        
    Returns:
        String de fecha o None
    """
    if value is None:
        return None
    return str(value)


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


def _normalize_course_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normaliza el payload de un curso para guardarlo en la base de datos.
    
    Args:
        data: Diccionario con datos del curso
        
    Returns:
        Diccionario normalizado
    """
    payload = dict(data)
    
    # Convertir strings de fecha a objetos date
    for field in ("fecha_inicio", "fecha_fin"):
        if isinstance(payload.get(field), str) and payload.get(field):
            try:
                payload[field] = date.fromisoformat(payload[field])
            except ValueError:
                payload[field] = None
    
    # Convertir listas a JSON strings
    for field in ("prerrequisitos", "departamentos"):
        if field in payload:
            payload[field + "_json"] = json.dumps(payload.pop(field) or [])
    
    return payload


def _gen_codigo() -> str:
    """
    Genera un código único para un curso.
    
    Returns:
        Código en formato CAP-XXXXXX
    """
    chars = string.ascii_uppercase + string.digits
    return "CAP-" + "".join(random.choices(chars, k=6))


# ============================================================================
# FUNCIONES DE SERIALIZACIÓN DE MODELOS
# ============================================================================

def _cat_dict(obj: CapCategoria) -> Dict[str, Any]:
    """
    Convierte un objeto CapCategoria a diccionario.
    
    Args:
        obj: Objeto CapCategoria
        
    Returns:
        Diccionario con datos de la categoría
    """
    return {
        "id": obj.id,
        "nombre": obj.nombre,
        "descripcion": obj.descripcion,
        "color": obj.color,
        "creado_en": _dt(obj.creado_en)
    }


def _leccion_dict(obj: CapLeccion) -> Dict[str, Any]:
    """
    Convierte un objeto CapLeccion a diccionario.
    
    Args:
        obj: Objeto CapLeccion
        
    Returns:
        Diccionario con datos de la lección
    """
    return {
        "id": obj.id,
        "curso_id": obj.curso_id,
        "titulo": obj.titulo,
        "tipo": obj.tipo,
        "contenido": obj.contenido,
        "url_archivo": obj.url_archivo,
        "duracion_min": obj.duracion_min,
        "orden": obj.orden,
        "es_obligatoria": obj.es_obligatoria,
        "creado_en": _dt(obj.creado_en),
    }


def _curso_dict(obj: CapCurso, with_lecciones: bool = False) -> Dict[str, Any]:
    """
    Convierte un objeto CapCurso a diccionario.
    
    Args:
        obj: Objeto CapCurso
        with_lecciones: Si debe incluir las lecciones del curso
        
    Returns:
        Diccionario con datos del curso
    """
    data = {
        "id": obj.id,
        "codigo": obj.codigo,
        "nombre": obj.nombre,
        "descripcion": obj.descripcion,
        "objetivo": obj.objetivo,
        "categoria_id": obj.categoria_id,
        "categoria_nombre": obj.categoria.nombre if obj.categoria else None,
        "nivel": obj.nivel,
        "estado": obj.estado,
        "responsable": obj.responsable,
        "duracion_horas": obj.duracion_horas,
        "puntaje_aprobacion": obj.puntaje_aprobacion,
        "imagen_url": obj.imagen_url,
        "fecha_inicio": _d(obj.fecha_inicio),
        "fecha_fin": _d(obj.fecha_fin),
        "es_obligatorio": obj.es_obligatorio,
        "vence_dias": obj.vence_dias,
        "recordatorio_dias": obj.recordatorio_dias,
        "reinscripcion_automatica": obj.reinscripcion_automatica,
        "prerrequisitos": _loads_list(obj.prerrequisitos_json),
        "departamentos": _loads_list(obj.departamentos_json),
        "rol_objetivo": obj.rol_objetivo,
        "puesto_objetivo": obj.puesto_objetivo,
        "bloquear_certificado_encuesta": obj.bloquear_certificado_encuesta,
        "requiere_encuesta_satisfaccion": obj.requiere_encuesta_satisfaccion,
        "version_numero": obj.version_numero,
        "version_padre_id": obj.version_padre_id,
        "version_actual": obj.version_actual,
        "creado_por": obj.creado_por,
        "actualizado_por": obj.actualizado_por,
        "publicado_por": obj.publicado_por,
        "publicado_en": _dt(obj.publicado_en),
        "total_lecciones": len(obj.lecciones) if obj.lecciones else 0,
        "total_inscripciones": len(obj.inscripciones) if obj.inscripciones else 0,
        "creado_en": _dt(obj.creado_en),
        "actualizado_en": _dt(obj.actualizado_en),
    }
    
    if with_lecciones and obj.lecciones:
        data["lecciones"] = [_leccion_dict(leccion) for leccion in obj.lecciones]
    
    return data


def _ruta_dict(obj: CapRutaAprendizaje) -> Dict[str, Any]:
    """
    Convierte un objeto CapRutaAprendizaje a diccionario.
    
    Args:
        obj: Objeto CapRutaAprendizaje
        
    Returns:
        Diccionario con datos de la ruta
    """
    return {
        "id": obj.id,
        "nombre": obj.nombre,
        "descripcion": obj.descripcion,
        "rol_objetivo": obj.rol_objetivo,
        "puesto_objetivo": obj.puesto_objetivo,
        "departamentos": _loads_list(obj.departamentos_json),
        "cursos": [
            {
                "curso_id": item.curso_id,
                "orden": item.orden,
                "obligatorio": item.obligatorio
            }
            for item in (obj.cursos or [])
        ],
    }


# ============================================================================
# SERVICIOS DE CATEGORÍAS
# ============================================================================

def list_categorias(tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Lista todas las categorías.
    
    Args:
        tenant_id: ID del tenant (opcional)
        
    Returns:
        Lista de categorías como diccionarios
    """
    db = repo.get_db()
    try:
        categorias = repo.list_categorias(db)
        return [_cat_dict(item) for item in categorias]
    finally:
        db.close()


def get_categoria(cat_id: int, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Obtiene una categoría por ID.
    
    Args:
        cat_id: ID de la categoría
        tenant_id: ID del tenant (opcional)
        
    Returns:
        Diccionario con datos de la categoría o None
    """
    db = repo.get_db()
    try:
        obj = repo.get_categoria(db, cat_id)
        return _cat_dict(obj) if obj else None
    finally:
        db.close()


def create_categoria(
    data: Dict[str, Any],
    tenant_id: Optional[str] = None,
    actor_key: Optional[str] = None,
    actor_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Crea una nueva categoría.
    
    Args:
        data: Datos de la categoría
        tenant_id: ID del tenant
        actor_key: Identificador del actor
        actor_name: Nombre del actor
        
    Returns:
        Diccionario con la categoría creada
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        data = dict(data)
        if tenant_id:
            data["tenant_id"] = tenant_id
        
        obj = repo.create_categoria(db, data)
        db.commit()
        db.refresh(obj)
        
        return _cat_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def update_categoria(
    cat_id: int,
    data: Dict[str, Any],
    tenant_id: Optional[str] = None,
    actor_key: Optional[str] = None,
    actor_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Actualiza una categoría existente.
    
    Args:
        cat_id: ID de la categoría
        data: Datos a actualizar
        tenant_id: ID del tenant
        actor_key: Identificador del actor
        actor_name: Nombre del actor
        
    Returns:
        Diccionario con la categoría actualizada o None
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        obj = repo.update_categoria(db, cat_id, data)
        if not obj:
            return None
        
        db.commit()
        db.refresh(obj)
        
        return _cat_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def delete_categoria(
    cat_id: int,
    tenant_id: Optional[str] = None,
    actor_key: Optional[str] = None,
    actor_name: Optional[str] = None
) -> bool:
    """
    Elimina una categoría.
    
    Args:
        cat_id: ID de la categoría
        tenant_id: ID del tenant
        actor_key: Identificador del actor
        actor_name: Nombre del actor
        
    Returns:
        True si se eliminó, False si no existía
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        ok = repo.delete_categoria(db, cat_id)
        if not ok:
            return False
        
        db.commit()
        return True
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


# ============================================================================
# SERVICIOS DE CURSOS
# ============================================================================

def list_cursos(
    tenant_id: Optional[str] = None,
    estado: Optional[str] = None,
    categoria_id: Optional[int] = None,
    nivel: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Lista cursos con filtros opcionales.
    
    Args:
        tenant_id: ID del tenant
        estado: Estado del curso (borrador, publicado, archivado)
        categoria_id: ID de la categoría
        nivel: Nivel del curso
        
    Returns:
        Lista de cursos como diccionarios
    """
    db = repo.get_db()
    try:
        cursos = repo.list_cursos(db, estado, categoria_id, nivel)
        return [_curso_dict(item) for item in cursos]
    finally:
        db.close()


def get_curso(
    curso_id: int,
    tenant_id: Optional[str] = None,
    with_lecciones: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Obtiene un curso por ID.
    
    Args:
        curso_id: ID del curso
        tenant_id: ID del tenant
        with_lecciones: Si debe incluir las lecciones
        
    Returns:
        Diccionario con datos del curso o None
    """
    db = repo.get_db()
    try:
        obj = repo.get_curso(db, curso_id)
        return _curso_dict(obj, with_lecciones=with_lecciones) if obj else None
    finally:
        db.close()


def create_curso(
    data: Dict[str, Any],
    tenant_id: Optional[str] = None,
    actor_key: Optional[str] = None,
    actor_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Crea un nuevo curso.
    
    Args:
        data: Datos del curso
        tenant_id: ID del tenant
        actor_key: Identificador del actor
        actor_name: Nombre del actor
        
    Returns:
        Diccionario con el curso creado
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        data = _normalize_course_payload(data)
        
        # Generar código único
        codigo = None
        for _ in range(10):
            codigo = _gen_codigo()
            if not repo.get_curso_by_codigo(db, codigo):
                break
        data["codigo"] = codigo
        
        # Asignar tenant y actor
        if tenant_id:
            data["tenant_id"] = tenant_id
        if actor_key:
            data.setdefault("creado_por", actor_key)
            data.setdefault("actualizado_por", actor_key)
        
        # Si se publica inmediatamente, registrar datos de publicación
        if str(data.get("estado", "")) == "publicado":
            data["publicado_por"] = actor_key
            data["publicado_en"] = datetime.utcnow()
        
        # Crear curso
        obj = repo.create_curso(db, data)
        
        # Registrar evento de creación
        registrar_evento(
            db,
            "curso",
            obj.id,
            "created",
            actor_key=actor_key,
            actor_nombre=actor_name,
            tenant_id=obj.tenant_id,
            detalle={"nombre": obj.nombre, "estado": str(obj.estado)},
        )
        
        # Si está publicado, registrar evento de publicación
        if str(obj.estado) == "publicado":
            registrar_evento(
                db,
                "curso",
                obj.id,
                "published",
                actor_key=actor_key,
                actor_nombre=actor_name,
                tenant_id=obj.tenant_id,
                detalle={"estado": str(obj.estado)},
            )
        
        db.commit()
        db.refresh(obj)
        
        return _curso_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def update_curso(
    curso_id: int,
    data: Dict[str, Any],
    tenant_id: Optional[str] = None,
    actor_key: Optional[str] = None,
    actor_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Actualiza un curso existente.
    
    Args:
        curso_id: ID del curso
        data: Datos a actualizar
        tenant_id: ID del tenant
        actor_key: Identificador del actor
        actor_name: Nombre del actor
        
    Returns:
        Diccionario con el curso actualizado o None
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        data = _normalize_course_payload(data)
        data.pop("codigo", None)  # No permitir cambiar el código
        
        # Obtener estado actual
        current = repo.get_curso(db, curso_id)
        if not current:
            return None
        
        prev_estado = str(current.estado)
        
        # Actualizar timestamps
        data["actualizado_en"] = datetime.utcnow()
        if actor_key:
            data["actualizado_por"] = actor_key
        
        # Si se está publicando, registrar datos de publicación
        next_estado = str(data.get("estado", prev_estado))
        if next_estado == "publicado" and prev_estado != "publicado":
            data["publicado_por"] = actor_key
            data["publicado_en"] = datetime.utcnow()
        
        # Actualizar curso
        obj = repo.update_curso(db, curso_id, data)
        if not obj:
            return None
        
        # Registrar evento de actualización
        registrar_evento(
            db,
            "curso",
            obj.id,
            "updated",
            actor_key=actor_key,
            actor_nombre=actor_name,
            tenant_id=obj.tenant_id,
            detalle={
                "estado_anterior": prev_estado,
                "estado_nuevo": str(obj.estado)
            },
        )
        
        # Si cambió a publicado, registrar evento de publicación
        if prev_estado != "publicado" and str(obj.estado) == "publicado":
            registrar_evento(
                db,
                "curso",
                obj.id,
                "published",
                actor_key=actor_key,
                actor_nombre=actor_name,
                tenant_id=obj.tenant_id,
                detalle={
                    "estado_anterior": prev_estado,
                    "estado_nuevo": str(obj.estado)
                },
            )
        
        db.commit()
        db.refresh(obj)
        
        return _curso_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def duplicate_as_new_version(
    curso_id: int,
    tenant_id: Optional[str] = None,
    actor_key: Optional[str] = None,
    actor_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Duplica un curso como nueva versión.
    
    Args:
        curso_id: ID del curso a duplicar
        tenant_id: ID del tenant
        actor_key: Identificador del actor
        actor_name: Nombre del actor
        
    Returns:
        Diccionario con el nuevo curso creado o None
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        current = repo.get_curso(db, curso_id)
        if not current:
            return None
        
        # Marcar versión actual como no actual
        current.version_actual = False
        
        # Preparar datos para nueva versión
        nueva_version = int(current.version_numero or 1) + 1
        data = {
            "tenant_id": tenant_id or current.tenant_id,
            "codigo": _gen_codigo(),
            "nombre": f"{current.nombre} v{nueva_version}",
            "descripcion": current.descripcion,
            "objetivo": current.objetivo,
            "categoria_id": current.categoria_id,
            "nivel": current.nivel,
            "estado": "borrador",
            "responsable": current.responsable,
            "duracion_horas": current.duracion_horas,
            "puntaje_aprobacion": current.puntaje_aprobacion,
            "imagen_url": current.imagen_url,
            "fecha_inicio": current.fecha_inicio,
            "fecha_fin": current.fecha_fin,
            "es_obligatorio": current.es_obligatorio,
            "vence_dias": current.vence_dias,
            "recordatorio_dias": current.recordatorio_dias,
            "reinscripcion_automatica": current.reinscripcion_automatica,
            "prerrequisitos_json": current.prerrequisitos_json,
            "departamentos_json": current.departamentos_json,
            "rol_objetivo": current.rol_objetivo,
            "puesto_objetivo": current.puesto_objetivo,
            "bloquear_certificado_encuesta": current.bloquear_certificado_encuesta,
            "requiere_encuesta_satisfaccion": current.requiere_encuesta_satisfaccion,
            "version_numero": nueva_version,
            "version_padre_id": current.id,
            "version_actual": True,
            "creado_por": actor_key,
            "actualizado_por": actor_key,
        }
        
        # Crear nuevo curso
        new_course = repo.create_curso(db, data)
        
        # Duplicar lecciones
        for leccion in current.lecciones:
            repo.create_leccion(
                db,
                {
                    "tenant_id": tenant_id or current.tenant_id,
                    "curso_id": new_course.id,
                    "titulo": leccion.titulo,
                    "tipo": leccion.tipo,
                    "contenido": leccion.contenido,
                    "url_archivo": leccion.url_archivo,
                    "duracion_min": leccion.duracion_min,
                    "orden": leccion.orden,
                    "es_obligatoria": leccion.es_obligatoria,
                },
            )
        
        # Registrar evento
        registrar_evento(
            db,
            "curso",
            new_course.id,
            "version_created",
            actor_key=actor_key,
            actor_nombre=actor_name,
            tenant_id=new_course.tenant_id,
            detalle={"version_padre_id": current.id, "version_numero": nueva_version}
        )
        
        db.commit()
        db.refresh(new_course)
        
        return _curso_dict(new_course, with_lecciones=True)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def delete_curso(
    curso_id: int,
    tenant_id: Optional[str] = None,
    actor_key: Optional[str] = None,
    actor_name: Optional[str] = None
) -> bool:
    """
    Elimina un curso.
    
    Args:
        curso_id: ID del curso
        tenant_id: ID del tenant
        actor_key: Identificador del actor
        actor_name: Nombre del actor
        
    Returns:
        True si se eliminó, False si no existía
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        # Registrar evento antes de eliminar
        obj = repo.get_curso(db, curso_id)
        if obj:
            registrar_evento(
                db,
                "curso",
                obj.id,
                "deleted",
                actor_key=actor_key,
                actor_nombre=actor_name,
                tenant_id=obj.tenant_id,
                detalle={"nombre": obj.nombre},
            )
        
        ok = repo.delete_curso(db, curso_id)
        if not ok:
            return False
        
        db.commit()
        return True
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


# ============================================================================
# SERVICIOS DE LECCIONES
# ============================================================================

def list_lecciones(curso_id: int, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Lista todas las lecciones de un curso.
    
    Args:
        curso_id: ID del curso
        tenant_id: ID del tenant
        
    Returns:
        Lista de lecciones como diccionarios
    """
    db = repo.get_db()
    try:
        lecciones = repo.list_lecciones(db, curso_id)
        return [_leccion_dict(item) for item in lecciones]
    finally:
        db.close()


def get_leccion(leccion_id: int, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Obtiene una lección por ID.
    
    Args:
        leccion_id: ID de la lección
        tenant_id: ID del tenant
        
    Returns:
        Diccionario con datos de la lección o None
    """
    db = repo.get_db()
    try:
        obj = repo.get_leccion(db, leccion_id)
        return _leccion_dict(obj) if obj else None
    finally:
        db.close()


def create_leccion(
    data: Dict[str, Any],
    tenant_id: Optional[str] = None,
    actor_key: Optional[str] = None,
    actor_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Crea una nueva lección.
    
    Args:
        data: Datos de la lección
        tenant_id: ID del tenant
        actor_key: Identificador del actor
        actor_name: Nombre del actor
        
    Returns:
        Diccionario con la lección creada
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        data = dict(data)
        if tenant_id:
            data["tenant_id"] = tenant_id
        
        obj = repo.create_leccion(db, data)
        db.commit()
        db.refresh(obj)
        
        return _leccion_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def update_leccion(
    leccion_id: int,
    data: Dict[str, Any],
    tenant_id: Optional[str] = None,
    actor_key: Optional[str] = None,
    actor_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Actualiza una lección existente.
    
    Args:
        leccion_id: ID de la lección
        data: Datos a actualizar
        tenant_id: ID del tenant
        actor_key: Identificador del actor
        actor_name: Nombre del actor
        
    Returns:
        Diccionario con la lección actualizada o None
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        obj = repo.update_leccion(db, leccion_id, data)
        if not obj:
            return None
        
        db.commit()
        db.refresh(obj)
        
        return _leccion_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def delete_leccion(
    leccion_id: int,
    tenant_id: Optional[str] = None,
    actor_key: Optional[str] = None,
    actor_name: Optional[str] = None
) -> bool:
    """
    Elimina una lección.
    
    Args:
        leccion_id: ID de la lección
        tenant_id: ID del tenant
        actor_key: Identificador del actor
        actor_name: Nombre del actor
        
    Returns:
        True si se eliminó, False si no existía
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        ok = repo.delete_leccion(db, leccion_id)
        if not ok:
            return False
        
        db.commit()
        return True
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def reordenar_lecciones(
    curso_id: int,
    orden_ids: List[int],
    tenant_id: Optional[str] = None,
    actor_key: Optional[str] = None,
    actor_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Reordena las lecciones de un curso.
    
    Args:
        curso_id: ID del curso
        orden_ids: Lista de IDs en el nuevo orden
        tenant_id: ID del tenant
        actor_key: Identificador del actor
        actor_name: Nombre del actor
        
    Returns:
        Lista de lecciones reordenadas
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        repo.reorder_lecciones(db, curso_id, orden_ids)
        db.commit()
        
        lecciones = repo.list_lecciones(db, curso_id)
        return [_leccion_dict(item) for item in lecciones]
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


# ============================================================================
# SERVICIOS DE RUTAS DE APRENDIZAJE
# ============================================================================

def create_ruta(
    data: Dict[str, Any],
    tenant_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Crea una nueva ruta de aprendizaje.
    
    Args:
        data: Datos de la ruta incluyendo cursos asociados
        tenant_id: ID del tenant
        
    Returns:
        Diccionario con la ruta creada
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        payload = dict(data)
        cursos = payload.pop("cursos", [])
        payload["tenant_id"] = tenant_id or payload.get("tenant_id", "default")
        
        # Normalizar departamentos a JSON
        if "departamentos" in payload:
            payload["departamentos_json"] = json.dumps(payload.pop("departamentos") or [])
        
        # Crear ruta
        ruta = repo.create_ruta(db, payload)
        
        # Asociar cursos a la ruta
        for idx, curso in enumerate(cursos):
            if isinstance(curso, dict):
                curso_id = curso["curso_id"]
                orden = curso.get("orden", idx)
                obligatorio = curso.get("obligatorio", True)
            else:
                curso_id = int(curso)
                orden = idx
                obligatorio = True
            
            repo.create_ruta_curso(
                db,
                {
                    "tenant_id": payload["tenant_id"],
                    "ruta_id": ruta.id,
                    "curso_id": curso_id,
                    "orden": orden,
                    "obligatorio": obligatorio,
                },
            )
        
        db.commit()
        db.refresh(ruta)
        
        return _ruta_dict(ruta)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def list_rutas() -> List[Dict[str, Any]]:
    """
    Lista todas las rutas de aprendizaje.
    
    Returns:
        Lista de rutas como diccionarios
    """
    db = repo.get_db()
    try:
        rutas = repo.list_rutas(db)
        return [_ruta_dict(ruta) for ruta in rutas]
    finally:
        db.close()
        
