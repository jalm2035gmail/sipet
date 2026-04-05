"""
api/conversations.py — Canal de conversaciones institucional.

Rutas:
  POST   /conversations                           crear conversación
  GET    /conversations                           listar conversaciones del usuario
  GET    /conversations/{id}                      detalle + participantes
  DELETE /conversations/{id}                      archivar (owner/admin)
  POST   /conversations/{id}/participants         agregar participante
  DELETE /conversations/{id}/participants/{uid}   eliminar participante
  GET    /conversations/{id}/messages             listar mensajes (paginado)
  POST   /conversations/{id}/messages             enviar mensaje
  PATCH  /messages/{id}                           editar mensaje
  DELETE /messages/{id}                           eliminar mensaje
  POST   /messages/{id}/attachments               subir adjunto
  POST   /conversations/{id}/read                 marcar leído hasta mensaje
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from api.deps import DBSession, get_current_active_user, require_admin
from app.services import media_service
from models.conversation import (
    Conversation,
    ConversationParticipant,
    Message,
    MessageAttachment,
    MessageMention,
    MessageReadReceipt,
)
from schemas.conversation import (
    AttachmentRead,
    ConversationCreate,
    ConversationRead,
    ConversationSummary,
    MessageCreate,
    MessageEdit,
    MessageRead,
    ParticipantAdd,
    ParticipantRead,
)

router = APIRouter()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _get_conv_or_404(conv_id: int, db: Session) -> Conversation:
    conv = db.get(Conversation, conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    return conv


def _assert_participant(conv: Conversation, user_id: int, db: Session) -> ConversationParticipant:
    part = (
        db.query(ConversationParticipant)
        .filter(
            ConversationParticipant.conversation_id == conv.id,
            ConversationParticipant.user_id == user_id,
        )
        .first()
    )
    if not part:
        raise HTTPException(status_code=403, detail="No pertenece a esta conversación")
    return part


def _is_owner_or_admin(conv: Conversation, current_user) -> bool:
    return (
        conv.created_by_id == current_user.id
        or getattr(current_user, "is_superuser", False)
        or getattr(current_user, "is_admin", False)
    )


def _build_message_read(msg: Message, db: Session) -> MessageRead:
    mentions = [m.mentioned_user_id for m in db.query(MessageMention).filter(MessageMention.message_id == msg.id).all()]
    attachments = db.query(MessageAttachment).filter(MessageAttachment.message_id == msg.id).all()
    return MessageRead(
        id=msg.id,
        conversation_id=msg.conversation_id,
        sender_id=msg.sender_id,
        body=msg.body,
        reply_to_id=msg.reply_to_id,
        is_system=msg.is_system,
        edited_at=msg.edited_at,
        created_at=msg.created_at,
        attachments=[
            AttachmentRead(
                id=a.id, message_id=a.message_id, filename=a.filename,
                file_url=a.file_url, mime_type=a.mime_type,
                size_bytes=a.size_bytes, uploaded_at=a.uploaded_at,
            )
            for a in attachments
        ],
        mentions=mentions,
    )


# ── Conversaciones ─────────────────────────────────────────────────────────────

@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
def create_conversation(
    body: ConversationCreate,
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    conv = Conversation(
        type=body.type,
        title=body.title,
        ref_type=body.ref_type,
        ref_id=body.ref_id,
        created_by_id=current_user.id,
        status="active",
        created_at=_utcnow(),
        updated_at=_utcnow(),
    )
    db.add(conv)
    db.flush()  # get conv.id before adding participants

    # owner always added
    participant_ids = set(body.participant_ids) | {current_user.id}
    for uid in participant_ids:
        role = "owner" if uid == current_user.id else "member"
        db.add(ConversationParticipant(
            conversation_id=conv.id, user_id=uid, role=role, joined_at=_utcnow()
        ))

    db.commit()
    db.refresh(conv)
    return conv


@router.get("", response_model=list[ConversationSummary])
def list_conversations(
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    parts = (
        db.query(ConversationParticipant)
        .filter(ConversationParticipant.user_id == current_user.id)
        .all()
    )
    result = []
    for p in parts:
        conv = db.get(Conversation, p.conversation_id)
        if not conv or conv.status == "archived":
            continue
        last_msg = (
            db.query(Message)
            .filter(Message.conversation_id == conv.id)
            .order_by(Message.id.desc())
            .first()
        )
        unread = (
            db.query(Message)
            .filter(
                Message.conversation_id == conv.id,
                Message.id > (p.last_read_at and 0 or 0),  # simplified; full impl uses last_read_at
            )
            .count()
        )
        result.append(ConversationSummary(
            id=conv.id, type=conv.type, title=conv.title, status=conv.status,
            ref_type=conv.ref_type, ref_id=conv.ref_id, created_by_id=conv.created_by_id,
            created_at=conv.created_at, updated_at=conv.updated_at,
            unread_count=unread,
            last_message=_build_message_read(last_msg, db) if last_msg else None,
        ))
    return result


@router.get("/{conv_id}", response_model=ConversationRead)
def get_conversation(
    conv_id: int,
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    conv = _get_conv_or_404(conv_id, db)
    _assert_participant(conv, current_user.id, db)
    return conv


@router.delete("/{conv_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_conversation(
    conv_id: int,
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    conv = _get_conv_or_404(conv_id, db)
    if not _is_owner_or_admin(conv, current_user):
        raise HTTPException(status_code=403, detail="Sin permisos para archivar")
    conv.status = "archived"
    conv.updated_at = _utcnow()
    db.commit()


# ── Participantes ─────────────────────────────────────────────────────────────

@router.post("/{conv_id}/participants", response_model=ParticipantRead, status_code=status.HTTP_201_CREATED)
def add_participant(
    conv_id: int,
    body: ParticipantAdd,
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    conv = _get_conv_or_404(conv_id, db)
    _assert_participant(conv, current_user.id, db)

    existing = (
        db.query(ConversationParticipant)
        .filter(
            ConversationParticipant.conversation_id == conv_id,
            ConversationParticipant.user_id == body.user_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Usuario ya es participante")

    part = ConversationParticipant(
        conversation_id=conv_id,
        user_id=body.user_id,
        role=body.role,
        joined_at=_utcnow(),
    )
    db.add(part)
    db.commit()
    db.refresh(part)
    return part


@router.delete("/{conv_id}/participants/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_participant(
    conv_id: int,
    user_id: int,
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    conv = _get_conv_or_404(conv_id, db)
    if not _is_owner_or_admin(conv, current_user) and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Sin permisos")

    part = (
        db.query(ConversationParticipant)
        .filter(
            ConversationParticipant.conversation_id == conv_id,
            ConversationParticipant.user_id == user_id,
        )
        .first()
    )
    if not part:
        raise HTTPException(status_code=404, detail="Participante no encontrado")
    if part.role == "owner" and conv.created_by_id == user_id:
        raise HTTPException(status_code=400, detail="No se puede remover al propietario")

    db.delete(part)
    db.commit()


# ── Mensajes ──────────────────────────────────────────────────────────────────

@router.get("/{conv_id}/messages", response_model=list[MessageRead])
def list_messages(
    conv_id: int,
    before_id: Optional[int] = Query(default=None),
    limit: int = Query(default=30, le=100),
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    conv = _get_conv_or_404(conv_id, db)
    _assert_participant(conv, current_user.id, db)

    q = db.query(Message).filter(Message.conversation_id == conv_id)
    if before_id:
        q = q.filter(Message.id < before_id)
    messages = q.order_by(Message.id.desc()).limit(limit).all()
    return [_build_message_read(m, db) for m in reversed(messages)]


@router.post("/{conv_id}/messages", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
def send_message(
    conv_id: int,
    body: MessageCreate,
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    conv = _get_conv_or_404(conv_id, db)
    _assert_participant(conv, current_user.id, db)

    if body.reply_to_id:
        reply = db.get(Message, body.reply_to_id)
        if not reply or reply.conversation_id != conv_id:
            raise HTTPException(status_code=400, detail="reply_to_id inválido")

    msg = Message(
        conversation_id=conv_id,
        sender_id=current_user.id,
        body=body.body,
        reply_to_id=body.reply_to_id,
        is_system=False,
        created_at=_utcnow(),
    )
    db.add(msg)
    db.flush()

    for uid in body.mentioned_user_ids:
        db.add(MessageMention(message_id=msg.id, mentioned_user_id=uid))

    # update conversation timestamp
    conv.updated_at = _utcnow()
    db.commit()
    db.refresh(msg)
    return _build_message_read(msg, db)


@router.patch("/messages/{msg_id}", response_model=MessageRead)
def edit_message(
    msg_id: int,
    body: MessageEdit,
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    msg = db.get(Message, msg_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")
    if msg.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="Solo el autor puede editar")
    if msg.is_system:
        raise HTTPException(status_code=400, detail="Los mensajes de sistema no se editan")
    msg.body = body.body
    msg.edited_at = _utcnow()
    db.commit()
    db.refresh(msg)
    return _build_message_read(msg, db)


@router.delete("/messages/{msg_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(
    msg_id: int,
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    msg = db.get(Message, msg_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")
    conv = db.get(Conversation, msg.conversation_id)
    if msg.sender_id != current_user.id and not _is_owner_or_admin(conv, current_user):
        raise HTTPException(status_code=403, detail="Sin permisos para eliminar")
    db.delete(msg)
    db.commit()


# ── Adjuntos ──────────────────────────────────────────────────────────────────

@router.post("/messages/{msg_id}/attachments", response_model=AttachmentRead, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    msg_id: int,
    file: UploadFile = File(...),
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    msg = db.get(Message, msg_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")
    _assert_participant(db.get(Conversation, msg.conversation_id), current_user.id, db)

    data = await file.read()
    stored_name = f"pwa_conv_{msg.conversation_id}_{msg_id}_{file.filename}"
    path = media_service.save_upload(data, stored_name, subfolder="pwa_attachments")
    attachment = MessageAttachment(
        message_id=msg_id,
        filename=file.filename,
        file_url=str(path).replace("media", "/media", 1),
        mime_type=file.content_type,
        size_bytes=len(data),
        uploaded_at=_utcnow(),
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


# ── Marcar como leído ─────────────────────────────────────────────────────────

@router.post("/{conv_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_read(
    conv_id: int,
    last_message_id: int = Query(...),
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    conv = _get_conv_or_404(conv_id, db)
    part = _assert_participant(conv, current_user.id, db)
    part.last_read_at = _utcnow()

    # upsert read receipts for all messages up to last_message_id
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conv_id, Message.id <= last_message_id)
        .all()
    )
    for msg in messages:
        exists = (
            db.query(MessageReadReceipt)
            .filter(MessageReadReceipt.message_id == msg.id, MessageReadReceipt.user_id == current_user.id)
            .first()
        )
        if not exists:
            db.add(MessageReadReceipt(message_id=msg.id, user_id=current_user.id, read_at=_utcnow()))

    db.commit()
