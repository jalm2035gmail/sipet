from __future__ import annotations

import json
import random
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from fastapi_modulo.modulos.capacitacion.modelos.db_models import (
    CapEvaluacion,
    CapInscripcion,
    CapIntentoEvaluacion,
    CapOpcion,
    CapPregunta
)
from fastapi_modulo.modulos.capacitacion.repositorios import evaluaciones_repository as repo
from fastapi_modulo.modulos.capacitacion.servicios.audit_service import registrar_evento
from fastapi_modulo.modulos.capacitacion.servicios.certificados_service import (
    cert_dict,
    emitir_certificado
)


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


# ============================================================================
# FUNCIONES DE SERIALIZACIÓN DE MODELOS
# ============================================================================

def _eval_dict(obj: CapEvaluacion) -> Dict[str, Any]:
    """
    Convierte un objeto CapEvaluacion a diccionario.
    
    Args:
        obj: Objeto CapEvaluacion
        
    Returns:
        Diccionario con datos de la evaluación
    """
    return {
        "id": obj.id,
        "curso_id": obj.curso_id,
        "titulo": obj.titulo,
        "instrucciones": obj.instrucciones,
        "puntaje_minimo": obj.puntaje_minimo,
        "max_intentos": obj.max_intentos,
        "preguntas_por_intento": obj.preguntas_por_intento,
        "tiempo_limite_min": obj.tiempo_limite_min,
        "creado_por": obj.creado_por,
        "actualizado_por": obj.actualizado_por,
        "publicado_por": obj.publicado_por,
        "publicado_en": _dt(obj.publicado_en),
        "creado_en": _dt(obj.creado_en),
    }


def _pregunta_dict(obj: CapPregunta, incluir_correctas: bool = False) -> Dict[str, Any]:
    """
    Convierte un objeto CapPregunta a diccionario.
    
    Args:
        obj: Objeto CapPregunta
        incluir_correctas: Si debe incluir las respuestas correctas
        
    Returns:
        Diccionario con datos de la pregunta
    """
    opciones = []
    for opcion in obj.opciones:
        data = {
            "id": opcion.id,
            "texto": opcion.texto,
            "orden": opcion.orden
        }
        if incluir_correctas:
            data["es_correcta"] = opcion.es_correcta
        opciones.append(data)
    
    return {
        "id": obj.id,
        "evaluacion_id": obj.evaluacion_id,
        "enunciado": obj.enunciado,
        "tipo": obj.tipo,
        "explicacion": obj.explicacion if incluir_correctas else None,
        "puntaje": obj.puntaje,
        "orden": obj.orden,
        "opciones": opciones,
    }


def _intento_dict(obj: CapIntentoEvaluacion) -> Dict[str, Any]:
    """
    Convierte un objeto CapIntentoEvaluacion a diccionario.
    
    Args:
        obj: Objeto CapIntentoEvaluacion
        
    Returns:
        Diccionario con datos del intento
    """
    return {
        "id": obj.id,
        "inscripcion_id": obj.inscripcion_id,
        "evaluacion_id": obj.evaluacion_id,
        "numero_intento": obj.numero_intento,
        "puntaje": obj.puntaje,
        "puntaje_maximo": obj.puntaje_maximo,
        "aprobado": obj.aprobado,
        "fecha_inicio": _dt(obj.fecha_inicio),
        "fecha_fin": _dt(obj.fecha_fin),
    }


# ============================================================================
# SERVICIOS DE EVALUACIONES
# ============================================================================

def list_evaluaciones(
    curso_id: int,
    tenant_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Lista todas las evaluaciones de un curso.
    
    Args:
        curso_id: ID del curso
        tenant_id: ID del tenant
        
    Returns:
        Lista de evaluaciones como diccionarios
    """
    db = repo.get_db()
    try:
        evaluaciones = repo.list_evaluaciones(db, curso_id)
        return [_eval_dict(item) for item in evaluaciones]
    finally:
        db.close()


def get_evaluacion(
    eval_id: int,
    tenant_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Obtiene una evaluación por ID.
    
    Args:
        eval_id: ID de la evaluación
        tenant_id: ID del tenant
        
    Returns:
        Diccionario con datos de la evaluación o None
    """
    db = repo.get_db()
    try:
        obj = repo.get_evaluacion(db, eval_id)
        return _eval_dict(obj) if obj else None
    finally:
        db.close()


def create_evaluacion(
    data: Dict[str, Any],
    tenant_id: Optional[str] = None,
    actor_key: Optional[str] = None,
    actor_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Crea una nueva evaluación con sus preguntas y opciones.
    
    Args:
        data: Datos de la evaluación incluyendo preguntas
        tenant_id: ID del tenant
        actor_key: Identificador del actor
        actor_name: Nombre del actor
        
    Returns:
        Diccionario con la evaluación creada
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        data = dict(data)
        preguntas_data = data.pop("preguntas", [])
        
        # Asignar tenant y actor
        if tenant_id:
            data["tenant_id"] = tenant_id
        if actor_key:
            data.setdefault("creado_por", actor_key)
            data.setdefault("actualizado_por", actor_key)
        
        # Crear evaluación
        obj = repo.create_evaluacion(db, data)
        
        # Crear preguntas y opciones
        for pregunta_data in preguntas_data:
            opciones_data = pregunta_data.pop("opciones", [])
            
            # Crear pregunta
            pregunta = repo.create_pregunta(
                db,
                {
                    **pregunta_data,
                    "evaluacion_id": obj.id,
                    "tenant_id": obj.tenant_id
                }
            )
            
            # Crear opciones de la pregunta
            for opcion_data in opciones_data:
                repo.create_opcion(
                    db,
                    {
                        **opcion_data,
                        "pregunta_id": pregunta.id,
                        "tenant_id": obj.tenant_id
                    }
                )
        
        # Registrar evento de auditoría
        registrar_evento(
            db,
            "evaluacion",
            obj.id,
            "created",
            actor_key=actor_key,
            actor_nombre=actor_name,
            tenant_id=obj.tenant_id,
            detalle={
                "titulo": obj.titulo,
                "curso_id": obj.curso_id
            }
        )
        
        db.commit()
        db.refresh(obj)
        
        return _eval_dict(obj)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


# ============================================================================
# SERVICIOS DE PREGUNTAS
# ============================================================================

def list_preguntas(
    eval_id: int,
    tenant_id: Optional[str] = None,
    incluir_correctas: bool = False
) -> List[Dict[str, Any]]:
    """
    Lista todas las preguntas de una evaluación.
    
    Args:
        eval_id: ID de la evaluación
        tenant_id: ID del tenant
        incluir_correctas: Si debe incluir las respuestas correctas
        
    Returns:
        Lista de preguntas como diccionarios
    """
    db = repo.get_db()
    try:
        preguntas = repo.list_preguntas(db, eval_id)
        return [_pregunta_dict(item, incluir_correctas) for item in preguntas]
    finally:
        db.close()


def create_pregunta(
    data: Dict[str, Any],
    tenant_id: Optional[str] = None,
    actor_key: Optional[str] = None,
    actor_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Crea una nueva pregunta con sus opciones.
    
    Args:
        data: Datos de la pregunta incluyendo opciones
        tenant_id: ID del tenant
        actor_key: Identificador del actor
        actor_name: Nombre del actor
        
    Returns:
        Diccionario con la pregunta creada
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        data = dict(data)
        opciones = data.pop("opciones", [])
        
        # Obtener evaluación para heredar tenant
        evaluacion = repo.get_evaluacion(db, data["evaluacion_id"])
        
        if tenant_id:
            data["tenant_id"] = tenant_id
        elif evaluacion:
            data["tenant_id"] = evaluacion.tenant_id
        
        # Crear pregunta
        obj = repo.create_pregunta(db, data)
        
        # Crear opciones
        for opcion in opciones:
            repo.create_opcion(
                db,
                {
                    **opcion,
                    "pregunta_id": obj.id,
                    "tenant_id": obj.tenant_id
                }
            )
        
        # Actualizar evaluación
        if evaluacion:
            evaluacion.actualizado_por = actor_key
            evaluacion.actualizado_en = datetime.utcnow()
        
        # Registrar evento de auditoría
        registrar_evento(
            db,
            "evaluacion",
            obj.evaluacion_id,
            "question_created",
            actor_key=actor_key,
            actor_nombre=actor_name,
            tenant_id=obj.tenant_id,
            detalle={
                "pregunta_id": obj.id,
                "enunciado": obj.enunciado
            }
        )
        
        db.commit()
        db.refresh(obj)
        
        return _pregunta_dict(obj, incluir_correctas=True)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def delete_pregunta(
    pregunta_id: int,
    tenant_id: Optional[str] = None,
    actor_key: Optional[str] = None,
    actor_name: Optional[str] = None
) -> bool:
    """
    Elimina una pregunta.
    
    Args:
        pregunta_id: ID de la pregunta
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
        # Obtener pregunta antes de eliminar
        obj = repo.get_pregunta(db, pregunta_id)
        
        if obj:
            # Actualizar evaluación
            evaluacion = repo.get_evaluacion(db, obj.evaluacion_id)
            if evaluacion:
                evaluacion.actualizado_por = actor_key
                evaluacion.actualizado_en = datetime.utcnow()
            
            # Registrar evento de auditoría
            registrar_evento(
                db,
                "evaluacion",
                obj.evaluacion_id,
                "question_deleted",
                actor_key=actor_key,
                actor_nombre=actor_name,
                tenant_id=obj.tenant_id,
                detalle={
                    "pregunta_id": obj.id,
                    "enunciado": obj.enunciado
                }
            )
        
        # Eliminar pregunta
        ok = repo.delete_pregunta(db, pregunta_id)
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
# SERVICIOS DE INTENTOS DE EVALUACIÓN
# ============================================================================

def iniciar_intento(
    inscripcion_id: int,
    evaluacion_id: int,
    tenant_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Inicia un nuevo intento de evaluación.
    
    Args:
        inscripcion_id: ID de la inscripción
        evaluacion_id: ID de la evaluación
        tenant_id: ID del tenant
        
    Returns:
        Diccionario con datos del intento y preguntas
        
    Raises:
        ValueError: Si la evaluación/inscripción no existe o se agotaron intentos
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        # Validar evaluación
        evaluacion = repo.get_evaluacion(db, evaluacion_id)
        if not evaluacion:
            raise ValueError("Evaluación no encontrada")
        
        # Validar inscripción
        insc = repo.get_inscripcion(db, inscripcion_id)
        if not insc:
            raise ValueError("Inscripción no encontrada")
        
        # Validar que la inscripción corresponde al curso
        if insc.curso_id != evaluacion.curso_id:
            raise ValueError(
                "La inscripción no corresponde al curso de esta evaluación"
            )
        
        # Validar intentos disponibles
        intentos_previos = repo.count_intentos(db, inscripcion_id, evaluacion_id)
        if intentos_previos >= evaluacion.max_intentos:
            raise ValueError(
                f"Se han agotado los {evaluacion.max_intentos} intentos permitidos"
            )
        
        # Seleccionar preguntas
        preguntas = list(evaluacion.preguntas)
        
        if (evaluacion.preguntas_por_intento and 
            evaluacion.preguntas_por_intento < len(preguntas)):
            # Seleccionar muestra aleatoria
            preguntas = random.sample(preguntas, evaluacion.preguntas_por_intento)
        else:
            # Mezclar todas las preguntas
            random.shuffle(preguntas)
        
        # Crear intento
        intento = repo.create_intento(
            db,
            {
                "inscripcion_id": inscripcion_id,
                "evaluacion_id": evaluacion_id,
                "numero_intento": intentos_previos + 1,
                "fecha_inicio": datetime.utcnow(),
                "tenant_id": tenant_id or getattr(insc, "tenant_id", None)
            }
        )
        
        db.commit()
        db.refresh(intento)
        
        return {
            "intento_id": intento.id,
            "numero_intento": intento.numero_intento,
            "max_intentos": evaluacion.max_intentos,
            "tiempo_limite_min": evaluacion.tiempo_limite_min,
            "preguntas": [_pregunta_dict(item, False) for item in preguntas],
        }
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def enviar_respuestas(
    intento_id: int,
    respuestas: Optional[Dict[str, Any]] = None,
    tenant_id: Optional[str] = None,
    actor_key: Optional[str] = None,
    actor_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Envía y califica las respuestas de un intento de evaluación.
    
    Args:
        intento_id: ID del intento
        respuestas: Diccionario con respuestas {pregunta_id: opcion_id}
        tenant_id: ID del tenant
        actor_key: Identificador del actor
        actor_name: Nombre del actor
        
    Returns:
        Diccionario con resultados del intento
        
    Raises:
        ValueError: Si el intento no existe o ya fue calificado
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        respuestas = respuestas or {}
        
        # Validar intento
        intento = repo.get_intento(db, intento_id)
        if not intento:
            raise ValueError("Intento no encontrado")
        
        if intento.fecha_fin:
            raise ValueError("Este intento ya fue calificado")
        
        # Obtener evaluación
        evaluacion = repo.get_evaluacion(db, intento.evaluacion_id)
        
        # Calificar respuestas
        puntaje_obtenido = 0.0
        puntaje_maximo = 0.0
        
        for pregunta in evaluacion.preguntas:
            puntaje_maximo += pregunta.puntaje
            
            # Obtener respuesta del usuario
            clave = str(pregunta.id)
            if clave not in respuestas:
                continue
            
            resp = respuestas[clave]
            
            # Validar respuesta según tipo de pregunta
            if pregunta.tipo in ("opcion_multiple", "verdadero_falso"):
                try:
                    opcion_id = int(resp)
                except (TypeError, ValueError):
                    continue
                
                # Buscar opción seleccionada
                opcion = next(
                    (item for item in pregunta.opciones if item.id == opcion_id),
                    None
                )
                
                # Sumar puntaje si es correcta
                if opcion and opcion.es_correcta:
                    puntaje_obtenido += pregunta.puntaje
        
        # Calcular porcentaje y aprobación
        pct = round(
            (puntaje_obtenido / puntaje_maximo) * 100, 
            2
        ) if puntaje_maximo else 0.0
        
        aprobado = pct >= evaluacion.puntaje_minimo
        
        # Actualizar intento
        intento.puntaje = pct
        intento.puntaje_maximo = puntaje_maximo
        intento.aprobado = aprobado
        intento.respuestas_json = json.dumps(respuestas)
        intento.fecha_fin = datetime.utcnow()
        
        # Actualizar inscripción
        insc = repo.get_inscripcion(db, intento.inscripcion_id)
        estado_previo = insc.estado if insc else None
        cert_previo = insc.certificado is not None if insc else False
        
        if insc and aprobado:
            # Actualizar mejor puntaje
            if insc.puntaje_final is None or pct > insc.puntaje_final:
                insc.puntaje_final = pct
            
            insc.aprobado = True
            
            # Marcar como completado si tiene 100% de avance
            if insc.pct_avance >= 100:
                insc.estado = "completado"
                insc.fecha_completado = insc.fecha_completado or datetime.utcnow()
                
                # Emitir certificado
                emitir_certificado(
                    db,
                    insc,
                    pct,
                    actor_key=actor_key or insc.colaborador_key,
                    actor_name=actor_name,
                    tenant_id=tenant_id or getattr(insc, "tenant_id", None)
                )
        
        elif insc and not aprobado:
            # Verificar si se agotaron todos los intentos
            total_intentos = repo.count_intentos(db, insc.id, evaluacion.id)
            
            if total_intentos >= evaluacion.max_intentos:
                # Verificar si todos los intentos fallaron
                intentos_previos = repo.list_intentos(db, insc.id, evaluacion.id)
                all_failed = not any(
                    item.aprobado 
                    for item in intentos_previos 
                    if item.id != intento.id
                )
                
                if all_failed:
                    insc.estado = "reprobado"
        
        db.commit()
        
        # Otorgar gamificación
        if insc:
            try:
                from fastapi_modulo.modulos.capacitacion.servicios.gamificacion_service import (
                    check_y_otorgar_insignias,
                    otorgar_puntos
                )
                
                # Puntos por aprobar evaluación
                if aprobado:
                    otorgar_puntos(
                        insc.colaborador_key,
                        "evaluacion_aprobada",
                        30,
                        "evaluacion",
                        evaluacion.id
                    )
                
                # Puntos extra por aprobar en primer intento
                if aprobado and intento.numero_intento == 1:
                    otorgar_puntos(
                        insc.colaborador_key,
                        "aprobado_primer_intento",
                        40,
                        "evaluacion",
                        evaluacion.id
                    )
                
                # Puntos por evaluación perfecta
                if pct >= 100.0 and aprobado:
                    otorgar_puntos(
                        insc.colaborador_key,
                        "evaluacion_perfecta",
                        50,
                        "evaluacion_perfecta",
                        evaluacion.id
                    )
                
                # Puntos por completar curso
                if estado_previo != "completado" and insc.estado == "completado":
                    otorgar_puntos(
                        insc.colaborador_key,
                        "curso_completado",
                        50,
                        "curso",
                        insc.curso_id
                    )
                
                # Puntos por obtener certificado
                if not cert_previo and insc.certificado:
                    otorgar_puntos(
                        insc.colaborador_key,
                        "certificado_obtenido",
                        100,
                        "certificado",
                        insc.certificado.id
                    )
                
                # Verificar insignias
                check_y_otorgar_insignias(insc.colaborador_key)
            except Exception:
                # No fallar si hay error en gamificación
                pass
        
        return {
            "intento_id": intento.id,
            "puntaje": pct,
            "puntaje_maximo": puntaje_maximo,
            "aprobado": aprobado,
            "puntaje_minimo_aprobacion": evaluacion.puntaje_minimo,
            "certificado": (
                cert_dict(insc.certificado) 
                if insc and insc.certificado 
                else None
            ),
        }
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def list_intentos(
    inscripcion_id: int,
    evaluacion_id: Optional[int] = None,
    tenant_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Lista los intentos de evaluación de una inscripción.
    
    Args:
        inscripcion_id: ID de la inscripción
        evaluacion_id: ID de la evaluación (opcional)
        tenant_id: ID del tenant
        
    Returns:
        Lista de intentos como diccionarios
    """
    db = repo.get_db()
    try:
        intentos = repo.list_intentos(db, inscripcion_id, evaluacion_id)
        return [_intento_dict(item) for item in intentos]
    finally:
        db.close()


def get_intento(
    intento_id: int,
    tenant_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Obtiene un intento de evaluación por ID.
    
    Args:
        intento_id: ID del intento
        tenant_id: ID del tenant
        
    Returns:
        Diccionario con datos del intento o None
    """
    db = repo.get_db()
    try:
        obj = repo.get_intento(db, intento_id)
        return _intento_dict(obj) if obj else None
    finally:
        db.close()
        