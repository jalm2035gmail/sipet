from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from fastapi_modulo.modulos.capacitacion.modelos.db_models import (
    CapCertificado,
    CapInscripcion
)
from fastapi_modulo.modulos.capacitacion.repositorios import evaluaciones_repository as repo
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
    return value.isoformat() if isinstance(value, datetime) else str(value)


# ============================================================================
# FUNCIONES DE SERIALIZACIÓN DE MODELOS
# ============================================================================

def cert_dict(obj: CapCertificado) -> Dict[str, Any]:
    """
    Convierte un objeto CapCertificado a diccionario.
    
    Args:
        obj: Objeto CapCertificado
        
    Returns:
        Diccionario con datos del certificado
    """
    insc = obj.inscripcion
    
    return {
        "id": obj.id,
        "folio": obj.folio,
        "puntaje_final": obj.puntaje_final,
        "creado_por": obj.creado_por,
        "fecha_emision": _dt(obj.fecha_emision),
        "url_pdf": obj.url_pdf,
        "inscripcion_id": obj.inscripcion_id,
        "colaborador_key": insc.colaborador_key if insc else None,
        "colaborador_nombre": insc.colaborador_nombre if insc else None,
        "curso_id": insc.curso_id if insc else None,
        "curso_nombre": insc.curso.nombre if insc and insc.curso else None,
    }


# ============================================================================
# SERVICIOS DE CERTIFICADOS
# ============================================================================

def emitir_certificado(
    db: Session,
    insc: CapInscripcion,
    puntaje: float,
    actor_key: Optional[str] = None,
    actor_name: Optional[str] = None,
    tenant_id: Optional[str] = None
) -> CapCertificado:
    """
    Emite un certificado para una inscripción aprobada.
    
    Args:
        db: Sesión de base de datos
        insc: Objeto CapInscripcion
        puntaje: Puntaje final obtenido
        actor_key: Identificador del actor
        actor_name: Nombre del actor
        tenant_id: ID del tenant
        
    Returns:
        Objeto CapCertificado creado
        
    Raises:
        ValueError: Si no cumple requisitos para emitir certificado
        SQLAlchemyError: Si hay error en la base de datos
    """
    # Verificar si ya existe certificado
    if insc.certificado:
        return insc.certificado
    
    # Validar que esté aprobado
    if not getattr(insc, "aprobado", False):
        raise ValueError(
            "La inscripción debe estar aprobada para emitir certificado"
        )
    
    # Validar que tenga 100% de avance
    pct_avance = float(getattr(insc, "pct_avance", 0) or 0)
    if pct_avance < 100:
        raise ValueError(
            "La inscripción debe completar el 100% del curso para emitir certificado"
        )
    
    # Validar encuesta de satisfacción si es requerida
    if insc.curso and getattr(insc.curso, "bloquear_certificado_encuesta", False):
        if not getattr(insc, "satisfaccion", None):
            raise ValueError(
                "Debe completar la encuesta de satisfacción para emitir certificado"
            )
    
    # Generar folio único
    folio = uuid.uuid4().hex[:12].upper()
    
    # Crear certificado
    certificado = repo.create_certificado(
        db,
        {
            "inscripcion_id": insc.id,
            "folio": folio,
            "puntaje_final": puntaje,
            "creado_por": actor_key,
            "fecha_emision": datetime.utcnow(),
            "tenant_id": tenant_id or getattr(insc, "tenant_id", "default")
        }
    )
    
    # Registrar evento de auditoría
    registrar_evento(
        db,
        "certificado",
        certificado.id,
        "issued",
        actor_key=actor_key,
        actor_nombre=actor_name,
        tenant_id=certificado.tenant_id,
        detalle={
            "inscripcion_id": insc.id,
            "curso_id": insc.curso_id,
            "folio": certificado.folio
        }
    )
    
    return certificado


def get_certificado(
    cert_id: int,
    tenant_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Obtiene un certificado por ID.
    
    Args:
        cert_id: ID del certificado
        tenant_id: ID del tenant
        
    Returns:
        Diccionario con datos del certificado o None
    """
    db = repo.get_db()
    try:
        obj = repo.get_certificado(db, cert_id)
        return cert_dict(obj) if obj else None
    finally:
        db.close()


def get_certificado_por_folio(
    folio: str,
    tenant_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Obtiene un certificado por folio.
    
    Args:
        folio: Folio único del certificado
        tenant_id: ID del tenant
        
    Returns:
        Diccionario con datos del certificado o None
    """
    db = repo.get_db()
    try:
        obj = repo.get_certificado_por_folio(db, folio)
        return cert_dict(obj) if obj else None
    finally:
        db.close()


def get_certificados_colaborador(
    colaborador_key: str,
    tenant_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Obtiene todos los certificados de un colaborador.
    
    Args:
        colaborador_key: Identificador del colaborador
        tenant_id: ID del tenant
        
    Returns:
        Lista de certificados como diccionarios
    """
    db = repo.get_db()
    try:
        result = []
        
        # Obtener inscripciones con certificado
        inscripciones = repo.list_inscripciones_con_certificado(
            db,
            colaborador_key
        )
        
        for insc in inscripciones:
            if insc.certificado:
                result.append(cert_dict(insc.certificado))
        
        return result
    finally:
        db.close()


def regenerar_certificado(
    cert_id: int,
    tenant_id: Optional[str] = None,
    actor_key: Optional[str] = None,
    actor_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Regenera un certificado (útil si se actualizó la plantilla).
    
    Args:
        cert_id: ID del certificado
        tenant_id: ID del tenant
        actor_key: Identificador del actor
        actor_name: Nombre del actor
        
    Returns:
        Diccionario con el certificado actualizado o None
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        certificado = repo.get_certificado(db, cert_id)
        
        if not certificado:
            return None
        
        # Limpiar URL del PDF anterior para forzar regeneración
        certificado.url_pdf = None
        certificado.actualizado_en = datetime.utcnow()
        
        # Registrar evento de regeneración
        registrar_evento(
            db,
            "certificado",
            certificado.id,
            "regenerated",
            actor_key=actor_key,
            actor_nombre=actor_name,
            tenant_id=certificado.tenant_id,
            detalle={"folio": certificado.folio}
        )
        
        db.commit()
        db.refresh(certificado)
        
        return cert_dict(certificado)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def actualizar_url_pdf_certificado(
    cert_id: int,
    url_pdf: str,
    tenant_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Actualiza la URL del PDF de un certificado.
    
    Args:
        cert_id: ID del certificado
        url_pdf: URL del archivo PDF generado
        tenant_id: ID del tenant
        
    Returns:
        Diccionario con el certificado actualizado o None
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        certificado = repo.get_certificado(db, cert_id)
        
        if not certificado:
            return None
        
        certificado.url_pdf = url_pdf
        certificado.actualizado_en = datetime.utcnow()
        
        db.commit()
        db.refresh(certificado)
        
        return cert_dict(certificado)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def validar_certificado(
    folio: str,
    tenant_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Valida la autenticidad de un certificado por su folio.
    
    Args:
        folio: Folio único del certificado
        tenant_id: ID del tenant
        
    Returns:
        Diccionario con validación y datos del certificado
    """
    certificado = get_certificado_por_folio(folio, tenant_id)
    
    if not certificado:
        return {
            "valido": False,
            "mensaje": "Certificado no encontrado",
            "certificado": None
        }
    
    return {
        "valido": True,
        "mensaje": "Certificado válido",
        "certificado": certificado
    }


def list_certificados_curso(
    curso_id: int,
    tenant_id: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Lista todos los certificados emitidos para un curso.
    
    Args:
        curso_id: ID del curso
        tenant_id: ID del tenant
        fecha_desde: Fecha inicial del filtro
        fecha_hasta: Fecha final del filtro
        
    Returns:
        Lista de certificados como diccionarios
    """
    db = repo.get_db()
    try:
        result = []
        
        # Obtener certificados del curso
        certificados = repo.list_certificados_por_curso(
            db,
            curso_id,
            fecha_desde,
            fecha_hasta
        )
        
        for cert in certificados:
            result.append(cert_dict(cert))
        
        return result
    finally:
        db.close()


def get_estadisticas_certificados(
    tenant_id: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None
) -> Dict[str, Any]:
    """
    Obtiene estadísticas de certificados emitidos.
    
    Args:
        tenant_id: ID del tenant
        fecha_desde: Fecha inicial del filtro
        fecha_hasta: Fecha final del filtro
        
    Returns:
        Diccionario con estadísticas de certificados
    """
    db = repo.get_db()
    try:
        stats = repo.get_stats_certificados(db, fecha_desde, fecha_hasta)
        
        return {
            "total_certificados": stats.get("total", 0),
            "certificados_por_curso": stats.get("por_curso", []),
            "certificados_por_mes": stats.get("por_mes", []),
            "promedio_puntaje": round(stats.get("promedio_puntaje", 0), 2),
            "top_colaboradores": stats.get("top_colaboradores", [])
        }
    finally:
        db.close()


def revocar_certificado(
    cert_id: int,
    motivo: str,
    tenant_id: Optional[str] = None,
    actor_key: Optional[str] = None,
    actor_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Revoca un certificado emitido.
    
    Args:
        cert_id: ID del certificado
        motivo: Motivo de la revocación
        tenant_id: ID del tenant
        actor_key: Identificador del actor
        actor_name: Nombre del actor
        
    Returns:
        Diccionario con el certificado revocado o None
        
    Raises:
        SQLAlchemyError: Si hay error en la base de datos
    """
    db = repo.get_db()
    try:
        certificado = repo.get_certificado(db, cert_id)
        
        if not certificado:
            return None
        
        # Marcar como revocado
        certificado.revocado = True
        certificado.motivo_revocacion = motivo
        certificado.fecha_revocacion = datetime.utcnow()
        certificado.revocado_por = actor_key
        certificado.actualizado_en = datetime.utcnow()
        
        # Registrar evento de revocación
        registrar_evento(
            db,
            "certificado",
            certificado.id,
            "revoked",
            actor_key=actor_key,
            actor_nombre=actor_name,
            tenant_id=certificado.tenant_id,
            detalle={
                "folio": certificado.folio,
                "motivo": motivo
            }
        )
        
        db.commit()
        db.refresh(certificado)
        
        return cert_dict(certificado)
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()
        