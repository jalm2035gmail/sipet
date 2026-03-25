"""add login logo filename to web login identity

Revision ID: 20260324_0003
Revises: 20260320_0002
Create Date: 2026-03-24 12:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260324_0003"
down_revision = "20260320_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "web_login_identity",
        sa.Column("login_logo_filename", sa.String(length=255), nullable=False, server_default="icon.png"),
    )


def downgrade() -> None:
    op.drop_column("web_login_identity", "login_logo_filename")
