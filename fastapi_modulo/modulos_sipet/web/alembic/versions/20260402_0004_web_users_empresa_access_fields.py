"""add empresa access fields to web users

Revision ID: 20260402_0004
Revises: 20260324_0003
Create Date: 2026-04-02 12:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260402_0004"
down_revision = "20260324_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("app_access", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("menu_blocks", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("conversation_access", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("is_employee", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column("users", "is_employee")
    op.drop_column("users", "conversation_access")
    op.drop_column("users", "menu_blocks")
    op.drop_column("users", "app_access")
