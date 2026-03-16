from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Index, Integer, String, Text

from fastapi_modulo.db import MAIN


class WebLoginAttempt(MAIN):
    __tablename__ = "web_login_attempt"
    __table_args__ = (
        Index("ix_web_login_attempt_tenant_username_created", "tenant_id", "username", "created_at"),
        Index("ix_web_login_attempt_ip_created", "ip", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    username = Column(String(255), nullable=False, default="", index=True)
    ip = Column(String(64), nullable=False, default="", index=True)
    user_agent = Column(Text, nullable=False, default="")
    success = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class WebUserSession(MAIN):
    __tablename__ = "web_user_session"
    __table_args__ = (
        Index("ix_web_user_session_user_tenant_revoked", "user_id", "tenant_id", "revoked_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    session_jti = Column(String(64), nullable=False, unique=True, index=True)
    ip = Column(String(64), nullable=False, default="")
    user_agent = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    revoked_at = Column(DateTime, nullable=True, index=True)


class WebMfaChallenge(MAIN):
    __tablename__ = "web_mfa_challenge"
    __table_args__ = (
        Index("ix_web_mfa_challenge_user_type_used", "user_id", "type", "used_at"),
        Index("ix_web_mfa_challenge_type_expires", "type", "expires_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True)
    token_jti = Column(String(64), nullable=False, unique=True, index=True)
    challenge = Column(String(512), nullable=False, unique=True, index=True)
    origin = Column(String(255), nullable=False, default="")
    rp_id = Column(String(255), nullable=False, default="")
    expires_at = Column(DateTime, nullable=False, index=True)
    used_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class WebUserPreference(MAIN):
    __tablename__ = "web_user_preference"
    __table_args__ = (
        Index("ix_web_user_preference_user_tenant", "user_id", "tenant_id", unique=True),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    theme = Column(String(32), nullable=False, default="system")
    sidebar_mode = Column(String(32), nullable=False, default="expanded")
    default_home = Column(String(255), nullable=False, default="/inicio")
    favorite_modules_json = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class WebSecurityEvent(MAIN):
    __tablename__ = "web_security_event"
    __table_args__ = (
        Index("ix_web_security_event_tenant_created", "tenant_id", "created_at"),
        Index("ix_web_security_event_user_created", "user_id", "created_at"),
        Index("ix_web_security_event_type_created", "event_type", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    user_id = Column(Integer, nullable=True, index=True)
    username = Column(String(255), nullable=False, default="", index=True)
    event_type = Column(String(80), nullable=False, default="", index=True)
    ip = Column(String(64), nullable=False, default="")
    user_agent = Column(Text, nullable=False, default="")
    success = Column(Boolean, nullable=False, default=True, index=True)
    metadata_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
