"""
Tareas Celery para el módulo de notificaciones/conversaciones.

Expone `celery_app` y la tarea pública `send_notification`, usando Redis
como broker y result backend.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from celery import Celery
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuración de Celery — lee variables de entorno con fallbacks seguros
# ---------------------------------------------------------------------------

_REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
_BROKER_URL = os.environ.get("CELERY_BROKER_URL", _REDIS_URL)
_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", _REDIS_URL)

celery_app = Celery(
    "notificaciones",
    broker=_BROKER_URL,
    backend=_RESULT_BACKEND,
)

celery_app.conf.update(
    # Serialización
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # Zona horaria
    timezone="UTC",
    enable_utc=True,
    # Reintentos y fiabilidad
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    # Expiración de resultados: 1 hora
    result_expires=3600,
    # Rutas de tareas
    task_routes={
        "notificaciones.send_notification": {"queue": "notificaciones"},
        "notificaciones.send_floating_notification": {"queue": "notificaciones"},
        "notificaciones.broadcast_notification": {"queue": "notificaciones"},
        "notificaciones.purge_old_notifications": {"queue": "maintenance"},
        "notificaciones.send_unread_summary_sse": {"queue": "notificaciones"},
    },
    # Beat schedule — tareas periódicas
    beat_schedule={
        "purge-old-notifications-daily": {
            "task": "notificaciones.purge_old_notifications",
            "schedule": 86400,  # cada 24 horas
            "kwargs": {"days_to_keep": 30},
        },
    },
)


# ---------------------------------------------------------------------------
# Schemas Pydantic para los payloads de las tareas
# Sirven como contrato tipado entre el código que encola y el worker.
# ---------------------------------------------------------------------------

class SendMessageRequest(BaseModel):
    """
    Payload para encolar el envío de un mensaje directo o de grupo.
    Validado antes de serializar a JSON y enviarlo al broker.
    """

    conversation_id: str = Field(..., min_length=1, description="ID de la conversación destino.")
    from_username: str = Field(..., min_length=1, description="Username del emisor.")
    to_usernames: List[str] = Field(..., min_length=1, description="Lista de destinatarios.")
    message: str = Field(..., min_length=1, max_length=4000, description="Texto del mensaje.")
    conv_type: str = Field(
        default="dm",
        pattern="^(dm|group)$",
        description="Tipo de conversación: 'dm' o 'group'.",
    )

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El mensaje no puede estar vacío.")
        return v.strip()

    @field_validator("to_usernames", mode="before")
    @classmethod
    def clean_recipients(cls, v: object) -> List[str]:
        if not isinstance(v, list):
            return []
        seen: set[str] = set()
        result: List[str] = []
        for item in v:
            name = str(item or "").strip().lower()
            if name and name not in seen:
                seen.add(name)
                result.append(name)
        return result


class CreateGroupRequest(BaseModel):
    """
    Payload para encolar la creación de un grupo de conversación.
    """

    group_name: str = Field(..., min_length=1, max_length=120)
    created_by: str = Field(..., min_length=1)
    member_usernames: List[str] = Field(..., min_length=2)
    tenant_id: str = Field(default="default")

    @field_validator("group_name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El nombre del grupo no puede estar vacío.")
        return v.strip()

    @field_validator("member_usernames", mode="before")
    @classmethod
    def clean_members(cls, v: object) -> List[str]:
        if not isinstance(v, list):
            return []
        seen: set[str] = set()
        result: List[str] = []
        for item in v:
            name = str(item or "").strip().lower()
            if name and name not in seen:
                seen.add(name)
                result.append(name)
        return result


class NotificationPayload(BaseModel):
    """
    Payload para encolar el envío de una notificación flotante.
    Usado por send_floating_notification_task y broadcast_notification_task.
    """

    from_username: str = Field(..., min_length=1)
    recipients: List[str] = Field(..., min_length=1)
    message: str = Field(..., min_length=1, max_length=2000)
    scope: str = Field(
        default="conversation",
        pattern="^(conversation|department|company)$",
    )
    conversation_id: str = Field(default="")
    tenant_id: str = Field(default="default")

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El mensaje no puede estar vacío.")
        return v.strip()

    @field_validator("recipients", mode="before")
    @classmethod
    def clean_recipients(cls, v: object) -> List[str]:
        if not isinstance(v, list):
            return []
        seen: set[str] = set()
        result: List[str] = []
        for item in v:
            name = str(item or "").strip().lower()
            if name and name not in seen:
                seen.add(name)
                result.append(name)
        return result


class NotificationItem(BaseModel):
    """
    Ítem de notificación global listo para publicar por SSE o Redis Pub/Sub.
    Equivalente al NotificationItem de schemas.py pero empaquetado para
    el worker — no depende de FastAPI ni de la sesión de DB.
    """

    id: str
    kind: str
    title: str
    message: str
    created_at: str
    href: str
    read: bool = False
    deadline_state: Optional[str] = None
    severity: Optional[str] = None
    tenant_id: str = "default"
    user_key: str = ""

    def to_sse_data(self) -> str:
        """Serializa el ítem como string JSON para un evento SSE."""
        return json.dumps(self.model_dump(), ensure_ascii=False)


# ---------------------------------------------------------------------------
# Helpers internos del worker
# ---------------------------------------------------------------------------

def _get_db():
    """
    Obtiene una sesión de DB para el worker.
    Importación diferida para evitar cargar SQLAlchemy al importar el módulo
    en entornos donde solo se usa el cliente Celery (ej: el proceso FastAPI).
    """
    from fastapi_modulo.core.db import SessionLocal  # noqa: PLC0415
    return SessionLocal()


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


# ---------------------------------------------------------------------------
# Helper compartido para insertar notificaciones
# ---------------------------------------------------------------------------

def _insert_notification(
    from_username: str,
    recipients: List[str],
    message: str,
    scope: str = "conversation",
    conversation_id: str = "",
) -> dict:
    payload = NotificationPayload(
        from_username=from_username,
        recipients=recipients,
        message=message,
        scope=scope,
        conversation_id=conversation_id,
    )

    db = _get_db()
    try:
        from sqlalchemy import text  # noqa: PLC0415
        db.execute(
            text(
                """
                INSERT INTO conversation_notifications
                    (from_username, to_usernames, message_text,
                     scope, conversation_id, is_read, created_at)
                VALUES
                    (:from_u, :to_u, :msg, :scope, :conv, 0, :ts)
                """
            ),
            {
                "from_u": payload.from_username,
                "to_u": json.dumps(payload.recipients, ensure_ascii=False),
                "msg": payload.message,
                "scope": payload.scope,
                "conv": payload.conversation_id,
                "ts": _now_iso(),
            },
        )
        db.commit()
        logger.info(
            "Notificación enviada por %s a %d destinatarios (scope=%s)",
            payload.from_username,
            len(payload.recipients),
            payload.scope,
        )
        return {"success": True, "recipients": len(payload.recipients), "scope": payload.scope}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tarea principal pedida por el módulo: send_notification.delay(...)
# ---------------------------------------------------------------------------

@celery_app.task(
    name="notificaciones.send_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def send_notification(
    self,
    from_username: str,
    recipients: List[str],
    message: str,
    scope: str = "conversation",
    conversation_id: str = "",
) -> dict:
    try:
        return _insert_notification(
            from_username=from_username,
            recipients=recipients,
            message=message,
            scope=scope,
            conversation_id=conversation_id,
        )
    except Exception as exc:
        logger.exception("Error al insertar notificación: %s", exc)
        raise self.retry(exc=exc)


# Alias legado para no romper imports previos.
@celery_app.task(
    name="notificaciones.send_floating_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def send_floating_notification_task(
    self,
    from_username: str,
    recipients: List[str],
    message: str,
    scope: str = "conversation",
    conversation_id: str = "",
) -> dict:
    try:
        return _insert_notification(
            from_username=from_username,
            recipients=recipients,
            message=message,
            scope=scope,
            conversation_id=conversation_id,
        )
    except Exception as exc:
        logger.exception("Error al insertar notificación: %s", exc)
        raise self.retry(exc=exc)


# ---------------------------------------------------------------------------
# Tarea: broadcast a un departamento o empresa completa
# ---------------------------------------------------------------------------

@celery_app.task(
    name="notificaciones.broadcast_notification",
    bind=True,
    max_retries=2,
    default_retry_delay=15,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def broadcast_notification_task(
    self,
    from_username: str,
    message: str,
    scope: str,
    tenant_id: str = "default",
    department: str = "",
) -> dict:
    """
    Envía una notificación a todos los usuarios de un departamento
    o de toda la empresa, resolviendo destinatarios en el worker.

    Uso:
        broadcast_notification_task.delay(
            from_username="admin",
            message="Sistema en mantenimiento a las 18:00",
            scope="company",
            tenant_id="coop_demo",
        )
    """
    db = _get_db()
    try:
        from sqlalchemy import text  # noqa: PLC0415

        query = "SELECT username FROM users WHERE is_active = 1"
        params: dict = {}
        if scope == "department" and department:
            query += " AND LOWER(COALESCE(departamento,'')) = :dept"
            params["dept"] = department.strip().lower()

        rows = db.execute(text(query), params).fetchall()
        recipients = [
            str(row.username).strip().lower()
            for row in rows
            if str(row.username or "").strip().lower() != from_username.strip().lower()
        ]

        if not recipients:
            logger.warning("broadcast_notification: sin destinatarios (scope=%s)", scope)
            return {"success": True, "recipients": 0, "scope": scope}

        db.execute(
            text(
                """
                INSERT INTO conversation_notifications
                    (from_username, to_usernames, message_text,
                     scope, conversation_id, is_read, created_at)
                VALUES
                    (:from_u, :to_u, :msg, :scope, '', 0, :ts)
                """
            ),
            {
                "from_u": from_username.strip().lower(),
                "to_u": json.dumps(recipients, ensure_ascii=False),
                "msg": message.strip(),
                "scope": scope,
                "ts": _now_iso(),
            },
        )
        db.commit()
        logger.info(
            "Broadcast por %s a %d usuarios (scope=%s, tenant=%s)",
            from_username,
            len(recipients),
            scope,
            tenant_id,
        )
        return {"success": True, "recipients": len(recipients), "scope": scope}
    except Exception as exc:
        db.rollback()
        logger.exception("Error en broadcast_notification: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tarea: publicar evento SSE via Redis Pub/Sub
# ---------------------------------------------------------------------------

@celery_app.task(
    name="notificaciones.send_unread_summary_sse",
    bind=True,
    max_retries=2,
    default_retry_delay=5,
    ignore_result=True,
)
def send_unread_summary_sse_task(
    self,
    user_key: str,
    unread_count: int,
    tenant_id: str = "default",
) -> None:
    """
    Publica en Redis el conteo de no leídas para un usuario específico.
    El endpoint SSE (/api/v1/notificaciones/stream) suscribe a este canal
    y hace push al cliente sin necesidad de polling.

    Canal Redis: notif:sse:{tenant_id}:{user_key}

    Uso:
        send_unread_summary_sse_task.delay(
            user_key="ana",
            unread_count=3,
            tenant_id="coop_demo",
        )
    """
    try:
        import redis  # noqa: PLC0415

        r = redis.from_url(_REDIS_URL, decode_responses=True)
        channel = f"notif:sse:{tenant_id}:{user_key}"
        payload = json.dumps(
            {"unread": unread_count, "ts": _now_iso()},
            ensure_ascii=False,
        )
        r.publish(channel, payload)
        logger.debug("SSE publicado en %s: %s", channel, payload)
    except Exception as exc:
        logger.exception("Error al publicar SSE para %s: %s", user_key, exc)
        raise self.retry(exc=exc)


# ---------------------------------------------------------------------------
# Tarea periódica: limpieza de notificaciones antiguas
# ---------------------------------------------------------------------------

@celery_app.task(
    name="notificaciones.purge_old_notifications",
    bind=True,
    max_retries=1,
    ignore_result=True,
)
def purge_old_notifications_task(self, days_to_keep: int = 30) -> dict:
    """
    Elimina notificaciones leídas con más de `days_to_keep` días de antigüedad.
    Se ejecuta diariamente via Celery Beat (configurado en beat_schedule).

    Uso manual:
        purge_old_notifications_task.delay(days_to_keep=30)
    """
    db = _get_db()
    try:
        from sqlalchemy import text  # noqa: PLC0415

        cutoff = (
            datetime.now(timezone.utc) - timedelta(days=days_to_keep)
        ).strftime("%Y-%m-%dT%H:%M:%S")

        result = db.execute(
            text(
                """
                DELETE FROM conversation_notifications
                WHERE is_read = 1 AND created_at < :cutoff
                """
            ),
            {"cutoff": cutoff},
        )
        deleted = result.rowcount
        db.commit()
        logger.info("purge_old_notifications: eliminadas %d notificaciones (cutoff=%s)", deleted, cutoff)
        return {"success": True, "deleted": deleted, "cutoff": cutoff}
    except Exception as exc:
        db.rollback()
        logger.exception("Error en purge_old_notifications: %s", exc)
        raise self.retry(exc=exc)
    finally:
        db.close()
        
