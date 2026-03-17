"""create web security and preference tables

Revision ID: 20260315_0001
Revises:
Create Date: 2026-03-15 20:30:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260315_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "web_login_attempt",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=False, server_default="default"),
        sa.Column("username", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("ip", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("user_agent", sa.Text(), nullable=False, server_default=""),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_web_login_attempt_id", "web_login_attempt", ["id"], unique=False)
    op.create_index("ix_web_login_attempt_tenant_id", "web_login_attempt", ["tenant_id"], unique=False)
    op.create_index("ix_web_login_attempt_username", "web_login_attempt", ["username"], unique=False)
    op.create_index("ix_web_login_attempt_ip", "web_login_attempt", ["ip"], unique=False)
    op.create_index("ix_web_login_attempt_success", "web_login_attempt", ["success"], unique=False)
    op.create_index("ix_web_login_attempt_created_at", "web_login_attempt", ["created_at"], unique=False)
    op.create_index(
        "ix_web_login_attempt_tenant_username_created",
        "web_login_attempt",
        ["tenant_id", "username", "created_at"],
        unique=False,
    )
    op.create_index("ix_web_login_attempt_ip_created", "web_login_attempt", ["ip", "created_at"], unique=False)

    op.create_table(
        "web_user_session",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=False, server_default="default"),
        sa.Column("session_jti", sa.String(length=64), nullable=False),
        sa.Column("ip", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("user_agent", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_web_user_session_id", "web_user_session", ["id"], unique=False)
    op.create_index("ix_web_user_session_user_id", "web_user_session", ["user_id"], unique=False)
    op.create_index("ix_web_user_session_tenant_id", "web_user_session", ["tenant_id"], unique=False)
    op.create_index("ix_web_user_session_session_jti", "web_user_session", ["session_jti"], unique=True)
    op.create_index("ix_web_user_session_created_at", "web_user_session", ["created_at"], unique=False)
    op.create_index("ix_web_user_session_expires_at", "web_user_session", ["expires_at"], unique=False)
    op.create_index("ix_web_user_session_revoked_at", "web_user_session", ["revoked_at"], unique=False)
    op.create_index(
        "ix_web_user_session_user_tenant_revoked",
        "web_user_session",
        ["user_id", "tenant_id", "revoked_at"],
        unique=False,
    )

    op.create_table(
        "web_mfa_challenge",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("token_jti", sa.String(length=64), nullable=False),
        sa.Column("challenge", sa.String(length=512), nullable=False),
        sa.Column("origin", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("rp_id", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_web_mfa_challenge_id", "web_mfa_challenge", ["id"], unique=False)
    op.create_index("ix_web_mfa_challenge_user_id", "web_mfa_challenge", ["user_id"], unique=False)
    op.create_index("ix_web_mfa_challenge_type", "web_mfa_challenge", ["type"], unique=False)
    op.create_index("ix_web_mfa_challenge_challenge", "web_mfa_challenge", ["challenge"], unique=True)
    op.create_index("ix_web_mfa_challenge_expires_at", "web_mfa_challenge", ["expires_at"], unique=False)
    op.create_index("ix_web_mfa_challenge_used_at", "web_mfa_challenge", ["used_at"], unique=False)
    op.create_index("ix_web_mfa_challenge_created_at", "web_mfa_challenge", ["created_at"], unique=False)
    op.create_index(
        "ix_web_mfa_challenge_user_type_used",
        "web_mfa_challenge",
        ["user_id", "type", "used_at"],
        unique=False,
    )
    op.create_index("ix_web_mfa_challenge_type_expires", "web_mfa_challenge", ["type", "expires_at"], unique=False)

    op.create_table(
        "web_user_preference",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=False, server_default="default"),
        sa.Column("theme", sa.String(length=32), nullable=False, server_default="system"),
        sa.Column("sidebar_mode", sa.String(length=32), nullable=False, server_default="expanded"),
        sa.Column("default_home", sa.String(length=255), nullable=False, server_default="/inicio"),
        sa.Column("favorite_modules_json", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_web_user_preference_id", "web_user_preference", ["id"], unique=False)
    op.create_index("ix_web_user_preference_user_id", "web_user_preference", ["user_id"], unique=False)
    op.create_index("ix_web_user_preference_tenant_id", "web_user_preference", ["tenant_id"], unique=False)
    op.create_index(
        "ix_web_user_preference_user_tenant",
        "web_user_preference",
        ["user_id", "tenant_id"],
        unique=True,
    )

    op.create_table(
        "web_security_event",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=False, server_default="default"),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("username", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("event_type", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("ip", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("user_agent", sa.Text(), nullable=False, server_default=""),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_web_security_event_id", "web_security_event", ["id"], unique=False)
    op.create_index("ix_web_security_event_tenant_id", "web_security_event", ["tenant_id"], unique=False)
    op.create_index("ix_web_security_event_user_id", "web_security_event", ["user_id"], unique=False)
    op.create_index("ix_web_security_event_username", "web_security_event", ["username"], unique=False)
    op.create_index("ix_web_security_event_event_type", "web_security_event", ["event_type"], unique=False)
    op.create_index("ix_web_security_event_success", "web_security_event", ["success"], unique=False)
    op.create_index("ix_web_security_event_created_at", "web_security_event", ["created_at"], unique=False)
    op.create_index("ix_web_security_event_tenant_created", "web_security_event", ["tenant_id", "created_at"], unique=False)
    op.create_index("ix_web_security_event_user_created", "web_security_event", ["user_id", "created_at"], unique=False)
    op.create_index("ix_web_security_event_type_created", "web_security_event", ["event_type", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_web_security_event_type_created", table_name="web_security_event")
    op.drop_index("ix_web_security_event_user_created", table_name="web_security_event")
    op.drop_index("ix_web_security_event_tenant_created", table_name="web_security_event")
    op.drop_index("ix_web_security_event_created_at", table_name="web_security_event")
    op.drop_index("ix_web_security_event_success", table_name="web_security_event")
    op.drop_index("ix_web_security_event_event_type", table_name="web_security_event")
    op.drop_index("ix_web_security_event_username", table_name="web_security_event")
    op.drop_index("ix_web_security_event_user_id", table_name="web_security_event")
    op.drop_index("ix_web_security_event_tenant_id", table_name="web_security_event")
    op.drop_index("ix_web_security_event_id", table_name="web_security_event")
    op.drop_table("web_security_event")

    op.drop_index("ix_web_user_preference_user_tenant", table_name="web_user_preference")
    op.drop_index("ix_web_user_preference_tenant_id", table_name="web_user_preference")
    op.drop_index("ix_web_user_preference_user_id", table_name="web_user_preference")
    op.drop_index("ix_web_user_preference_id", table_name="web_user_preference")
    op.drop_table("web_user_preference")

    op.drop_index("ix_web_mfa_challenge_type_expires", table_name="web_mfa_challenge")
    op.drop_index("ix_web_mfa_challenge_user_type_used", table_name="web_mfa_challenge")
    op.drop_index("ix_web_mfa_challenge_created_at", table_name="web_mfa_challenge")
    op.drop_index("ix_web_mfa_challenge_used_at", table_name="web_mfa_challenge")
    op.drop_index("ix_web_mfa_challenge_expires_at", table_name="web_mfa_challenge")
    op.drop_index("ix_web_mfa_challenge_challenge", table_name="web_mfa_challenge")
    op.drop_index("ix_web_mfa_challenge_type", table_name="web_mfa_challenge")
    op.drop_index("ix_web_mfa_challenge_user_id", table_name="web_mfa_challenge")
    op.drop_index("ix_web_mfa_challenge_id", table_name="web_mfa_challenge")
    op.drop_table("web_mfa_challenge")

    op.drop_index("ix_web_user_session_user_tenant_revoked", table_name="web_user_session")
    op.drop_index("ix_web_user_session_revoked_at", table_name="web_user_session")
    op.drop_index("ix_web_user_session_expires_at", table_name="web_user_session")
    op.drop_index("ix_web_user_session_created_at", table_name="web_user_session")
    op.drop_index("ix_web_user_session_session_jti", table_name="web_user_session")
    op.drop_index("ix_web_user_session_tenant_id", table_name="web_user_session")
    op.drop_index("ix_web_user_session_user_id", table_name="web_user_session")
    op.drop_index("ix_web_user_session_id", table_name="web_user_session")
    op.drop_table("web_user_session")

    op.drop_index("ix_web_login_attempt_ip_created", table_name="web_login_attempt")
    op.drop_index("ix_web_login_attempt_tenant_username_created", table_name="web_login_attempt")
    op.drop_index("ix_web_login_attempt_created_at", table_name="web_login_attempt")
    op.drop_index("ix_web_login_attempt_success", table_name="web_login_attempt")
    op.drop_index("ix_web_login_attempt_ip", table_name="web_login_attempt")
    op.drop_index("ix_web_login_attempt_username", table_name="web_login_attempt")
    op.drop_index("ix_web_login_attempt_tenant_id", table_name="web_login_attempt")
    op.drop_index("ix_web_login_attempt_id", table_name="web_login_attempt")
    op.drop_table("web_login_attempt")
