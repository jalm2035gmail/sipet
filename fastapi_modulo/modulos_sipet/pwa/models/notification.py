from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey,
    Integer, JSON, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Notificación ──────────────────────────────────────────────────────────────

class Notification(Base):
    __tablename__ = "pwa_notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    event_type = Column(String(20), nullable=False)          # NT-01 .. NT-14
    severity = Column(String(20), nullable=False)            # informativa | preventiva | crítica
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=True)
    ref_type = Column(String(50), nullable=True)             # "activity" | "conversation" | …
    ref_id = Column(Integer, nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    is_archived = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    delivery_logs = relationship(
        "NotificationDeliveryLog", back_populates="notification", cascade="all, delete-orphan"
    )


# ── Regla de notificación ─────────────────────────────────────────────────────

class NotificationRule(Base):
    __tablename__ = "pwa_notification_rules"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(20), unique=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    channels = Column(JSON, default=lambda: ["in_app"])      # ["in_app", "email", "push"]
    cooldown_minutes = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


# ── Preferencia de usuario ────────────────────────────────────────────────────

class UserNotificationPreference(Base):
    __tablename__ = "pwa_user_notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_type = Column(String(20), nullable=False)
    in_app_enabled = Column(Boolean, default=True, nullable=False)
    email_enabled = Column(Boolean, default=False, nullable=False)
    push_enabled = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (UniqueConstraint("user_id", "event_type", name="uq_user_event_pref"),)


# ── Log de entrega ────────────────────────────────────────────────────────────

class NotificationDeliveryLog(Base):
    __tablename__ = "pwa_notification_delivery_logs"

    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(Integer, ForeignKey("pwa_notifications.id"), nullable=False, index=True)
    channel = Column(String(20), nullable=False)             # in_app | email | push
    status = Column(String(20), default="pending", nullable=False)  # pending | sent | failed
    attempted_at = Column(DateTime(timezone=True), default=utcnow)
    error_detail = Column(Text, nullable=True)

    notification = relationship("Notification", back_populates="delivery_logs")


# ── Suscripción push ──────────────────────────────────────────────────────────

class PushSubscription(Base):
    __tablename__ = "pwa_push_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    endpoint = Column(Text, nullable=False)
    p256dh = Column(Text, nullable=False)
    auth = Column(Text, nullable=False)
    user_agent = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
