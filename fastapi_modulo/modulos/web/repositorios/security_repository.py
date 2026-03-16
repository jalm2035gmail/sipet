from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy.exc import OperationalError, SQLAlchemyError

from fastapi_modulo.db import SessionLocal
from fastapi_modulo.modulos.web.modelos.db_models import (
    WebLoginAttempt,
    WebMfaChallenge,
    WebSecurityEvent,
    WebUserPreference,
    WebUserSession,
)
from fastapi_modulo.modulos.web.servicios.redis_security_service import mark_session_revoked


def _safe_commit(db) -> bool:
    try:
        db.commit()
        return True
    except (OperationalError, SQLAlchemyError):
        db.rollback()
        return False


def log_login_attempt(
    *,
    tenant_id: str,
    username: str,
    ip: str,
    user_agent: str,
    success: bool,
) -> None:
    db = SessionLocal()
    try:
        db.add(
            WebLoginAttempt(
                tenant_id=tenant_id,
                username=username,
                ip=ip,
                user_agent=user_agent,
                success=success,
            )
        )
        _safe_commit(db)
    finally:
        db.close()


def store_user_session(
    *,
    user_id: int,
    tenant_id: str,
    session_jti: str,
    ip: str,
    user_agent: str,
    expires_at: datetime,
) -> None:
    db = SessionLocal()
    try:
        existing = db.query(WebUserSession).filter(WebUserSession.session_jti == session_jti).first()
        if existing is None:
            existing = WebUserSession(
                user_id=int(user_id),
                tenant_id=tenant_id,
                session_jti=session_jti,
            )
            db.add(existing)
        existing.ip = ip
        existing.user_agent = user_agent
        existing.expires_at = expires_at
        existing.revoked_at = None
        _safe_commit(db)
    finally:
        db.close()


def revoke_session(session_jti: str) -> None:
    if not session_jti:
        return
    mark_session_revoked(session_jti, 60 * 60 * 24)
    db = SessionLocal()
    try:
        row = db.query(WebUserSession).filter(WebUserSession.session_jti == session_jti).first()
        if row is None:
            return
        row.revoked_at = datetime.utcnow()
        _safe_commit(db)
    finally:
        db.close()


def revoke_user_sessions(*, user_id: int, tenant_id: str, keep_session_jti: str = "") -> int:
    revoked = 0
    db = SessionLocal()
    try:
        rows = (
            db.query(WebUserSession)
            .filter(
                WebUserSession.user_id == int(user_id),
                WebUserSession.tenant_id == tenant_id,
                WebUserSession.revoked_at.is_(None),
                WebUserSession.expires_at > datetime.utcnow(),
            )
            .all()
        )
        for row in rows:
            if keep_session_jti and row.session_jti == keep_session_jti:
                continue
            row.revoked_at = datetime.utcnow()
            mark_session_revoked(row.session_jti, 60 * 60 * 24)
            revoked += 1
        _safe_commit(db)
        return revoked
    finally:
        db.close()


def count_active_sessions(*, user_id: int, tenant_id: str) -> int:
    db = SessionLocal()
    try:
        return int(
            db.query(WebUserSession)
            .filter(
                WebUserSession.user_id == int(user_id),
                WebUserSession.tenant_id == tenant_id,
                WebUserSession.revoked_at.is_(None),
                WebUserSession.expires_at > datetime.utcnow(),
            )
            .count()
        )
    finally:
        db.close()


def list_active_sessions(*, user_id: int, tenant_id: str) -> list[dict[str, Any]]:
    db = SessionLocal()
    try:
        rows = (
            db.query(WebUserSession)
            .filter(
                WebUserSession.user_id == int(user_id),
                WebUserSession.tenant_id == tenant_id,
                WebUserSession.revoked_at.is_(None),
                WebUserSession.expires_at > datetime.utcnow(),
            )
            .order_by(WebUserSession.created_at.desc())
            .all()
        )
        return [
            {
                "session_jti": row.session_jti,
                "ip": row.ip,
                "user_agent": row.user_agent,
                "created_at": row.created_at.isoformat() if row.created_at else "",
                "expires_at": row.expires_at.isoformat() if row.expires_at else "",
            }
            for row in rows
        ]
    finally:
        db.close()


def store_mfa_challenge(
    *,
    user_id: int,
    challenge_type: str,
    token_jti: str,
    challenge: str,
    expires_at: datetime,
    origin: str = "",
    rp_id: str = "",
) -> None:
    db = SessionLocal()
    try:
        existing = db.query(WebMfaChallenge).filter(WebMfaChallenge.token_jti == token_jti).first()
        if existing is None:
            existing = WebMfaChallenge(
                user_id=int(user_id),
                type=challenge_type,
                token_jti=token_jti,
                challenge=challenge,
                origin=origin,
                rp_id=rp_id,
                expires_at=expires_at,
            )
            db.add(existing)
        else:
            existing.user_id = int(user_id)
            existing.type = challenge_type
            existing.token_jti = token_jti
            existing.challenge = challenge
            existing.origin = origin
            existing.rp_id = rp_id
            existing.expires_at = expires_at
            existing.used_at = None
        _safe_commit(db)
    finally:
        db.close()


def consume_mfa_challenge(
    *,
    user_id: int,
    challenge_type: str,
    token_jti: str,
    challenge: str,
) -> None:
    db = SessionLocal()
    try:
        row = (
            db.query(WebMfaChallenge)
            .filter(
                WebMfaChallenge.user_id == int(user_id),
                WebMfaChallenge.type == challenge_type,
                WebMfaChallenge.token_jti == token_jti,
                WebMfaChallenge.challenge == challenge,
                WebMfaChallenge.used_at.is_(None),
            )
            .first()
        )
        if row is None:
            return
        row.used_at = datetime.utcnow()
        _safe_commit(db)
    finally:
        db.close()


def get_active_mfa_challenge(
    *,
    user_id: int,
    challenge_type: str,
    token_jti: str,
) -> Optional[WebMfaChallenge]:
    db = SessionLocal()
    try:
        row = (
            db.query(WebMfaChallenge)
            .filter(
                WebMfaChallenge.user_id == int(user_id),
                WebMfaChallenge.type == challenge_type,
                WebMfaChallenge.token_jti == token_jti,
                WebMfaChallenge.used_at.is_(None),
                WebMfaChallenge.expires_at > datetime.utcnow(),
            )
            .first()
        )
        return row
    finally:
        db.close()


def is_session_active(session_jti: str) -> bool:
    if not session_jti:
        return False
    db = SessionLocal()
    try:
        row = (
            db.query(WebUserSession)
            .filter(
                WebUserSession.session_jti == session_jti,
                WebUserSession.revoked_at.is_(None),
                WebUserSession.expires_at > datetime.utcnow(),
            )
            .first()
        )
        return row is not None
    finally:
        db.close()


def upsert_user_preference(
    *,
    user_id: int,
    tenant_id: str,
    values: dict[str, Any],
) -> Optional[WebUserPreference]:
    db = SessionLocal()
    try:
        row = (
            db.query(WebUserPreference)
            .filter(
                WebUserPreference.user_id == int(user_id),
                WebUserPreference.tenant_id == tenant_id,
            )
            .first()
        )
        if row is None:
            row = WebUserPreference(user_id=int(user_id), tenant_id=tenant_id)
            db.add(row)
        if "theme" in values:
            row.theme = str(values.get("theme") or "system")
        if "sidebar_mode" in values:
            row.sidebar_mode = str(values.get("sidebar_mode") or "expanded")
        if "default_home" in values:
            row.default_home = str(values.get("default_home") or "/inicio")
        if "favorite_modules_json" in values:
            row.favorite_modules_json = values.get("favorite_modules_json") or []
        if not _safe_commit(db):
            return None
        db.refresh(row)
        return row
    finally:
        db.close()


def log_security_event(
    *,
    tenant_id: str,
    event_type: str,
    user_id: Optional[int] = None,
    username: str = "",
    ip: str = "",
    user_agent: str = "",
    success: bool = True,
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    db = SessionLocal()
    try:
        db.add(
            WebSecurityEvent(
                tenant_id=tenant_id,
                event_type=(event_type or "").strip(),
                user_id=int(user_id) if user_id is not None else None,
                username=(username or "").strip(),
                ip=(ip or "").strip(),
                user_agent=(user_agent or "").strip(),
                success=bool(success),
                metadata_json=metadata or {},
            )
        )
        _safe_commit(db)
    finally:
        db.close()
