"""add empresa access fields to web users

Revision ID: 20260402_0004
Revises: 20260324_0003
Create Date: 2026-04-02 12:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260402_0004"
down_revision = "20260324_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("users")}

    if "app_access" not in existing_columns:
        op.add_column("users", sa.Column("app_access", sa.Text(), nullable=True))
    if "menu_blocks" not in existing_columns:
        op.add_column("users", sa.Column("menu_blocks", sa.Text(), nullable=True))
    if "conversation_access" not in existing_columns:
        op.add_column("users", sa.Column("conversation_access", sa.Text(), nullable=True))
    if "is_employee" not in existing_columns:
        op.add_column("users", sa.Column("is_employee", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("users")}

    if "is_employee" in existing_columns:
        op.drop_column("users", "is_employee")
    if "conversation_access" in existing_columns:
        op.drop_column("users", "conversation_access")
    if "menu_blocks" in existing_columns:
        op.drop_column("users", "menu_blocks")
    if "app_access" in existing_columns:
        op.drop_column("users", "app_access")
