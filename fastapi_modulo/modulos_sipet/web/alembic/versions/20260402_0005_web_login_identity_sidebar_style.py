"""add sidebar style variant to web login identity

Revision ID: 20260402_0005
Revises: 20260402_0004
Create Date: 2026-04-02 13:10:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260402_0005"
down_revision = "20260402_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "web_login_identity",
        sa.Column("sidebar_style_variant", sa.String(length=16), nullable=False, server_default="modern"),
    )


def downgrade() -> None:
    op.drop_column("web_login_identity", "sidebar_style_variant")
