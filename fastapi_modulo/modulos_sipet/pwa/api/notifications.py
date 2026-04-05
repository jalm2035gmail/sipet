"""
api/notifications.py — Motor de notificaciones institucional.

Rutas:
  GET    /notifications                        listar notificaciones del usuario
  GET    /notifications/unread-count           conteo sin leer
  POST   /notifications/read                   marcar por ids como leídas
  POST   /notifications/{id}/archive           archivar notificación
  GET    /notification-rules                   listar reglas (admin)
  PATCH  /notification-rules/{event_type}      actualizar regla (admin)
  GET    /notifications/preferences            preferencias del usuario
  PATCH  /notifications/preferences/{event}    actualizar preferencia
  POST   /push/subscribe                       registrar suscripción push
  DELETE /push/subscribe                       eliminar suscripción push
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.deps import DBSession, get_current_active_user, require_admin
from models.notification import (
    Notification,
    NotificationRule,
    PushSubscription,
    UserNotificationPreference,
)
from schemas.notification import (
    DeliveryLogRead,
    NotificationPreferenceRead,
    NotificationPreferenceUpdate,
    NotificationRead,
    NotificationRuleRead,
    NotificationRuleUpdate,
    PushSubscriptionCreate,
    PushSubscriptionRead,
    UnreadCountResponse,
)

router = APIRouter()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Notificaciones ────────────────────────────────────────────────────────────

@router.get("", response_model=list[NotificationRead])
def list_notifications(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=30, le=100),
    unread_only: bool = Query(default=False),
    archived: bool = Query(default=False),
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    q = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_archived == archived)
    )
    if unread_only:
        q = q.filter(Notification.is_read.is_(False))
    return q.order_by(Notification.id.desc()).offset(skip).limit(limit).all()


@router.get("/unread-count", response_model=UnreadCountResponse)
def unread_count(
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    count = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
            Notification.is_archived.is_(False),
        )
        .count()
    )
    return UnreadCountResponse(unread=count)


@router.post("/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_notifications_read(
    ids: list[int] = Body(...),
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    if not ids:
        return
    (
        db.query(Notification)
        .filter(
            Notification.id.in_(ids),
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
        .update({"is_read": True, "read_at": _utcnow()}, synchronize_session=False)
    )
    db.commit()


@router.post("/{notif_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
def archive_notification(
    notif_id: int,
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    notif = db.get(Notification, notif_id)
    if not notif or notif.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    notif.is_archived = True
    db.commit()


# ── Reglas de notificación (admin) ────────────────────────────────────────────

@router.get("/rules", response_model=list[NotificationRuleRead])
def list_rules(
    db: Session = DBSession,
    _current_user=Depends(require_admin),
):
    return db.query(NotificationRule).order_by(NotificationRule.event_type).all()


@router.patch("/rules/{event_type}", response_model=NotificationRuleRead)
def update_rule(
    event_type: str,
    body: NotificationRuleUpdate,
    db: Session = DBSession,
    _current_user=Depends(require_admin),
):
    rule = db.query(NotificationRule).filter(NotificationRule.event_type == event_type).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    if body.is_active is not None:
        rule.is_active = body.is_active
    if body.channels is not None:
        rule.channels = body.channels
    if body.cooldown_minutes is not None:
        rule.cooldown_minutes = body.cooldown_minutes
    rule.updated_at = _utcnow()
    db.commit()
    db.refresh(rule)
    return rule


# ── Preferencias de usuario ───────────────────────────────────────────────────

@router.get("/preferences", response_model=list[NotificationPreferenceRead])
def list_preferences(
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    return (
        db.query(UserNotificationPreference)
        .filter(UserNotificationPreference.user_id == current_user.id)
        .order_by(UserNotificationPreference.event_type)
        .all()
    )


@router.patch("/preferences/{event_type}", response_model=NotificationPreferenceRead)
def update_preference(
    event_type: str,
    body: NotificationPreferenceUpdate,
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    pref = (
        db.query(UserNotificationPreference)
        .filter(
            UserNotificationPreference.user_id == current_user.id,
            UserNotificationPreference.event_type == event_type,
        )
        .first()
    )
    if not pref:
        # create on first access
        pref = UserNotificationPreference(
            user_id=current_user.id,
            event_type=event_type,
            updated_at=_utcnow(),
        )
        db.add(pref)

    if body.in_app_enabled is not None:
        pref.in_app_enabled = body.in_app_enabled
    if body.email_enabled is not None:
        pref.email_enabled = body.email_enabled
    if body.push_enabled is not None:
        pref.push_enabled = body.push_enabled
    pref.updated_at = _utcnow()

    db.commit()
    db.refresh(pref)
    return pref


# ── Suscripciones push ────────────────────────────────────────────────────────

@router.post("/push/subscribe", response_model=PushSubscriptionRead, status_code=status.HTTP_201_CREATED)
def register_push(
    body: PushSubscriptionCreate,
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    # deactivate any existing subscription with same endpoint
    (
        db.query(PushSubscription)
        .filter(PushSubscription.endpoint == body.endpoint)
        .update({"is_active": False}, synchronize_session=False)
    )
    sub = PushSubscription(
        user_id=current_user.id,
        endpoint=body.endpoint,
        p256dh=body.p256dh,
        auth=body.auth,
        user_agent=body.user_agent,
        is_active=True,
        created_at=_utcnow(),
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


@router.delete("/push/subscribe", status_code=status.HTTP_204_NO_CONTENT)
def unregister_push(
    endpoint: str = Body(..., embed=True),
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    (
        db.query(PushSubscription)
        .filter(
            PushSubscription.endpoint == endpoint,
            PushSubscription.user_id == current_user.id,
        )
        .update({"is_active": False}, synchronize_session=False)
    )
    db.commit()
