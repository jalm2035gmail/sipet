from celery import shared_task
from datetime import datetime, timedelta, date
import logging
from sqlalchemy import and_, case, func
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.messaging.models import (
    AutoReplyRule,
    Conversation,
    Message,
    MessageAnalytics,
)
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.vendors.models import VendorStore as Vendor
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import SessionLocal
# from backend.apps.notifications.utils import send_email_notification
# from backend.apps.surveys.models import Survey

logger = logging.getLogger(__name__)

@shared_task
def send_message_notification(message_id: int):
    """Enviar notificación por email de nuevo mensaje (placeholder)"""
    db = SessionLocal()
    try:
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message or not message.recipient:
            return
        # if not message.recipient.notification_preferences.get('new_messages', True):
        #     return
        # subject = f"New message from {message.sender.first_name}"
        # context = {...}
        # send_email_notification(to_email=message.recipient.email, subject=subject, template_name='new_message', context=context)
        logger.info(f"Would send message notification to {message.recipient.email}")
    except Exception:
        logger.exception("Error sending message notification")
    finally:
        db.close()

@shared_task
def send_auto_reply(rule_id: int, conversation_id: int, trigger_message_id: int):
    """Enviar respuesta automática basada en reglas"""
    db = SessionLocal()
    try:
        rule = db.query(AutoReplyRule).filter(AutoReplyRule.id == rule_id).first()
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        trigger_message = db.query(Message).filter(Message.id == trigger_message_id).first()
        if not rule or not conversation or not trigger_message:
            return
        if conversation.status != 'active':
            return
        # context = {...}
        reply_content = rule.template or "Auto-reply"
        auto_message = Message(
            conversation_id=conversation.id,
            sender_id=rule.vendor_id,
            recipient_id=trigger_message.sender_id,
            content=reply_content,
            message_type='text'
        )
        db.add(auto_message)
        db.commit()
        logger.info(f"Sent auto-reply to conversation {conversation_id}")
    except Exception:
        logger.exception("Error sending auto-reply")
    finally:
        db.close()

@shared_task
def close_inactive_conversations():
    """Cerrar conversaciones inactivas automáticamente"""
    db = SessionLocal()
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=72)
        inactive_conversations = db.query(Conversation).filter(
            Conversation.status == 'active',
            Conversation.last_message_at < cutoff_time
        ).all()
        closed_count = 0
        for conversation in inactive_conversations:
            conversation.status = 'closed'
            conversation.closed_at = datetime.utcnow()
            db.add(conversation)
            closed_count += 1
        db.commit()
        logger.info(f"Closed {closed_count} inactive conversations")
    except Exception:
        logger.exception("Error closing inactive conversations")
    finally:
        db.close()

@shared_task
def update_message_analytics():
    """Actualizar analíticas de mensajería"""
    db = SessionLocal()
    try:
        today = date.today()
        day_start = datetime.combine(today, datetime.min.time())
        vendors = (
            db.query(Vendor.id, Vendor.vendor_id)
            .filter(Vendor.status == 'approved')
            .all()
        )
        if not vendors:
            return

        vendor_ids = [vendor.id for vendor in vendors]

        conversation_stats = {
            row.vendor_id: row
            for row in (
                db.query(
                    Conversation.vendor_id.label("vendor_id"),
                    func.count(Conversation.id).label("total_conversations"),
                    func.sum(
                        case((Conversation.created_at >= day_start, 1), else_=0)
                    ).label("new_conversations"),
                )
                .filter(Conversation.vendor_id.in_(vendor_ids))
                .group_by(Conversation.vendor_id)
                .all()
            )
        }

        message_stats = {
            row.vendor_id: row
            for row in (
                db.query(
                    Conversation.vendor_id.label("vendor_id"),
                    func.count(Message.id).label("total_messages"),
                    func.sum(
                        case(
                            (
                                and_(
                                    Message.created_at >= day_start,
                                    Message.sender_id == Vendor.vendor_id,
                                ),
                                1,
                            ),
                            else_=0,
                        )
                    ).label("messages_sent"),
                    func.sum(
                        case(
                            (
                                and_(
                                    Message.created_at >= day_start,
                                    Message.sender_id != Vendor.vendor_id,
                                ),
                                1,
                            ),
                            else_=0,
                        )
                    ).label("messages_received"),
                )
                .join(Conversation, Conversation.id == Message.conversation_id)
                .join(Vendor, Vendor.id == Conversation.vendor_id)
                .filter(Conversation.vendor_id.in_(vendor_ids))
                .group_by(Conversation.vendor_id)
                .all()
            )
        }

        analytics_rows = {
            analytics.vendor_id: analytics
            for analytics in (
                db.query(MessageAnalytics)
                .filter(
                    MessageAnalytics.vendor_id.in_(vendor_ids),
                    MessageAnalytics.date == today,
                )
                .all()
            )
        }

        for vendor in vendors:
            analytics = analytics_rows.get(vendor.id)
            if analytics is None:
                analytics = MessageAnalytics(vendor_id=vendor.id, date=today)
                db.add(analytics)
                analytics_rows[vendor.id] = analytics

            vendor_conversations = conversation_stats.get(vendor.id)
            vendor_messages = message_stats.get(vendor.id)
            analytics.total_conversations = int(
                getattr(vendor_conversations, "total_conversations", 0) or 0
            )
            analytics.new_conversations = int(
                getattr(vendor_conversations, "new_conversations", 0) or 0
            )
            analytics.total_messages = int(
                getattr(vendor_messages, "total_messages", 0) or 0
            )
            analytics.messages_sent = int(
                getattr(vendor_messages, "messages_sent", 0) or 0
            )
            analytics.messages_received = int(
                getattr(vendor_messages, "messages_received", 0) or 0
            )
            # Tiempo promedio de respuesta (simplificado)
            analytics.avg_response_time_minutes = 0

        db.commit()
        logger.info("Updated messaging analytics for %s vendors", len(vendors))
    except Exception:
        logger.exception("Error updating messaging analytics")
    finally:
        db.close()

@shared_task
def send_conversation_followup(conversation_id: int):
    """Enviar seguimiento automático después de conversación resuelta (placeholder)"""
    db = SessionLocal()
    try:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation or conversation.status != 'resolved':
            return
        # if conversation.closed_at > datetime.utcnow() - timedelta(hours=24):
        #     return
        # survey = Survey(...)
        # followup_message = Message(...)
        logger.info(f"Would send follow-up survey for conversation {conversation_id}")
    except Exception:
        logger.exception("Error sending conversation follow-up")
    finally:
        db.close()
