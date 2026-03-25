"""create web login identity table

Revision ID: 20260320_0002
Revises: 20260315_0001
Create Date: 2026-03-20 19:15:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260320_0002"
down_revision = "20260315_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "web_login_identity",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("singleton_key", sa.String(length=32), nullable=False, server_default="default"),
        sa.Column("favicon_filename", sa.String(length=255), nullable=False, server_default="icon.png"),
        sa.Column("logo_filename", sa.String(length=255), nullable=False, server_default="icon.png"),
        sa.Column("desktop_bg_filename", sa.String(length=255), nullable=False, server_default="fondo.jpg"),
        sa.Column("mobile_bg_filename", sa.String(length=255), nullable=False, server_default="movil.jpg"),
        sa.Column("company_short_name", sa.String(length=60), nullable=False, server_default="AVAN"),
        sa.Column(
            "login_message",
            sa.String(length=200),
            nullable=False,
            server_default="Incrementando el nivel de eficiencia",
        ),
        sa.Column("menu_position", sa.String(length=16), nullable=False, server_default="arriba"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_web_login_identity_id", "web_login_identity", ["id"], unique=False)
    op.create_index(
        "ix_web_login_identity_singleton_key",
        "web_login_identity",
        ["singleton_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_web_login_identity_singleton_key", table_name="web_login_identity")
    op.drop_index("ix_web_login_identity_id", table_name="web_login_identity")
    op.drop_table("web_login_identity")
