"""add tenant admin tables

Revision ID: 20260316_add_tenant_admin_tables
Revises: 20260316_add_applications_governance_tables
Create Date: 2026-03-16
"""

from alembic import op
import sqlalchemy as sa


revision = "20260316_add_tenant_admin_tables"
down_revision = "20260316_add_applications_governance_tables"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade():
    if not _table_exists("tenant_registry"):
        op.create_table(
            "tenant_registry",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("tenant_key", sa.String(), nullable=False),
            sa.Column("primary_host", sa.String(), nullable=False),
            sa.Column("db_name", sa.String(), nullable=False, server_default=""),
            sa.Column("db_url", sa.String(), nullable=False, server_default=""),
            sa.Column("plan", sa.String(), nullable=False, server_default="base"),
            sa.Column("status", sa.String(), nullable=False, server_default="active"),
            sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_tenant_registry_id", "tenant_registry", ["id"])
        op.create_index("ix_tenant_registry_tenant_key", "tenant_registry", ["tenant_key"], unique=True)
        op.create_index("ix_tenant_registry_primary_host", "tenant_registry", ["primary_host"], unique=True)
        op.create_index("ix_tenant_registry_status", "tenant_registry", ["status"])
        op.create_index("ix_tenant_registry_is_active", "tenant_registry", ["is_active"])

    if not _table_exists("tenant_domains"):
        op.create_table(
            "tenant_domains",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("tenant_key", sa.String(), nullable=False),
            sa.Column("host", sa.String(), nullable=False),
            sa.Column("domain_type", sa.String(), nullable=False, server_default="primary"),
            sa.Column("certificate_status", sa.String(), nullable=False, server_default="pending"),
            sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_tenant_domains_id", "tenant_domains", ["id"])
        op.create_index("ix_tenant_domains_tenant_key", "tenant_domains", ["tenant_key"])
        op.create_index("ix_tenant_domains_host", "tenant_domains", ["host"], unique=True)
        op.create_index("ix_tenant_domains_is_active", "tenant_domains", ["is_active"])

    if not _table_exists("tenant_installed_apps"):
        op.create_table(
            "tenant_installed_apps",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("tenant_key", sa.String(), nullable=False),
            sa.Column("app_key", sa.String(), nullable=False),
            sa.Column("app_version", sa.String(), nullable=False, server_default="0.0.0"),
            sa.Column("install_status", sa.String(), nullable=False, server_default="installed"),
            sa.Column("is_enabled", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("installed_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_tenant_installed_apps_id", "tenant_installed_apps", ["id"])
        op.create_index("ix_tenant_installed_apps_tenant_key", "tenant_installed_apps", ["tenant_key"])
        op.create_index("ix_tenant_installed_apps_app_key", "tenant_installed_apps", ["app_key"])
        op.create_index("ix_tenant_installed_apps_install_status", "tenant_installed_apps", ["install_status"])
        op.create_index("ix_tenant_installed_apps_is_enabled", "tenant_installed_apps", ["is_enabled"])

    if not _table_exists("tenant_provision_logs"):
        op.create_table(
            "tenant_provision_logs",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("tenant_key", sa.String(), nullable=False),
            sa.Column("action", sa.String(), nullable=False, server_default="create"),
            sa.Column("status", sa.String(), nullable=False, server_default="pending"),
            sa.Column("detail", sa.Text(), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_tenant_provision_logs_id", "tenant_provision_logs", ["id"])
        op.create_index("ix_tenant_provision_logs_tenant_key", "tenant_provision_logs", ["tenant_key"])
        op.create_index("ix_tenant_provision_logs_status", "tenant_provision_logs", ["status"])


def downgrade():
    if _table_exists("tenant_provision_logs"):
        op.drop_index("ix_tenant_provision_logs_status", table_name="tenant_provision_logs")
        op.drop_index("ix_tenant_provision_logs_tenant_key", table_name="tenant_provision_logs")
        op.drop_index("ix_tenant_provision_logs_id", table_name="tenant_provision_logs")
        op.drop_table("tenant_provision_logs")
    if _table_exists("tenant_installed_apps"):
        op.drop_index("ix_tenant_installed_apps_is_enabled", table_name="tenant_installed_apps")
        op.drop_index("ix_tenant_installed_apps_install_status", table_name="tenant_installed_apps")
        op.drop_index("ix_tenant_installed_apps_app_key", table_name="tenant_installed_apps")
        op.drop_index("ix_tenant_installed_apps_tenant_key", table_name="tenant_installed_apps")
        op.drop_index("ix_tenant_installed_apps_id", table_name="tenant_installed_apps")
        op.drop_table("tenant_installed_apps")
    if _table_exists("tenant_domains"):
        op.drop_index("ix_tenant_domains_is_active", table_name="tenant_domains")
        op.drop_index("ix_tenant_domains_host", table_name="tenant_domains")
        op.drop_index("ix_tenant_domains_tenant_key", table_name="tenant_domains")
        op.drop_index("ix_tenant_domains_id", table_name="tenant_domains")
        op.drop_table("tenant_domains")
    if _table_exists("tenant_registry"):
        op.drop_index("ix_tenant_registry_is_active", table_name="tenant_registry")
        op.drop_index("ix_tenant_registry_status", table_name="tenant_registry")
        op.drop_index("ix_tenant_registry_primary_host", table_name="tenant_registry")
        op.drop_index("ix_tenant_registry_tenant_key", table_name="tenant_registry")
        op.drop_index("ix_tenant_registry_id", table_name="tenant_registry")
        op.drop_table("tenant_registry")
