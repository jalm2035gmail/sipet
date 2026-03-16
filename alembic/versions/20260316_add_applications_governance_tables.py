"""add applications governance tables

Revision ID: 20260316_add_applications_governance_tables
Revises: 20260315_add_dashboard_preferences_table
Create Date: 2026-03-16
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260316_add_applications_governance_tables"
down_revision = "20260315_add_dashboard_preferences_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_registry_state",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("module_key", sa.String(length=120), nullable=False),
        sa.Column("tenant_id", sa.String(length=120), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("installed_version", sa.String(length=64), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_by", sa.String(length=255), nullable=True),
    )
    op.create_index("ix_app_registry_state_module_key", "app_registry_state", ["module_key"], unique=False)
    op.create_index("ix_app_registry_state_tenant_id", "app_registry_state", ["tenant_id"], unique=False)

    op.create_table(
        "app_registry_audit",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("module_key", sa.String(length=120), nullable=False),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("result", sa.String(length=80), nullable=False, server_default="pending"),
        sa.Column("user_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("ip", sa.String(length=64), nullable=True),
    )
    op.create_index("ix_app_registry_audit_module_key", "app_registry_audit", ["module_key"], unique=False)
    op.create_index("ix_app_registry_audit_action", "app_registry_audit", ["action"], unique=False)
    op.create_index("ix_app_registry_audit_result", "app_registry_audit", ["result"], unique=False)
    op.create_index("ix_app_registry_audit_user_id", "app_registry_audit", ["user_id"], unique=False)
    op.create_index("ix_app_registry_audit_created_at", "app_registry_audit", ["created_at"], unique=False)

    op.create_table(
        "app_protocol_audit",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("module_key", sa.String(length=120), nullable=False),
        sa.Column("has_init", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("has_manifest", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("missing_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("ok", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("scanned_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_app_protocol_audit_module_key", "app_protocol_audit", ["module_key"], unique=False)
    op.create_index("ix_app_protocol_audit_ok", "app_protocol_audit", ["ok"], unique=False)
    op.create_index("ix_app_protocol_audit_scanned_at", "app_protocol_audit", ["scanned_at"], unique=False)

    op.create_table(
        "app_package_upload",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("module_key", sa.String(length=120), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("uploaded_by", sa.String(length=255), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("applied", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_app_package_upload_module_key", "app_package_upload", ["module_key"], unique=False)
    op.create_index("ix_app_package_upload_checksum", "app_package_upload", ["checksum"], unique=False)
    op.create_index("ix_app_package_upload_uploaded_by", "app_package_upload", ["uploaded_by"], unique=False)
    op.create_index("ix_app_package_upload_uploaded_at", "app_package_upload", ["uploaded_at"], unique=False)
    op.create_index("ix_app_package_upload_applied", "app_package_upload", ["applied"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_app_package_upload_applied", table_name="app_package_upload")
    op.drop_index("ix_app_package_upload_uploaded_at", table_name="app_package_upload")
    op.drop_index("ix_app_package_upload_uploaded_by", table_name="app_package_upload")
    op.drop_index("ix_app_package_upload_checksum", table_name="app_package_upload")
    op.drop_index("ix_app_package_upload_module_key", table_name="app_package_upload")
    op.drop_table("app_package_upload")

    op.drop_index("ix_app_protocol_audit_scanned_at", table_name="app_protocol_audit")
    op.drop_index("ix_app_protocol_audit_ok", table_name="app_protocol_audit")
    op.drop_index("ix_app_protocol_audit_module_key", table_name="app_protocol_audit")
    op.drop_table("app_protocol_audit")

    op.drop_index("ix_app_registry_audit_created_at", table_name="app_registry_audit")
    op.drop_index("ix_app_registry_audit_user_id", table_name="app_registry_audit")
    op.drop_index("ix_app_registry_audit_result", table_name="app_registry_audit")
    op.drop_index("ix_app_registry_audit_action", table_name="app_registry_audit")
    op.drop_index("ix_app_registry_audit_module_key", table_name="app_registry_audit")
    op.drop_table("app_registry_audit")

    op.drop_index("ix_app_registry_state_tenant_id", table_name="app_registry_state")
    op.drop_index("ix_app_registry_state_module_key", table_name="app_registry_state")
    op.drop_table("app_registry_state")
