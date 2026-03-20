"""
Tareas asíncronas con Celery para el módulo de capacitación.

Este módulo contiene todas las tareas programadas y asíncronas:
- Envío de notificaciones y recordatorios
- Generación de reportes
- Procesamiento de inscripciones masivas
- Limpieza y mantenimiento de datos
- Sincronización con sistemas externos
- Generación de certificados
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from celery import shared_task
from sqlalchemy.exc import SQLAlchemyError

from fastapi_modulo.modulos.capacitacion.repositorios import (
    cursos_repository,
    inscripciones_repository,
    evaluaciones_repository
)
from fastapi_modulo.modulos.capacitacion.servicios import (
    inscripciones_service,
    certificados_service,
    cursos_service
)
from fastapi_modulo.modulos.capacitacion.servicios.utils import (
    datetime_to_iso,
    generate_folio
)


# Configurar logger
logger = logging.getLogger(__name__)


# ============================================================================
# TAREAS DE RECORDATORIOS Y NOTIFICACIONES
# ============================================================================

@shared_task(
    name="capacitacion.enviar_recordatorios_vencimiento",
    bind=True,
    max_retries=3,
    default_retry_delay=300
)
def enviar_recordatorios_vencimiento(self) -> Dict[str, Any]:
    """
    Envía recordatorios a colaboradores con cursos próximos a vencer.
    
    Esta tarea se ejecuta diariamente y:
    1. Identifica inscripciones con fecha de vencimiento cercana
    2. Verifica que no se haya enviado recordatorio recientemente
    3. Envía notificaciones según configuración del curso
    
    Returns:
        Diccionario con estadísticas de envío
    """
    try:
        logger.info("Iniciando envío de recordatorios de vencimiento")
        
        # Ejecutar operación de cursos (recordatorios y reinscripciones)
        resultado = inscripciones_service.ejecutar_operacion_cursos()
        
        recordatorios = resultado.get("recordatorios", [])
        reinscripciones = resultado.get("reinscripciones", 0)
        
        # Aquí se integraría con el sistema de notificaciones
        # Por ahora solo registramos
        for recordatorio in recordatorios:
            logger.info(
                f"Recordatorio enviado - Inscripción: {recordatorio['inscripcion_id']}, "
                f"Curso: {recordatorio['curso_id']}, "
                f"Vence en: {recordatorio['vence_en_dias']} días"
            )
        
        logger.info(
            f"Recordatorios enviados: {len(recordatorios)}, "
            f"Reinscripciones: {reinscripciones}"
        )
        
        return {
            "success": True,
            "recordatorios_enviados": len(recordatorios),
            "reinscripciones_realizadas": reinscripciones,
            "timestamp": datetime_to_iso(datetime.utcnow())
        }
        
    except Exception as exc:
        logger.error(f"Error al enviar recordatorios: {exc}")
        raise self.retry(exc=exc)


@shared_task(
    name="capacitacion.notificar_curso_disponible",
    bind=True,
    max_retries=3
)
def notificar_curso_disponible(
    curso_id: int,
    colaboradores: List[str]
) -> Dict[str, Any]:
    """
    Notifica a colaboradores sobre un curso recién disponible.
    
    Args:
        curso_id: ID del curso
        colaboradores: Lista de claves de colaboradores
        
    Returns:
        Diccionario con resultado del envío
    """
    try:
        logger.info(
            f"Notificando curso {curso_id} a {len(colaboradores)} colaboradores"
        )
        
        # Obtener información del curso
        curso = cursos_service.get_curso(curso_id)
        
        if not curso:
            logger.warning(f"Curso {curso_id} no encontrado")
            return {"success": False, "error": "Curso no encontrado"}
        
        # Aquí se integraría con el sistema de notificaciones
        # Por ejemplo: enviar emails, push notifications, etc.
        notificaciones_enviadas = 0
        
        for colaborador_key in colaboradores:
            # Simular envío de notificación
            logger.info(
                f"Notificación enviada a {colaborador_key} sobre curso '{curso['nombre']}'"
            )
            notificaciones_enviadas += 1
        
        return {
            "success": True,
            "curso_id": curso_id,
            "notificaciones_enviadas": notificaciones_enviadas,
            "timestamp": datetime_to_iso(datetime.utcnow())
        }
        
    except Exception as exc:
        logger.error(f"Error al notificar curso disponible: {exc}")
        raise self.retry(exc=exc)


# ============================================================================
# TAREAS DE INSCRIPCIONES
# ============================================================================

@shared_task(
    name="capacitacion.procesar_inscripciones_masivas",
    bind=True,
    max_retries=3
)
def procesar_inscripciones_masivas(
    curso_id: int,
    colaboradores: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Procesa inscripciones masivas de colaboradores a un curso.
    
    Args:
        curso_id: ID del curso
        colaboradores: Lista de datos de colaboradores
        
    Returns:
        Diccionario con estadísticas del procesamiento
    """
    try:
        logger.info(
            f"Procesando inscripciones masivas - Curso: {curso_id}, "
            f"Colaboradores: {len(colaboradores)}"
        )
        
        resultado = inscripciones_service.inscribir_masivo(curso_id, colaboradores)
        
        logger.info(
            f"Inscripciones procesadas - Creados: {resultado['creados']}, "
            f"Ya inscritos: {resultado['ya_inscritos']}, "
            f"Errores: {resultado['errores']}"
        )
        
        return {
            "success": True,
            "curso_id": curso_id,
            **resultado,
            "timestamp": datetime_to_iso(datetime.utcnow())
        }
        
    except Exception as exc:
        logger.error(f"Error al procesar inscripciones masivas: {exc}")
        raise self.retry(exc=exc)


@shared_task(
    name="capacitacion.asignar_cursos_por_reglas",
    bind=True,
    max_retries=3
)
def asignar_cursos_por_reglas(curso_id: int) -> Dict[str, Any]:
    """
    Asigna automáticamente un curso a colaboradores que cumplen las reglas.
    
    Args:
        curso_id: ID del curso
        
    Returns:
        Diccionario con estadísticas de asignación
    """
    try:
        logger.info(f"Asignando curso {curso_id} por reglas automáticas")
        
        resultado = inscripciones_service.asignar_por_reglas(curso_id)
        
        logger.info(
            f"Asignación completada - Creados: {resultado['creados']}, "
            f"Ya inscritos: {resultado['ya_inscritos']}, "
            f"Errores: {resultado['errores']}"
        )
        
        return {
            "success": True,
            "curso_id": curso_id,
            **resultado,
            "timestamp": datetime_to_iso(datetime.utcnow())
        }
        
    except Exception as exc:
        logger.error(f"Error al asignar cursos por reglas: {exc}")
        raise self.retry(exc=exc)


# ============================================================================
# TAREAS DE CERTIFICADOS
# ============================================================================

@shared_task(
    name="capacitacion.generar_certificado_pdf",
    bind=True,
    max_retries=3
)
def generar_certificado_pdf(
    certificado_id: int,
    template: str = "default"
) -> Dict[str, Any]:
    """
    Genera el PDF de un certificado.
    
    Args:
        certificado_id: ID del certificado
        template: Plantilla a usar para el PDF
        
    Returns:
        Diccionario con URL del PDF generado
    """
    try:
        logger.info(f"Generando PDF para certificado {certificado_id}")
        
        # Obtener certificado
        certificado = certificados_service.get_certificado(certificado_id)
        
        if not certificado:
            logger.warning(f"Certificado {certificado_id} no encontrado")
            return {"success": False, "error": "Certificado no encontrado"}
        
        # Aquí iría la lógica real de generación de PDF
        # Por ejemplo, usando ReportLab, WeasyPrint, o una API externa
        
        # Simular generación de PDF
        pdf_url = f"https://storage.example.com/certificados/{certificado['folio']}.pdf"
        
        # Actualizar URL del PDF en el certificado
        certificados_service.actualizar_url_pdf_certificado(
            certificado_id,
            pdf_url
        )
        
        logger.info(f"PDF generado exitosamente: {pdf_url}")
        
        return {
            "success": True,
            "certificado_id": certificado_id,
            "pdf_url": pdf_url,
            "timestamp": datetime_to_iso(datetime.utcnow())
        }
        
    except Exception as exc:
        logger.error(f"Error al generar PDF de certificado: {exc}")
        raise self.retry(exc=exc)


@shared_task(
    name="capacitacion.regenerar_certificados_lote",
    bind=True
)
def regenerar_certificados_lote(
    certificado_ids: List[int]
) -> Dict[str, Any]:
    """
    Regenera múltiples certificados en lote.
    
    Args:
        certificado_ids: Lista de IDs de certificados
        
    Returns:
        Diccionario con estadísticas de regeneración
    """
    try:
        logger.info(f"Regenerando {len(certificado_ids)} certificados")
        
        exitosos = 0
        fallidos = 0
        
        for cert_id in certificado_ids:
            try:
                # Regenerar certificado
                certificados_service.regenerar_certificado(cert_id)
                
                # Generar PDF
                generar_certificado_pdf.delay(cert_id)
                
                exitosos += 1
                
            except Exception as e:
                logger.error(f"Error al regenerar certificado {cert_id}: {e}")
                fallidos += 1
        
        return {
            "success": True,
            "total": len(certificado_ids),
            "exitosos": exitosos,
            "fallidos": fallidos,
            "timestamp": datetime_to_iso(datetime.utcnow())
        }
        
    except Exception as exc:
        logger.error(f"Error al regenerar certificados en lote: {exc}")
        raise


# ============================================================================
# TAREAS DE REPORTES
# ============================================================================

@shared_task(
    name="capacitacion.generar_reporte_mensual",
    bind=True
)
def generar_reporte_mensual(
    mes: int,
    anio: int,
    tenant_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Genera un reporte mensual de actividad de capacitación.
    
    Args:
        mes: Mes del reporte (1-12)
        anio: Año del reporte
        tenant_id: ID del tenant
        
    Returns:
        Diccionario con datos del reporte
    """
    try:
        logger.info(f"Generando reporte mensual - {mes}/{anio}")
        
        # Calcular fechas del periodo
        fecha_inicio = datetime(anio, mes, 1)
        
        if mes == 12:
            fecha_fin = datetime(anio + 1, 1, 1) - timedelta(days=1)
        else:
            fecha_fin = datetime(anio, mes + 1, 1) - timedelta(days=1)
        
        # Obtener estadísticas del dashboard
        stats = inscripciones_service.get_dashboard_stats()
        
        # Aquí se generaría un reporte más completo
        # Por ejemplo, exportar a Excel, PDF, etc.
        
        reporte = {
            "periodo": f"{mes:02d}/{anio}",
            "fecha_inicio": datetime_to_iso(fecha_inicio),
            "fecha_fin": datetime_to_iso(fecha_fin),
            "estadisticas": stats,
            "generado_en": datetime_to_iso(datetime.utcnow())
        }
        
        logger.info("Reporte mensual generado exitosamente")
        
        return {
            "success": True,
            "reporte": reporte,
            "timestamp": datetime_to_iso(datetime.utcnow())
        }
        
    except Exception as exc:
        logger.error(f"Error al generar reporte mensual: {exc}")
        raise


@shared_task(
    name="capacitacion.exportar_datos_curso",
    bind=True,
    max_retries=3
)
def exportar_datos_curso(
    curso_id: int,
    formato: str = "xlsx"
) -> Dict[str, Any]:
    """
    Exporta los datos de un curso a un archivo.
    
    Args:
        curso_id: ID del curso
        formato: Formato de exportación (xlsx, csv, pdf)
        
    Returns:
        Diccionario con URL del archivo exportado
    """
    try:
        logger.info(f"Exportando datos del curso {curso_id} a formato {formato}")
        
        # Obtener datos del curso
        curso = cursos_service.get_curso(curso_id, with_lecciones=True)
        
        if not curso:
            return {"success": False, "error": "Curso no encontrado"}
        
        # Obtener inscripciones
        inscripciones = inscripciones_service.list_inscripciones(curso_id=curso_id)
        
        # Aquí iría la lógica de exportación
        # Por ejemplo, usando openpyxl para Excel, csv para CSV, etc.
        
        # Simular exportación
        export_url = f"https://storage.example.com/exports/curso_{curso_id}.{formato}"
        
        logger.info(f"Exportación completada: {export_url}")
        
        return {
            "success": True,
            "curso_id": curso_id,
            "formato": formato,
            "export_url": export_url,
            "total_inscripciones": len(inscripciones),
            "timestamp": datetime_to_iso(datetime.utcnow())
        }
        
    except Exception as exc:
        logger.error(f"Error al exportar datos del curso: {exc}")
        raise self.retry(exc=exc)


# ============================================================================
# TAREAS DE LIMPIEZA Y MANTENIMIENTO
# ============================================================================

@shared_task(name="capacitacion.limpiar_sesiones_expiradas")
def limpiar_sesiones_expiradas() -> Dict[str, Any]:
    """
    Limpia sesiones y tokens expirados.
    
    Returns:
        Diccionario con estadísticas de limpieza
    """
    try:
        logger.info("Limpiando sesiones expiradas")
        
        # Aquí iría la lógica de limpieza
        # Por ejemplo, eliminar tokens JWT expirados, sesiones antiguas, etc.
        
        sesiones_eliminadas = 0
        
        logger.info(f"Limpieza completada - {sesiones_eliminadas} sesiones eliminadas")
        
        return {
            "success": True,
            "sesiones_eliminadas": sesiones_eliminadas,
            "timestamp": datetime_to_iso(datetime.utcnow())
        }
        
    except Exception as exc:
        logger.error(f"Error al limpiar sesiones: {exc}")
        raise


@shared_task(name="capacitacion.limpiar_archivos_temporales")
def limpiar_archivos_temporales(dias_antiguedad: int = 7) -> Dict[str, Any]:
    """
    Limpia archivos temporales antiguos.
    
    Args:
        dias_antiguedad: Días de antigüedad para considerar archivo como temporal
        
    Returns:
        Diccionario con estadísticas de limpieza
    """
    try:
        logger.info(f"Limpiando archivos temporales (>{dias_antiguedad} días)")
        
        # Aquí iría la lógica de limpieza de archivos
        # Por ejemplo, eliminar archivos en /tmp, uploads temporales, etc.
        
        archivos_eliminados = 0
        espacio_liberado_mb = 0
        
        logger.info(
            f"Limpieza completada - {archivos_eliminados} archivos, "
            f"{espacio_liberado_mb} MB liberados"
        )
        
        return {
            "success": True,
            "archivos_eliminados": archivos_eliminados,
            "espacio_liberado_mb": espacio_liberado_mb,
            "timestamp": datetime_to_iso(datetime.utcnow())
        }
        
    except Exception as exc:
        logger.error(f"Error al limpiar archivos temporales: {exc}")
        raise


@shared_task(name="capacitacion.archivar_cursos_antiguos")
def archivar_cursos_antiguos(dias_inactividad: int = 180) -> Dict[str, Any]:
    """
    Archiva cursos sin actividad reciente.
    
    Args:
        dias_inactividad: Días de inactividad para archivar
        
    Returns:
        Diccionario con estadísticas de archivado
    """
    try:
        logger.info(f"Archivando cursos con >{dias_inactividad} días de inactividad")
        
        fecha_limite = datetime.utcnow() - timedelta(days=dias_inactividad)
        
        # Aquí iría la lógica de archivado
        # Por ejemplo, cambiar estado de cursos sin inscripciones recientes
        
        cursos_archivados = 0
        
        logger.info(f"Archivado completado - {cursos_archivados} cursos archivados")
        
        return {
            "success": True,
            "cursos_archivados": cursos_archivados,
            "fecha_limite": datetime_to_iso(fecha_limite),
            "timestamp": datetime_to_iso(datetime.utcnow())
        }
        
    except Exception as exc:
        logger.error(f"Error al archivar cursos: {exc}")
        raise


# ============================================================================
# TAREAS DE SINCRONIZACIÓN
# ============================================================================

@shared_task(
    name="capacitacion.sincronizar_colaboradores",
    bind=True,
    max_retries=3
)
def sincronizar_colaboradores(self, origen: str = "hr_system") -> Dict[str, Any]:
    """
    Sincroniza datos de colaboradores desde sistema externo.
    
    Args:
        origen: Sistema origen de datos (hr_system, active_directory, etc.)
        
    Returns:
        Diccionario con estadísticas de sincronización
    """
    try:
        logger.info(f"Sincronizando colaboradores desde {origen}")
        
        # Aquí iría la lógica de sincronización
        # Por ejemplo, consultar API de HR, LDAP, etc.
        
        colaboradores_actualizados = 0
        colaboradores_nuevos = 0
        errores = 0
        
        logger.info(
            f"Sincronización completada - "
            f"Nuevos: {colaboradores_nuevos}, "
            f"Actualizados: {colaboradores_actualizados}, "
            f"Errores: {errores}"
        )
        
        return {
            "success": True,
            "origen": origen,
            "colaboradores_nuevos": colaboradores_nuevos,
            "colaboradores_actualizados": colaboradores_actualizados,
            "errores": errores,
            "timestamp": datetime_to_iso(datetime.utcnow())
        }
        
    except Exception as exc:
        logger.error(f"Error al sincronizar colaboradores: {exc}")
        raise self.retry(exc=exc)


@shared_task(
    name="capacitacion.sincronizar_con_lms_externo",
    bind=True,
    max_retries=3
)
def sincronizar_con_lms_externo(
    lms_name: str,
    operacion: str = "pull"
) -> Dict[str, Any]:
    """
    Sincroniza datos con un LMS externo.
    
    Args:
        lms_name: Nombre del LMS (moodle, blackboard, canvas, etc.)
        operacion: Tipo de operación (pull, push, sync)
        
    Returns:
        Diccionario con estadísticas de sincronización
    """
    try:
        logger.info(f"Sincronizando con LMS {lms_name} - Operación: {operacion}")
        
        # Aquí iría la lógica de sincronización con LMS externo
        # Por ejemplo, API de Moodle, Canvas, Blackboard, etc.
        
        cursos_sincronizados = 0
        inscripciones_sincronizadas = 0
        
        logger.info(
            f"Sincronización con LMS completada - "
            f"Cursos: {cursos_sincronizados}, "
            f"Inscripciones: {inscripciones_sincronizadas}"
        )
        
        return {
            "success": True,
            "lms_name": lms_name,
            "operacion": operacion,
            "cursos_sincronizados": cursos_sincronizados,
            "inscripciones_sincronizadas": inscripciones_sincronizadas,
            "timestamp": datetime_to_iso(datetime.utcnow())
        }
        
    except Exception as exc:
        logger.error(f"Error al sincronizar con LMS: {exc}")
        raise self.retry(exc=exc)


# ============================================================================
# TAREAS DE ANÁLISIS Y MÉTRICAS
# ============================================================================

@shared_task(name="capacitacion.calcular_metricas_diarias")
def calcular_metricas_diarias() -> Dict[str, Any]:
    """
    Calcula y almacena métricas diarias del sistema.
    
    Returns:
        Diccionario con métricas calculadas
    """
    try:
        logger.info("Calculando métricas diarias")
        
        # Obtener estadísticas
        stats = inscripciones_service.get_dashboard_stats()
        
        # Aquí se almacenarían las métricas en una tabla histórica
        # para análisis de tendencias
        
        metricas = {
            "fecha": datetime_to_iso(datetime.utcnow().date()),
            "total_inscripciones": stats.get("total_inscripciones", 0),
            "tasa_completado": stats.get("tasa_completado", 0),
            "tasa_aprobacion": stats.get("tasa_aprobacion", 0),
            "certificados_emitidos": stats.get("certificados_emitidos", 0),
            "colaboradores_activos": stats.get("colaboradores_unicos", 0),
        }
        
        logger.info("Métricas diarias calculadas exitosamente")
        
        return {
            "success": True,
            "metricas": metricas,
            "timestamp": datetime_to_iso(datetime.utcnow())
        }
        
    except Exception as exc:
        logger.error(f"Error al calcular métricas diarias: {exc}")
        raise


@shared_task(name="capacitacion.detectar_anomalias")
def detectar_anomalias() -> Dict[str, Any]:
    """
    Detecta anomalías en el sistema de capacitación.
    
    Detecta:
    - Cursos con tasas de reprobación anormalmente altas
    - Inscripciones sospechosas
    - Patrones de fraude en evaluaciones
    
    Returns:
        Diccionario con anomalías detectadas
    """
    try:
        logger.info("Detectando anomalías en el sistema")
        
        anomalias = []
        
        # Aquí iría la lógica de detección de anomalías
        # Por ejemplo, usando ML, reglas estadísticas, etc.
        
        # Detectar cursos con alta tasa de reprobación
        stats = inscripciones_service.get_dashboard_stats()
        cursos_problema = stats.get("cursos_peor_aprobacion", [])
        
        for curso in cursos_problema[:3]:  # Top 3 peores
            if curso.get("tasa_aprobacion", 100) < 30:
                anomalias.append({
                    "tipo": "tasa_aprobacion_baja",
                    "curso_id": curso.get("curso_id"),
                    "curso_nombre": curso.get("nombre"),
                    "tasa_aprobacion": curso.get("tasa_aprobacion"),
                    "severidad": "alta"
                })
        
        logger.info(f"Detección completada - {len(anomalias)} anomalías encontradas")
        
        return {
            "success": True,
            "anomalias": anomalias,
            "total_anomalias": len(anomalias),
            "timestamp": datetime_to_iso(datetime.utcnow())
        }
        
    except Exception as exc:
        logger.error(f"Error al detectar anomalías: {exc}")
        raise


# ============================================================================
# TAREAS PROGRAMADAS (Beat Schedule)
# ============================================================================

# Configuración de tareas programadas para Celery Beat
CELERY_BEAT_SCHEDULE = {
    # Diarias
    "enviar-recordatorios-diarios": {
        "task": "capacitacion.enviar_recordatorios_vencimiento",
        "schedule": 86400.0,  # 24 horas
        "options": {"expires": 3600}
    },
    "calcular-metricas-diarias": {
        "task": "capacitacion.calcular_metricas_diarias",
        "schedule": 86400.0,  # 24 horas
        "options": {"expires": 3600}
    },
    "limpiar-archivos-temporales": {
        "task": "capacitacion.limpiar_archivos_temporales",
        "schedule": 86400.0,  # 24 horas
        "options": {"expires": 3600}
    },
    
    # Semanales
    "detectar-anomalias-semanales": {
        "task": "capacitacion.detectar_anomalias",
        "schedule": 604800.0,  # 7 días
        "options": {"expires": 7200}
    },
    "archivar-cursos-antiguos": {
        "task": "capacitacion.archivar_cursos_antiguos",
        "schedule": 604800.0,  # 7 días
        "options": {"expires": 7200}
    },
    
    # Mensuales
    "generar-reporte-mensual": {
        "task": "capacitacion.generar_reporte_mensual",
        "schedule": 2592000.0,  # 30 días (aproximado)
        "options": {"expires": 86400}
    },
    
    # Cada hora
    "limpiar-sesiones-expiradas": {
        "task": "capacitacion.limpiar_sesiones_expiradas",
        "schedule": 3600.0,  # 1 hora
        "options": {"expires": 900}
    },
}


# ============================================================================
# UTILIDADES PARA TAREAS
# ============================================================================

def schedule_task_at(
    task_func: callable,
    run_at: datetime,
    *args,
    **kwargs
) -> Any:
    """
    Programa una tarea para ejecutarse en una fecha/hora específica.
    
    Args:
        task_func: Función de tarea de Celery
        run_at: Fecha/hora de ejecución
        *args: Argumentos posicionales para la tarea
        **kwargs: Argumentos nombrados para la tarea
        
    Returns:
        Resultado de apply_async
    
    Examples:
        >>> from datetime import datetime, timedelta
        >>> run_time = datetime.utcnow() + timedelta(hours=2)
        >>> schedule_task_at(enviar_recordatorios_vencimiento, run_time)
    """
    eta = run_at if isinstance(run_at, datetime) else datetime.fromisoformat(run_at)
    
    return task_func.apply_async(args=args, kwargs=kwargs, eta=eta)


def cancel_scheduled_task(task_id: str) -> bool:
    """
    Cancela una tarea programada.
    
    Args:
        task_id: ID de la tarea a cancelar
        
    Returns:
        True si se canceló exitosamente
    """
    from celery.result import AsyncResult
    
    result = AsyncResult(task_id)
    result.revoke(terminate=True)
    
    return True


def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Obtiene el estado de una tarea.
    
    Args:
        task_id: ID de la tarea
        
    Returns:
        Diccionario con estado de la tarea
    """
    from celery.result import AsyncResult
    
    result = AsyncResult(task_id)
    
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
        "traceback": result.traceback if result.failed() else None
    }
    