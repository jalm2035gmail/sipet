"""Servicio de conversaciones contextuales del CRM.

Permite vincular hilos de conversación a cualquier entidad CRM:
contacto, oportunidad, actividad o campaña.

Tipos de mensaje predefinidos:
  comentario  — seguimiento libre del lead / oportunidad
  apoyo       — solicitud de ayuda a ejecutivo o supervisor
  validacion  — solicitud de revisión / aprobación de propuesta
  cierre      — observaciones finales al cerrar una oportunidad
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi_modulo.modulos.crm.modelos.db_models import CrmConversacion, CrmMensaje
from fastapi_modulo.modulos.crm.repositorios.common import get_db

# Tipos válidos de referencia
REF_TIPOS = {"contacto", "oportunidad", "actividad", "campania"}
# Tipos válidos de mensaje
TIPOS_MENSAJE = {"comentario", "apoyo", "validacion", "cierre"}


# ── Mappers ────────────────────────────────────────────────────────────────────

def _map_conversacion(c: CrmConversacion, include_mensajes: bool = False) -> dict[str, Any]:
    out: dict[str, Any] = {
        "id": c.id,
        "tenant_id": c.tenant_id,
        "ref_tipo": c.ref_tipo,
        "ref_id": c.ref_id,
        "asunto": c.asunto,
        "estado": c.estado,
        "actor": c.actor,
        "multitienda_uuid": c.multitienda_uuid,
        "creado_en": c.creado_en.isoformat() if c.creado_en else None,
        "actualizado_en": c.actualizado_en.isoformat() if c.actualizado_en else None,
        "total_mensajes": len(c.mensajes) if c.mensajes is not None else 0,
        "no_leidos": sum(1 for m in (c.mensajes or []) if not m.leido),
    }
    if include_mensajes:
        out["mensajes"] = [_map_mensaje(m) for m in sorted(c.mensajes or [], key=lambda m: m.creado_en or datetime.min)]
    return out


def _map_mensaje(m: CrmMensaje) -> dict[str, Any]:
    return {
        "id": m.id,
        "conversacion_id": m.conversacion_id,
        "actor": m.actor,
        "contenido": m.contenido,
        "tipo": m.tipo,
        "leido": m.leido,
        "creado_en": m.creado_en.isoformat() if m.creado_en else None,
    }


# ── CRUD ───────────────────────────────────────────────────────────────────────

def list_conversaciones(
    tenant_id: str,
    ref_tipo: str | None = None,
    ref_id: int | None = None,
    estado: str | None = None,
    host: str | None = None,
) -> list[dict[str, Any]]:
    db = get_db(host)
    try:
        q = db.query(CrmConversacion).filter(CrmConversacion.tenant_id == tenant_id)
        if ref_tipo:
            q = q.filter(CrmConversacion.ref_tipo == ref_tipo)
        if ref_id is not None:
            q = q.filter(CrmConversacion.ref_id == ref_id)
        if estado:
            q = q.filter(CrmConversacion.estado == estado)
        rows = q.order_by(CrmConversacion.actualizado_en.desc()).all()
        return [_map_conversacion(c, include_mensajes=False) for c in rows]
    finally:
        db.close()


def get_conversacion(
    tenant_id: str, conversacion_id: int, host: str | None = None
) -> dict[str, Any] | None:
    db = get_db(host)
    try:
        c = (
            db.query(CrmConversacion)
            .filter(CrmConversacion.id == conversacion_id, CrmConversacion.tenant_id == tenant_id)
            .first()
        )
        return _map_conversacion(c, include_mensajes=True) if c else None
    finally:
        db.close()


def crear_conversacion(
    tenant_id: str,
    ref_tipo: str,
    ref_id: int,
    asunto: str,
    actor: str,
    mensaje_inicial: str,
    tipo_mensaje: str = "comentario",
    multitienda_uuid: str | None = None,
    host: str | None = None,
) -> dict[str, Any]:
    if ref_tipo not in REF_TIPOS:
        raise ValueError(f"ref_tipo inválido: {ref_tipo}. Valores: {REF_TIPOS}")
    if tipo_mensaje not in TIPOS_MENSAJE:
        raise ValueError(f"tipo_mensaje inválido: {tipo_mensaje}. Valores: {TIPOS_MENSAJE}")
    db = get_db(host)
    try:
        conv = CrmConversacion(
            tenant_id=tenant_id,
            ref_tipo=ref_tipo,
            ref_id=ref_id,
            asunto=asunto,
            estado="abierta",
            actor=actor,
            multitienda_uuid=multitienda_uuid,
            creado_en=datetime.utcnow(),
            actualizado_en=datetime.utcnow(),
        )
        db.add(conv)
        db.flush()
        msg = CrmMensaje(
            conversacion_id=conv.id,
            actor=actor,
            contenido=mensaje_inicial,
            tipo=tipo_mensaje,
            leido=False,
            creado_en=datetime.utcnow(),
        )
        db.add(msg)
        db.commit()
        db.refresh(conv)
        return _map_conversacion(conv, include_mensajes=True)
    finally:
        db.close()


def agregar_mensaje(
    tenant_id: str,
    conversacion_id: int,
    actor: str,
    contenido: str,
    tipo: str = "comentario",
    host: str | None = None,
) -> dict[str, Any]:
    if tipo not in TIPOS_MENSAJE:
        raise ValueError(f"tipo inválido: {tipo}. Valores: {TIPOS_MENSAJE}")
    db = get_db(host)
    try:
        conv = (
            db.query(CrmConversacion)
            .filter(CrmConversacion.id == conversacion_id, CrmConversacion.tenant_id == tenant_id)
            .first()
        )
        if not conv:
            raise ValueError("Conversación no encontrada")
        if conv.estado == "cerrada":
            raise ValueError("No se puede agregar mensajes a una conversación cerrada")
        msg = CrmMensaje(
            conversacion_id=conversacion_id,
            actor=actor,
            contenido=contenido,
            tipo=tipo,
            leido=False,
            creado_en=datetime.utcnow(),
        )
        db.add(msg)
        conv.actualizado_en = datetime.utcnow()
        db.commit()
        db.refresh(msg)
        return _map_mensaje(msg)
    finally:
        db.close()


def marcar_mensajes_leidos(
    tenant_id: str, conversacion_id: int, actor: str, host: str | None = None
) -> dict[str, Any]:
    db = get_db(host)
    try:
        conv = (
            db.query(CrmConversacion)
            .filter(CrmConversacion.id == conversacion_id, CrmConversacion.tenant_id == tenant_id)
            .first()
        )
        if not conv:
            raise ValueError("Conversación no encontrada")
        actualizados = 0
        for msg in conv.mensajes or []:
            if not msg.leido and msg.actor != actor:
                msg.leido = True
                actualizados += 1
        db.commit()
        return {"marcados_leidos": actualizados}
    finally:
        db.close()


def cerrar_conversacion(
    tenant_id: str, conversacion_id: int, actor: str, observacion: str = "", host: str | None = None
) -> dict[str, Any]:
    db = get_db(host)
    try:
        conv = (
            db.query(CrmConversacion)
            .filter(CrmConversacion.id == conversacion_id, CrmConversacion.tenant_id == tenant_id)
            .first()
        )
        if not conv:
            raise ValueError("Conversación no encontrada")
        if conv.estado == "cerrada":
            raise ValueError("La conversación ya está cerrada")
        conv.estado = "cerrada"
        conv.actualizado_en = datetime.utcnow()
        if observacion:
            msg = CrmMensaje(
                conversacion_id=conversacion_id,
                actor=actor,
                contenido=observacion,
                tipo="cierre",
                leido=False,
                creado_en=datetime.utcnow(),
            )
            db.add(msg)
        db.commit()
        db.refresh(conv)
        return _map_conversacion(conv, include_mensajes=True)
    finally:
        db.close()


# ── Acciones tipificadas ────────────────────────────────────────────────────────

def comentar_seguimiento(
    tenant_id: str, ref_tipo: str, ref_id: int, actor: str, comentario: str, host: str | None = None
) -> dict[str, Any]:
    """Abre una conversación de seguimiento de lead u oportunidad."""
    return crear_conversacion(
        tenant_id=tenant_id,
        ref_tipo=ref_tipo,
        ref_id=ref_id,
        asunto=f"Seguimiento — {ref_tipo} #{ref_id}",
        actor=actor,
        mensaje_inicial=comentario,
        tipo_mensaje="comentario",
        host=host,
    )


def pedir_apoyo(
    tenant_id: str, ref_tipo: str, ref_id: int, actor: str, descripcion: str,
    destinatario: str = "", host: str | None = None
) -> dict[str, Any]:
    """Solicita apoyo de ejecutivo o supervisor."""
    contenido = descripcion if not destinatario else f"@{destinatario} — {descripcion}"
    return crear_conversacion(
        tenant_id=tenant_id,
        ref_tipo=ref_tipo,
        ref_id=ref_id,
        asunto=f"Solicitud de apoyo — {ref_tipo} #{ref_id}",
        actor=actor,
        mensaje_inicial=contenido,
        tipo_mensaje="apoyo",
        host=host,
    )


def validar_propuesta(
    tenant_id: str, ref_tipo: str, ref_id: int, actor: str, detalle: str, host: str | None = None
) -> dict[str, Any]:
    """Solicita validación o aprobación de una propuesta."""
    return crear_conversacion(
        tenant_id=tenant_id,
        ref_tipo=ref_tipo,
        ref_id=ref_id,
        asunto=f"Validar propuesta — {ref_tipo} #{ref_id}",
        actor=actor,
        mensaje_inicial=detalle,
        tipo_mensaje="validacion",
        host=host,
    )


def registrar_observaciones_cierre(
    tenant_id: str, ref_tipo: str, ref_id: int, actor: str, observaciones: str, host: str | None = None
) -> dict[str, Any]:
    """Deja observaciones al cerrar una oportunidad."""
    conv = crear_conversacion(
        tenant_id=tenant_id,
        ref_tipo=ref_tipo,
        ref_id=ref_id,
        asunto=f"Observaciones de cierre — {ref_tipo} #{ref_id}",
        actor=actor,
        mensaje_inicial=observaciones,
        tipo_mensaje="cierre",
        host=host,
    )
    # Auto-cerrar la conversación de cierre
    db = get_db(host)
    try:
        c = db.query(CrmConversacion).filter(CrmConversacion.id == conv["id"]).first()
        if c:
            c.estado = "cerrada"
            db.commit()
            conv["estado"] = "cerrada"
    finally:
        db.close()
    return conv
