"""create conversation tables

Revision ID: 001_conv_tables
Revises:
Create Date: 2026-03-18
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "001_conv_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_direct_messages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("conversation_id", sa.String(length=255), nullable=False),
        sa.Column("from_username", sa.String(length=120), nullable=False),
        sa.Column("to_usernames", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("message_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_udm_conv",
        "user_direct_messages",
        ["conversation_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_udm_from",
        "user_direct_messages",
        ["from_username", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_udm_read",
        "user_direct_messages",
        ["from_username", "is_read"],
        unique=False,
    )

    op.create_table(
        "conversation_groups",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("conversation_id", sa.String(length=255), nullable=False),
        sa.Column("group_name", sa.String(length=120), nullable=False),
        sa.Column("created_by", sa.String(length=120), nullable=False),
        sa.Column("member_usernames", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("conversation_id", name="uq_conversation_groups_conversation_id"),
    )
    op.create_index("ix_cg_conv", "conversation_groups", ["conversation_id"], unique=False)

    op.create_table(
        "conversation_group_messages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("conversation_id", sa.String(length=255), nullable=False),
        sa.Column("from_username", sa.String(length=120), nullable=False),
        sa.Column("to_usernames", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("message_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_cgm_conv",
        "conversation_group_messages",
        ["conversation_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_cgm_read",
        "conversation_group_messages",
        ["from_username", "is_read"],
        unique=False,
    )

    op.create_table(
        "conversation_notifications",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("from_username", sa.String(length=120), nullable=False),
        sa.Column("to_usernames", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("message_text", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "scope",
            sa.String(length=32),
            nullable=False,
            server_default="conversation",
        ),
        sa.Column("conversation_id", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_cn_to_read",
        "conversation_notifications",
        ["is_read", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_cn_to_read", table_name="conversation_notifications")
    op.drop_table("conversation_notifications")

    op.drop_index("ix_cgm_read", table_name="conversation_group_messages")
    op.drop_index("ix_cgm_conv", table_name="conversation_group_messages")
    op.drop_table("conversation_group_messages")

    op.drop_index("ix_cg_conv", table_name="conversation_groups")
    op.drop_table("conversation_groups")

    op.drop_index("ix_udm_read", table_name="user_direct_messages")
    op.drop_index("ix_udm_from", table_name="user_direct_messages")
    op.drop_index("ix_udm_conv", table_name="user_direct_messages")
    op.drop_table("user_direct_messages")
