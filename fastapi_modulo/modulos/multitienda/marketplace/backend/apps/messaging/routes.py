from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import get_db
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.dependencies import require_role
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.messaging.models import (
    Conversation,
    ConversationNote,
    Message,
    MessageAttachment,
    MessageTemplate,
    AutoReplyRule,
)
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.messaging.schemas import (
    ConversationCreate,
    ConversationStatusUpdate,
    MessageCreate,
    MessageTemplateCreate,
)

router = APIRouter(tags=["messaging"])


# ─── Conversaciones ──────────────────────────────────────────────────────────

@router.get("/conversations")
def list_conversations(
    vendor_id: int | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("authenticated")),
):
    q = db.query(Conversation)
    if vendor_id:
        q = q.filter(Conversation.vendor_id == vendor_id)
    if status:
        q = q.filter(Conversation.status == status)
    total = q.count()
    items = q.order_by(Conversation.last_message_at.desc()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "items": [
            {
                "id": c.id,
                "uuid": c.uuid,
                "conversation_type": c.conversation_type,
                "status": c.status,
                "subject": c.subject,
                "message_count": c.message_count,
                "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None,
                "vendor_id": c.vendor_id,
                "product_id": c.product_id,
                "order_id": c.order_id,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in items
        ],
    }


@router.post("/conversations", status_code=201)
def create_conversation(
    body: ConversationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("authenticated")),
):
    conv = Conversation(
        conversation_type=body.conversation_type,
        subject=body.subject or "",
        vendor_id=body.vendor_id,
        product_id=body.product_id,
        order_id=body.order_id,
        tags=body.tags or [],
    )
    db.add(conv)
    db.flush()

    if body.initial_message:
        msg = Message(
            conversation_id=conv.id,
            sender_id=current_user.id,
            content=body.initial_message,
            message_type="text",
        )
        db.add(msg)
        conv.message_count = 1

    db.commit()
    db.refresh(conv)
    return {"id": conv.id, "uuid": conv.uuid, "status": conv.status}


@router.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("authenticated")),
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")
    return {
        "id": conv.id,
        "uuid": conv.uuid,
        "conversation_type": conv.conversation_type,
        "status": conv.status,
        "subject": conv.subject,
        "message_count": conv.message_count,
        "vendor_id": conv.vendor_id,
        "product_id": conv.product_id,
        "order_id": conv.order_id,
        "tags": conv.tags,
        "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
        "created_at": conv.created_at.isoformat() if conv.created_at else None,
    }


@router.put("/conversations/{conversation_id}/status")
def update_conversation_status(
    conversation_id: int,
    body: ConversationStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("vendor")),
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")
    conv.status = body.status
    db.commit()
    return {"id": conv.id, "status": conv.status}


# ─── Mensajes ─────────────────────────────────────────────────────────────────

@router.get("/conversations/{conversation_id}/messages")
def list_messages(
    conversation_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("authenticated")),
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")
    msgs = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": m.id,
            "uuid": m.uuid,
            "sender_id": m.sender_id,
            "content": m.content,
            "message_type": m.message_type,
            "is_read": m.is_read,
            "parent_message_id": m.parent_message_id,
            "replied_to_id": m.replied_to_id,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in msgs
    ]


@router.post("/conversations/{conversation_id}/messages", status_code=201)
def send_message(
    conversation_id: int,
    body: MessageCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("authenticated")),
):
    from datetime import datetime

    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")
    if conv.status in {"archived", "blocked"}:
        raise HTTPException(status_code=400, detail=f"Conversación en estado '{conv.status}', no acepta mensajes.")

    msg = Message(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        content=body.content,
        message_type=body.message_type or "text",
        parent_message_id=body.parent_message_id,
        replied_to_id=body.replied_to_id,
    )
    db.add(msg)
    conv.message_count = (conv.message_count or 0) + 1
    conv.last_message_at = datetime.utcnow()
    conv.last_message_by_id = current_user.id
    db.commit()
    db.refresh(msg)
    return {"id": msg.id, "uuid": msg.uuid, "created_at": msg.created_at.isoformat() if msg.created_at else None}


@router.put("/conversations/{conversation_id}/messages/{message_id}/read")
def mark_message_read(
    conversation_id: int,
    message_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("authenticated")),
):
    from datetime import datetime

    msg = db.query(Message).filter(
        Message.id == message_id,
        Message.conversation_id == conversation_id,
    ).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado.")
    msg.is_read = True
    msg.read_at = datetime.utcnow()
    db.commit()
    return {"success": True}


# ─── Plantillas de mensaje ────────────────────────────────────────────────────

@router.get("/message-templates")
def list_templates(
    vendor_id: int | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("vendor")),
):
    q = db.query(MessageTemplate).filter(MessageTemplate.is_active == True)
    if vendor_id:
        q = q.filter(MessageTemplate.vendor_id == vendor_id)
    items = q.order_by(MessageTemplate.name).all()
    return [
        {
            "id": t.id,
            "vendor_id": t.vendor_id,
            "template_type": t.template_type,
            "name": t.name,
            "subject": t.subject,
            "content": t.content,
            "variables": t.variables,
            "use_count": t.use_count,
        }
        for t in items
    ]


@router.post("/message-templates", status_code=201)
def create_template(
    body: MessageTemplateCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("vendor")),
):
    tmpl = MessageTemplate(
        vendor_id=getattr(current_user, "vendor_id", None),
        template_type=body.template_type,
        name=body.name,
        subject=body.subject or "",
        content=body.content,
        variables=body.variables or [],
    )
    db.add(tmpl)
    db.commit()
    db.refresh(tmpl)
    return {"id": tmpl.id, "name": tmpl.name}


@router.delete("/message-templates/{template_id}")
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("vendor")),
):
    tmpl = db.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada.")
    tmpl.is_active = False
    db.commit()
    return {"success": True}
