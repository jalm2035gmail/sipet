from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Conversación ──────────────────────────────────────────────────────────────

class Conversation(Base):
    __tablename__ = "pwa_conversations"

    id = Column(Integer, primary_key=True, index=True)
    # direct | group | ctx_activity | ctx_objective | ctx_kpi | ctx_area | ctx_store
    type = Column(String(30), nullable=False)
    title = Column(String(255), nullable=True)
    status = Column(String(20), default="active", nullable=False)  # active | archived | closed
    ref_type = Column(String(50), nullable=True)   # "activity" | "objective" | "kpi" | "store_order" …
    ref_id = Column(Integer, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    participants = relationship(
        "ConversationParticipant", back_populates="conversation", cascade="all, delete-orphan"
    )
    messages = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )


# ── Participante ──────────────────────────────────────────────────────────────

class ConversationParticipant(Base):
    __tablename__ = "pwa_conversation_participants"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("pwa_conversations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(20), default="member", nullable=False)  # owner | member | observer
    joined_at = Column(DateTime(timezone=True), default=utcnow)
    last_read_at = Column(DateTime(timezone=True), nullable=True)

    conversation = relationship("Conversation", back_populates="participants")


# ── Mensaje ───────────────────────────────────────────────────────────────────

class Message(Base):
    __tablename__ = "pwa_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("pwa_conversations.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    body = Column(Text, nullable=False)
    reply_to_id = Column(Integer, ForeignKey("pwa_messages.id"), nullable=True)
    is_system = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    edited_at = Column(DateTime(timezone=True), nullable=True)

    conversation = relationship("Conversation", back_populates="messages")
    mentions = relationship(
        "MessageMention", back_populates="message", cascade="all, delete-orphan"
    )
    attachments = relationship(
        "MessageAttachment", back_populates="message", cascade="all, delete-orphan"
    )
    read_receipts = relationship(
        "MessageReadReceipt", back_populates="message", cascade="all, delete-orphan"
    )


# ── Mención ───────────────────────────────────────────────────────────────────

class MessageMention(Base):
    __tablename__ = "pwa_message_mentions"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("pwa_messages.id"), nullable=False, index=True)
    mentioned_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    message = relationship("Message", back_populates="mentions")


# ── Adjunto ───────────────────────────────────────────────────────────────────

class MessageAttachment(Base):
    __tablename__ = "pwa_message_attachments"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("pwa_messages.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=True)
    size_bytes = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), default=utcnow)

    message = relationship("Message", back_populates="attachments")


# ── Recibo de lectura ─────────────────────────────────────────────────────────

class MessageReadReceipt(Base):
    __tablename__ = "pwa_message_read_receipts"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("pwa_messages.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    read_at = Column(DateTime(timezone=True), default=utcnow)

    message = relationship("Message", back_populates="read_receipts")
