"""pwa v2: conversations, notifications, push subscriptions + refuerzo sipet tables

Revision ID: 0001pwa2conv
Revises:
Create Date: 2026-04-02
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "0001pwa2conv"
down_revision = None
branch_labels = None
depends_on = None


# ─────────────────────────────────────────────────────────────────────────────
# UPGRADE
# ─────────────────────────────────────────────────────────────────────────────

def upgrade() -> None:

    # ── pwa_conversations ─────────────────────────────────────────────────────
    op.create_table(
        "pwa_conversations",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("ref_type", sa.String(50), nullable=True),
        sa.Column("ref_id", sa.Integer, nullable=True),
        sa.Column("created_by_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── pwa_conversation_participants ─────────────────────────────────────────
    op.create_table(
        "pwa_conversation_participants",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "conversation_id",
            sa.Integer,
            sa.ForeignKey("pwa_conversations.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="member"),
        sa.Column("last_read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("conversation_id", "user_id", name="uq_conv_participant"),
    )

    # ── pwa_messages ──────────────────────────────────────────────────────────
    op.create_table(
        "pwa_messages",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "conversation_id",
            sa.Integer,
            sa.ForeignKey("pwa_conversations.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("sender_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("reply_to_id", sa.Integer, sa.ForeignKey("pwa_messages.id"), nullable=True),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── pwa_message_mentions ──────────────────────────────────────────────────
    op.create_table(
        "pwa_message_mentions",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "message_id",
            sa.Integer,
            sa.ForeignKey("pwa_messages.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "mentioned_user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False
        ),
    )

    # ── pwa_message_attachments ───────────────────────────────────────────────
    op.create_table(
        "pwa_message_attachments",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "message_id",
            sa.Integer,
            sa.ForeignKey("pwa_messages.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_url", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("size_bytes", sa.Integer, nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── pwa_message_read_receipts ─────────────────────────────────────────────
    op.create_table(
        "pwa_message_read_receipts",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "message_id",
            sa.Integer,
            sa.ForeignKey("pwa_messages.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("message_id", "user_id", name="uq_msg_read_user"),
    )

    # ── pwa_notifications ─────────────────────────────────────────────────────
    op.create_table(
        "pwa_notifications",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("event_type", sa.String(20), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text, nullable=True),
        sa.Column("ref_type", sa.String(50), nullable=True),
        sa.Column("ref_id", sa.Integer, nullable=True),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_archived", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── pwa_notification_rules ────────────────────────────────────────────────
    op.create_table(
        "pwa_notification_rules",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("event_type", sa.String(20), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("channels", sa.JSON, nullable=True),
        sa.Column("cooldown_minutes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── pwa_user_notification_preferences ────────────────────────────────────
    op.create_table(
        "pwa_user_notification_preferences",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("event_type", sa.String(20), nullable=False),
        sa.Column("in_app_enabled", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("email_enabled", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("push_enabled", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("user_id", "event_type", name="uq_user_event_pref"),
    )

    # ── pwa_notification_delivery_logs ────────────────────────────────────────
    op.create_table(
        "pwa_notification_delivery_logs",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "notification_id",
            sa.Integer,
            sa.ForeignKey("pwa_notifications.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_detail", sa.Text, nullable=True),
    )

    # ── pwa_push_subscriptions ────────────────────────────────────────────────
    op.create_table(
        "pwa_push_subscriptions",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("endpoint", sa.Text, nullable=False),
        sa.Column("p256dh", sa.Text, nullable=False),
        sa.Column("auth", sa.Text, nullable=False),
        sa.Column("user_agent", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── Refuerzo sipet_kpis ───────────────────────────────────────────────────
    with op.batch_alter_table("sipet_kpis") as batch_op:
        batch_op.add_column(
            sa.Column("responsible_user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True)
        )
        batch_op.add_column(
            sa.Column("last_updated_at", sa.DateTime(timezone=True), nullable=True)
        )

    # ── Refuerzo sipet_activities ─────────────────────────────────────────────
    with op.batch_alter_table("sipet_activities") as batch_op:
        batch_op.add_column(
            sa.Column("responsible_user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True)
        )
        batch_op.add_column(sa.Column("area", sa.String(120), nullable=True))
        batch_op.add_column(
            sa.Column("approved_by_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True)
        )
        batch_op.add_column(
            sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True)
        )

    # ── Refuerzo sipet_activity_evidences ─────────────────────────────────────
    with op.batch_alter_table("sipet_activity_evidences") as batch_op:
        batch_op.add_column(
            sa.Column("uploaded_by_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True)
        )
        batch_op.add_column(
            sa.Column("status", sa.String(20), nullable=False, server_default="pending")
        )
        batch_op.add_column(
            sa.Column("reviewed_by_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True)
        )
        batch_op.add_column(
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(sa.Column("review_note", sa.Text, nullable=True))
        batch_op.add_column(sa.Column("ref_type", sa.String(50), nullable=True))
        batch_op.add_column(sa.Column("ref_id", sa.Integer, nullable=True))
        # make activity_id nullable (batch handles sqlite ALTER limitation)
        batch_op.alter_column("activity_id", existing_type=sa.Integer(), nullable=True)


# ─────────────────────────────────────────────────────────────────────────────
# DOWNGRADE
# ─────────────────────────────────────────────────────────────────────────────

def downgrade() -> None:

    # ── Revertir columnas sipet_activity_evidences ────────────────────────────
    with op.batch_alter_table("sipet_activity_evidences") as batch_op:
        batch_op.alter_column("activity_id", existing_type=sa.Integer(), nullable=False)
        for col in ("ref_id", "ref_type", "review_note", "reviewed_at",
                    "reviewed_by_id", "status", "uploaded_by_id"):
            batch_op.drop_column(col)

    # ── Revertir columnas sipet_activities ────────────────────────────────────
    with op.batch_alter_table("sipet_activities") as batch_op:
        for col in ("approved_at", "approved_by_id", "area", "responsible_user_id"):
            batch_op.drop_column(col)

    # ── Revertir columnas sipet_kpis ──────────────────────────────────────────
    with op.batch_alter_table("sipet_kpis") as batch_op:
        for col in ("last_updated_at", "responsible_user_id"):
            batch_op.drop_column(col)

    # ── Eliminar tablas pwa_* (en orden inverso de FK) ────────────────────────
    op.drop_table("pwa_push_subscriptions")
    op.drop_table("pwa_notification_delivery_logs")
    op.drop_table("pwa_user_notification_preferences")
    op.drop_table("pwa_notification_rules")
    op.drop_table("pwa_notifications")
    op.drop_table("pwa_message_read_receipts")
    op.drop_table("pwa_message_attachments")
    op.drop_table("pwa_message_mentions")
    op.drop_table("pwa_messages")
    op.drop_table("pwa_conversation_participants")
    op.drop_table("pwa_conversations")
