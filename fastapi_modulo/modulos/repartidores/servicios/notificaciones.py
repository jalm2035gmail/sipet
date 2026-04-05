from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from fastapi_modulo.modulos.repartidores.modelos.db_models import (
        RepEntrega,
        RepRepartidor,
    )

logger = logging.getLogger(__name__)

_WHATSAPP_ENABLED = os.environ.get('WHATSAPP_ENABLED', '').lower() in {'1', 'true', 'yes'}
_EMAIL_ENABLED = os.environ.get('EMAIL_ENABLED', '').lower() in {'1', 'true', 'yes'}


# ---------------------------------------------------------------------------
# Stubs de entrega real — reemplazar cuando se configure WhatsApp/email
# ---------------------------------------------------------------------------

def _send_whatsapp(to_phone: str, message: str) -> bool:
    """Envía mensaje WhatsApp. Requiere WHATSAPP_ENABLED=true y credenciales."""
    if not _WHATSAPP_ENABLED or not to_phone:
        logger.debug('WhatsApp no configurado. Mensaje al %s no enviado.', to_phone)
        return False
    # TODO: integrar con Twilio / Meta Cloud API usando:
    #   WHATSAPP_API_TOKEN, WHATSAPP_PHONE_ID, WHATSAPP_API_URL
    logger.warning('WhatsApp stub — pendiente integrar: %s → %.80s', to_phone, message)
    return False


def _send_email(to_email: str, subject: str, body: str) -> bool:
    """Envía email. Requiere EMAIL_ENABLED=true y credenciales SMTP/SendGrid."""
    if not _EMAIL_ENABLED or not to_email:
        logger.debug('Email no configurado. Mensaje a %s no enviado.', to_email)
        return False
    # TODO: integrar con SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SMTP_PORT
    #   o SENDGRID_API_KEY
    logger.warning('Email stub — pendiente integrar: %s → %s', to_email, subject)
    return False


# ---------------------------------------------------------------------------
# Logger interno en DB
# ---------------------------------------------------------------------------

def _log_notificacion(
    db: Session,
    tipo: str,
    canal: str,
    destinatario: str,
    mensaje: str,
    entrega_id: int | None = None,
    repartidor_id: int | None = None,
    estado: str = 'pendiente',
    error: str = '',
) -> None:
    from fastapi_modulo.modulos.repartidores.modelos.db_models import RepNotificacionLog

    log = RepNotificacionLog(
        tipo=tipo,
        canal=canal,
        destinatario=destinatario,
        mensaje=mensaje,
        entrega_id=entrega_id,
        repartidor_id=repartidor_id,
        estado=estado,
        error_msg=error,
    )
    db.add(log)
    try:
        db.flush()
    except Exception as exc:
        logger.warning('_log_notificacion: flush error=%s', exc)


# ---------------------------------------------------------------------------
# Notificaciones al cliente
# ---------------------------------------------------------------------------

def notif_entrega_asignada(
    db: Session,
    entrega: RepEntrega,
    repartidor: RepRepartidor,
) -> None:
    """Cliente: su entrega fue asignada a un repartidor."""
    mensaje = (
        f'Tu entrega {entrega.folio} fue asignada a {repartidor.name}. '
        f'Tel: {repartidor.telefono or "—"}'
    )
    enviado_wapp = _send_whatsapp(entrega.cliente_telefono or '', mensaje)
    enviado_email = _send_email(
        entrega.cliente_nombre or '',
        f'Entrega asignada — {entrega.folio}',
        mensaje,
    )
    estado = 'enviado' if (enviado_wapp or enviado_email) else 'pendiente'
    _log_notificacion(
        db,
        'entrega_asignada',
        'whatsapp+email',
        entrega.cliente_telefono or entrega.cliente_nombre or '—',
        mensaje,
        entrega_id=entrega.id,
        repartidor_id=repartidor.id,
        estado=estado,
    )


def notif_repartidor_en_camino(
    db: Session,
    entrega: RepEntrega,
    repartidor: RepRepartidor,
) -> None:
    """Cliente: el repartidor está en camino."""
    mensaje = (
        f'Tu repartidor {repartidor.name} está en camino '
        f'con tu pedido {entrega.folio}.'
    )
    enviado = _send_whatsapp(entrega.cliente_telefono or '', mensaje)
    _log_notificacion(
        db,
        'repartidor_en_camino',
        'whatsapp',
        entrega.cliente_telefono or '—',
        mensaje,
        entrega_id=entrega.id,
        repartidor_id=repartidor.id,
        estado='enviado' if enviado else 'pendiente',
    )


def notif_entrega_confirmada(db: Session, entrega: RepEntrega) -> None:
    """Cliente: la entrega fue completada."""
    mensaje = f'Entrega {entrega.folio} completada exitosamente. ¡Gracias!'
    enviado = _send_whatsapp(entrega.cliente_telefono or '', mensaje)
    _log_notificacion(
        db,
        'entrega_confirmada',
        'whatsapp',
        entrega.cliente_telefono or '—',
        mensaje,
        entrega_id=entrega.id,
        estado='enviado' if enviado else 'pendiente',
    )


# ---------------------------------------------------------------------------
# Notificaciones al repartidor
# ---------------------------------------------------------------------------

def notif_nueva_asignacion_repartidor(
    db: Session,
    entrega: RepEntrega,
    repartidor: RepRepartidor,
) -> None:
    """Repartidor: tiene una nueva entrega asignada."""
    mensaje = (
        f'Nueva entrega asignada: {entrega.folio}\n'
        f'Destino: {entrega.destino}\n'
        f'Cliente: {entrega.cliente_nombre}'
    )
    enviado = _send_whatsapp(repartidor.telefono or '', mensaje)
    _log_notificacion(
        db,
        'nueva_asignacion',
        'whatsapp',
        repartidor.telefono or repartidor.email or '—',
        mensaje,
        entrega_id=entrega.id,
        repartidor_id=repartidor.id,
        estado='enviado' if enviado else 'pendiente',
    )


def notif_recordatorio_pendientes_directo(
    db: Session,
    repartidor: RepRepartidor,
    entregas: list[RepEntrega],
) -> None:
    """Repartidor: recordatorio de entregas pendientes del día (llamado desde Celery)."""
    folios = ', '.join(e.folio for e in entregas[:5])
    extra = f' (y {len(entregas) - 5} más)' if len(entregas) > 5 else ''
    mensaje = (
        f'Recordatorio: tienes {len(entregas)} entrega(s) pendiente(s) hoy.\n'
        f'Folios: {folios}{extra}'
    )
    enviado = _send_whatsapp(repartidor.telefono or '', mensaje)
    _log_notificacion(
        db,
        'recordatorio_pendientes',
        'whatsapp',
        repartidor.telefono or repartidor.email or '—',
        mensaje,
        repartidor_id=repartidor.id,
        estado='enviado' if enviado else 'pendiente',
    )
