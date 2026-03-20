"""
modelos/orm_models.py

Modelos SQLAlchemy ORM para el módulo de notificaciones/conversaciones.
Reemplaza los CREATE TABLE IF NOT EXISTS inline que estaban dispersos
en los controladores. Las tablas se crean/migran via Alembic.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# ---------------------------------------------------------------------------
# Base declarativa compartida con el resto de la app.
# Si la app ya define una Base en otro módulo, importa esa en lugar de crear
# una nueva: from fastapi_modulo.core.db import Base
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ---------------------------------------------------------------------------
# Mensajes directos entre usuarios
# ---------------------------------------------------------------------------

class UserDirectMessage(Base):
    """
    Mensaje directo entre dos usuarios.
    conversation_id sigue el patrón 'dm-{user_a}_{user_b}' (sorted).
    to_usernames se almacena como JSON array en texto: '["ana","luis"]'
    """
    __tablename__ = "user_direct_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(String(255), nullable=False)
    from_username: Mapped[str] = mapped_column(String(120), nullable=False)
    to_usernames: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    message_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow
    )

    __table_args__ = (
        Index("ix_udm_conv", "conversation_id", "created_at"),
        Index("ix_udm_from", "from_username", "created_at"),
        # Índice sobre is_read para conteos de no leídos eficientes
        Index("ix_udm_read", "from_username", "is_read"),
    )

    def __repr__(self) -> str:
        return (
            f"<UserDirectMessage id={self.id} "
            f"conv={self.conversation_id!r} "
            f"from={self.from_username!r}>"
        )


# ---------------------------------------------------------------------------
# Grupos de conversación
## Las tablas de conversaciones se migran via Alembic.
## Los modelos ORM se mantienen para uso en la app, pero la creación de tablas se gestiona por migraciones.
        Index("ix_cgm_conv", "conversation_id", "created_at"),
        Index("ix_cgm_read", "from_username", "is_read"),
    )

    def __repr__(self) -> str:
        return (
            f"<ConversationGroupMessage id={self.id} "
            f"conv={self.conversation_id!r} "
            f"from={self.from_username!r}>"
        )


# ---------------------------------------------------------------------------
# Notificaciones flotantes de conversación
# ---------------------------------------------------------------------------

class ConversationNotification(Base):
    """
    Notificación flotante enviada dentro del módulo de conversaciones.
    scope: 'conversation' | 'department' | 'company'
    to_usernames: JSON array de destinatarios.
    """
    __tablename__ = "conversation_notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    from_username: Mapped[str] = mapped_column(String(120), nullable=False)
    to_usernames: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    message_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    scope: Mapped[str] = mapped_column(
        String(32), nullable=False, default="conversation"
    )
    conversation_id: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow
    )

    __table_args__ = (
        Index("ix_cn_read", "is_read", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<ConversationNotification id={self.id} "
            f"scope={self.scope!r} "
            f"from={self.from_username!r}>"
        )


# ---------------------------------------------------------------------------
# Alertas de riesgo IA — POA
# ---------------------------------------------------------------------------

class IaPoaRiskAlert(Base):
    """
    Alertas generadas por el motor de riesgo IA sobre actividades POA.
    source: identifica el motor que generó la alerta (default 'ia_risk_engine').
    severity: 'high' | 'medium' | 'low'
    status: 'active' | 'resolved'
    """
    __tablename__ = "ia_poa_risk_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow, onupdate=_utcnow
    )
    alert_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    activity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    objective_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    axis_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    owner: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    title: Mapped[str] = mapped_column(Text, nullable=False, default="")
    message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    recommendation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source: Mapped[str] = mapped_column(
        String(64), nullable=False, default="ia_risk_engine"
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_ia_risk_status", "source", "status", "severity"),
        UniqueConstraint("alert_key", name="uq_ia_risk_alert_key"),
    )

    def __repr__(self) -> str:
        return (
            f"<IaPoaRiskAlert id={self.id} "
            f"severity={self.severity!r} "
            f"status={self.status!r}>"
        )


# ---------------------------------------------------------------------------
# Lectura de notificaciones globales (UserNotificationRead)
# Tabla usada por global_notifications_service para marcar leídas.
# Si ya está definida en runtime_app, no redefinir — comentar este bloque.
# ---------------------------------------------------------------------------

class UserNotificationRead(Base):
    """
    Registro de notificaciones globales leídas por usuario/tenant.
    notification_id es el ID compuesto de la notificación
    (ej: 'poa-approval-42', 'kpi-alerta-7').
    """
    __tablename__ = "user_notification_reads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(120), nullable=False)
    user_key: Mapped[str] = mapped_column(String(255), nullable=False)
    notification_id: Mapped[str] = mapped_column(String(255), nullable=False)
    read_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "user_key", "notification_id",
            name="uq_notif_read_per_user"
        ),
        Index("ix_notif_read_lookup", "tenant_id", "user_key"),
    )

    def __repr__(self) -> str:
        return (
            f"<UserNotificationRead id={self.id} "
            f"user={self.user_key!r} "
            f"notif={self.notification_id!r}>"
        )
        