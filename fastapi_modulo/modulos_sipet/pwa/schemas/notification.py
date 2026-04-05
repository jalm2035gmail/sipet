from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


Severity = Literal["informativa", "preventiva", "crítica"]
DeliveryChannel = Literal["in_app", "email", "push"]
DeliveryStatus = Literal["pending", "sent", "failed"]


# ── Notificación ──────────────────────────────────────────────────────────────

class NotificationRead(BaseModel):
    id: int
    user_id: int
    event_type: str
    severity: Severity
    title: str
    body: Optional[str] = None
    ref_type: Optional[str] = None
    ref_id: Optional[int] = None
    is_read: bool
    read_at: Optional[datetime] = None
    is_archived: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationMarkRead(BaseModel):
    ids: list[int]


class UnreadCountResponse(BaseModel):
    unread: int


# ── Regla de notificación ─────────────────────────────────────────────────────

class NotificationRuleRead(BaseModel):
    id: int
    event_type: str
    is_active: bool
    channels: list[DeliveryChannel]
    cooldown_minutes: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NotificationRuleUpdate(BaseModel):
    is_active: Optional[bool] = None
    channels: Optional[list[DeliveryChannel]] = None
    cooldown_minutes: Optional[int] = None


# ── Preferencia de usuario ────────────────────────────────────────────────────

class NotificationPreferenceRead(BaseModel):
    id: int
    user_id: int
    event_type: str
    in_app_enabled: bool
    email_enabled: bool
    push_enabled: bool
    updated_at: datetime

    model_config = {"from_attributes": True}


class NotificationPreferenceUpdate(BaseModel):
    in_app_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None


# ── Log de entrega ────────────────────────────────────────────────────────────

class DeliveryLogRead(BaseModel):
    id: int
    notification_id: int
    channel: DeliveryChannel
    status: DeliveryStatus
    attempted_at: datetime
    error_detail: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Suscripción push ──────────────────────────────────────────────────────────

class PushSubscriptionCreate(BaseModel):
    endpoint: str
    p256dh: str
    auth: str
    user_agent: Optional[str] = None


class PushSubscriptionRead(BaseModel):
    id: int
    user_id: int
    endpoint: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
