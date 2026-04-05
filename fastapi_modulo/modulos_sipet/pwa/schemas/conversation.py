from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


ConversationType = Literal["direct", "group", "activity", "delivery"]
ConversationStatus = Literal["active", "archived", "closed"]
ParticipantRole = Literal["owner", "member", "observer"]


# ── Conversación ──────────────────────────────────────────────────────────────

class ConversationCreate(BaseModel):
    type: ConversationType
    title: Optional[str] = None
    ref_type: Optional[str] = None
    ref_id: Optional[int] = None
    participant_ids: list[int] = []


class ConversationRead(BaseModel):
    id: int
    type: ConversationType
    title: Optional[str] = None
    status: ConversationStatus
    ref_type: Optional[str] = None
    ref_id: Optional[int] = None
    created_by_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Participante ──────────────────────────────────────────────────────────────

class ParticipantRead(BaseModel):
    id: int
    conversation_id: int
    user_id: int
    role: ParticipantRole
    last_read_at: Optional[datetime] = None
    joined_at: datetime

    model_config = {"from_attributes": True}


class ParticipantAdd(BaseModel):
    user_id: int
    role: ParticipantRole = "member"


# ── Mensaje ───────────────────────────────────────────────────────────────────

class MessageCreate(BaseModel):
    conversation_id: int
    body: str
    reply_to_id: Optional[int] = None
    mentioned_user_ids: list[int] = []


class MessageRead(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    body: str
    reply_to_id: Optional[int] = None
    is_system: bool
    edited_at: Optional[datetime] = None
    created_at: datetime
    attachments: list["AttachmentRead"] = []
    mentions: list[int] = []          # mentioned_user_ids

    model_config = {"from_attributes": True}


class MessageEdit(BaseModel):
    body: str


# ── Adjunto ───────────────────────────────────────────────────────────────────

class AttachmentRead(BaseModel):
    id: int
    message_id: int
    filename: str
    file_url: str
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    uploaded_at: datetime

    model_config = {"from_attributes": True}


# ── Acuse de lectura ──────────────────────────────────────────────────────────

class ReadReceiptCreate(BaseModel):
    message_id: int


class ReadReceiptRead(BaseModel):
    id: int
    message_id: int
    user_id: int
    read_at: datetime

    model_config = {"from_attributes": True}


# ── Resumen de conversación (con conteo no leído) ─────────────────────────────

class ConversationSummary(ConversationRead):
    unread_count: int = 0
    last_message: Optional[MessageRead] = None
