"""
modelos/schemas.py

Schemas Pydantic v2 para el módulo de notificaciones/conversaciones.
Cubre request bodies, responses y modelos internos de todos los endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ===========================================================================
# Base compartida
# ===========================================================================

class _Base(BaseModel):
    model_config = {"from_attributes": True, "populate_by_name": True}


# ===========================================================================
# ── MENSAJES DIRECTOS ──────────────────────────────────────────────────────
# ===========================================================================

class SendDirectMessageRequest(_Base):
    """Body para POST /api/v1/conversaciones/direct/send"""

    to_username: Optional[str] = Field(
        default="",
        description="Username del destinatario. Requerido si no se envía conversation_id.",
    )
    conversation_id: Optional[str] = Field(
        default="",
        description="ID de conversación existente. Alternativa a to_username.",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Texto del mensaje.",
    )

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El mensaje no puede estar vacío o contener solo espacios.")
        return v.strip()

    @field_validator("to_username", "conversation_id", mode="before")
    @classmethod
    def clean_str(cls, v: Any) -> str:
        return str(v or "").strip().lower()

    @model_validator(mode="after")
    def require_target(self) -> "SendDirectMessageRequest":
        if not self.to_username and not self.conversation_id:
            raise ValueError("Debes proporcionar to_username o conversation_id.")
        return self


class DirectMessageOut(_Base):
    """Mensaje directo serializado para respuestas."""

    id: int
    from_username: str
    to_usernames: List[str] = Field(default_factory=list)
    message_text: str
    is_read: bool
    created_at: str
    is_mine: bool = False


class DirectConversationSummary(_Base):
    """Resumen de conversación directa en la lista del sidebar."""

    conversation_id: str
    other_user: str
    last_at: str = ""
    last_message: str = ""
    unread: int = 0


class SendDirectMessageResponse(_Base):
    success: bool
    data: Dict[str, str] = Field(default_factory=dict)


class ListDirectConversationsResponse(_Base):
    success: bool
    data: List[DirectConversationSummary]
    access: Optional[Dict[str, Any]] = None


class GetDirectConversationResponse(_Base):
    success: bool
    data: List[DirectMessageOut]
    access: Optional[Dict[str, Any]] = None


# ===========================================================================
# ── GRUPOS ─────────────────────────────────────────────────────────────────
# ===========================================================================

class CreateGroupRequest(_Base):
    """Body para POST /api/v1/conversaciones/groups"""

    group_name: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Nombre visible del grupo.",
    )
    member_usernames: List[str] = Field(
        default_factory=list,
        description="Lista de usernames a incluir (sin contar al creador).",
    )

    @field_validator("group_name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El nombre del grupo no puede estar vacío.")
        return v.strip()

    @field_validator("member_usernames", mode="before")
    @classmethod
    def clean_members(cls, v: Any) -> List[str]:
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


class SendGroupMessageRequest(_Base):
    """Body para POST /api/v1/conversaciones/groups/{conv_id}/send"""

    message: str = Field(..., min_length=1, max_length=4000)

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El mensaje no puede estar vacío.")
        return v.strip()


class GroupMessageOut(_Base):
    """Mensaje de grupo serializado para respuestas."""

    id: int
    from_username: str
    to_usernames: List[str] = Field(default_factory=list)
    message_text: str
    is_read: bool
    created_at: str
    is_mine: bool = False


class GroupMeta(_Base):
    """Metadatos del grupo devueltos junto con los mensajes."""

    conversation_id: str
    group_name: str
    created_by: str
    member_usernames: List[str] = Field(default_factory=list)


class GroupConversationSummary(_Base):
    """Resumen de grupo en la lista del sidebar."""

    conversation_id: str
    group_name: str
    created_by: str = ""
    member_usernames: List[str] = Field(default_factory=list)
    last_at: str = ""
    last_message: str = ""
    unread: int = 0


class CreateGroupResponse(_Base):
    success: bool
    data: Dict[str, Any] = Field(default_factory=dict)


class ListGroupConversationsResponse(_Base):
    success: bool
    data: List[GroupConversationSummary]
    access: Optional[Dict[str, Any]] = None


class GetGroupConversationResponse(_Base):
    success: bool
    data: List[GroupMessageOut]
    group: Optional[GroupMeta] = None
    access: Optional[Dict[str, Any]] = None


# ===========================================================================
# ── NOTIFICACIONES DE CONVERSACIÓN ─────────────────────────────────────────
# ===========================================================================

class SendConversationNotificationRequest(_Base):
    """Body para POST /api/v1/conversaciones/notifications/send"""

    conversation_id: Optional[str] = Field(default="")
    message: str = Field(..., min_length=1, max_length=2000)
    scope: Literal["conversation", "department", "company"] = Field(
        default="conversation",
        description="Alcance de la notificación.",
    )

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El mensaje no puede estar vacío.")
        return v.strip()

    @field_validator("conversation_id", mode="before")
    @classmethod
    def clean_conv(cls, v: Any) -> str:
        return str(v or "").strip()


class ConversationNotificationOut(_Base):
    """Notificación flotante serializada para el inbox."""

    id: int
    from_username: str
    message_text: str
    scope: str
    conversation_id: str
    created_at: str


class SendNotificationResponse(_Base):
    success: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    access: Optional[Dict[str, Any]] = None


class NotificationInboxResponse(_Base):
    success: bool
    data: List[ConversationNotificationOut]
    access: Optional[Dict[str, Any]] = None


# ===========================================================================
# ── CONTEO DE NO LEÍDOS ────────────────────────────────────────────────────
# ===========================================================================

class UnreadCountData(_Base):
    count: int = 0
    direct: int = 0
    group: int = 0
    notifications: int = 0


class UnreadCountResponse(_Base):
    success: bool
    data: UnreadCountData
    access: Optional[Dict[str, Any]] = None


# ===========================================================================
# ── USUARIOS DEL MÓDULO ────────────────────────────────────────────────────
# ===========================================================================

class ConversationAccessInfo(_Base):
    role: str = ""
    can_create_groups: bool = False
    can_send_notifications: bool = False
    notification_scope: str = ""


class ModuleUserOut(_Base):
    """Usuario visible en los modales de nueva conversación/grupo."""

    id: int
    username: str
    full_name: str
    role: str = ""
    imagen: str = ""
    departamento: str = ""
    conversation_access: ConversationAccessInfo


class ListUsersResponse(_Base):
    success: bool
    data: List[ModuleUserOut]
    access: Optional[ConversationAccessInfo] = None


class GetAccessResponse(_Base):
    success: bool
    data: ConversationAccessInfo


# ===========================================================================
# ── NOTIFICACIONES GLOBALES (global_notifications_service) ─────────────────
# ===========================================================================

class NotificationItem(_Base):
    """
    Ítem de notificación global (POA, KPI, documentos, etc.)
    devuelto por GET /api/v1/notificaciones/summary.
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


class NotificationCounts(_Base):
    poa_aprobacion: int = 0
    documento_autorizacion: int = 0
    actividad_fecha: int = 0
    actividad_atrasada: int = 0
    actividad_por_vencer: int = 0
    quiz_descuento: int = 0
    ia_riesgo_poa: int = 0
    kpi_alerta: int = 0
    kpi_advertencia: int = 0


class NotificationsSummaryResponse(_Base):
    success: bool
    total: int
    unread: int
    counts: NotificationCounts
    items: List[NotificationItem]


class MarkReadRequest(_Base):
    """Body para POST /api/v1/notificaciones/read"""

    id: str = Field(
        ...,
        min_length=1,
        description="ID compuesto de la notificación (ej: 'poa-approval-42').",
    )

    @field_validator("id")
    @classmethod
    def id_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El ID de notificación no puede estar vacío.")
        return v.strip()


class MarkAllReadRequest(_Base):
    """Body para POST /api/v1/notificaciones/read-all"""

    ids: List[str] = Field(
        default_factory=list,
        max_length=200,
        description="Lista de IDs de notificaciones a marcar como leídas.",
    )

    @field_validator("ids", mode="before")
    @classmethod
    def clean_ids(cls, v: Any) -> List[str]:
        if not isinstance(v, list):
            return []
        return [str(i).strip() for i in v if str(i).strip()][:200]


class MarkReadResponse(_Base):
    success: bool
    updated: Optional[int] = None


# ===========================================================================
# ── RESPUESTA DE ERROR ESTÁNDAR ────────────────────────────────────────────
# ===========================================================================

class ErrorResponse(_Base):
    """
    Respuesta de error uniforme para todos los endpoints del módulo.
    Usar como response_model en los decoradores @router cuando sea conveniente.
    """

    success: Literal[False] = False
    error: str
    detail: Optional[str] = None
    