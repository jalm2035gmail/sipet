"""add dashboard preferences table

Revision ID: 20260315_add_dashboard_preferences_table
Revises: 20260312_add_encuestas_tables
Create Date: 2026-03-15
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260315_add_dashboard_preferences_table"
down_revision = "20260312_add_encuestas_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dashboard_preferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tenant_id", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("item_key", sa.String(length=120), nullable=False),
        sa.Column("item_title", sa.String(length=200), nullable=True),
        sa.Column("priority_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_favorite", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("theme", sa.String(length=32), nullable=True),
        sa.Column("layout", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_dashboard_preferences_user_id", "dashboard_preferences", ["user_id"])
    op.create_index("ix_dashboard_preferences_tenant_id", "dashboard_preferences", ["tenant_id"])
    op.create_index("ix_dashboard_preferences_item_key", "dashboard_preferences", ["item_key"])


def downgrade() -> None:
    op.drop_index("ix_dashboard_preferences_item_key", table_name="dashboard_preferences")
    op.drop_index("ix_dashboard_preferences_tenant_id", table_name="dashboard_preferences")
    op.drop_index("ix_dashboard_preferences_user_id", table_name="dashboard_preferences")
    op.drop_table("dashboard_preferences")
