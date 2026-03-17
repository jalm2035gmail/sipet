"""add tenant migration runs table

Revision ID: 20260316_add_tenant_migration_runs_table
Revises: 20260316_add_tenant_admin_tables
Create Date: 2026-03-16
"""

from alembic import op
import sqlalchemy as sa


revision = "20260316_add_tenant_migration_runs_table"
down_revision = "20260316_add_tenant_admin_tables"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade():
    if _table_exists("tenant_migration_runs"):
        return
    op.create_table(
        "tenant_migration_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("tenant_key", sa.String(), nullable=False),
        sa.Column("target_scope", sa.String(), nullable=False, server_default="tenant"),
        sa.Column("migration_key", sa.String(), nullable=False, server_default="core"),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("detail", sa.Text(), nullable=False, server_default=""),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_tenant_migration_runs_id", "tenant_migration_runs", ["id"])
    op.create_index("ix_tenant_migration_runs_tenant_key", "tenant_migration_runs", ["tenant_key"])
    op.create_index("ix_tenant_migration_runs_target_scope", "tenant_migration_runs", ["target_scope"])
    op.create_index("ix_tenant_migration_runs_migration_key", "tenant_migration_runs", ["migration_key"])
    op.create_index("ix_tenant_migration_runs_status", "tenant_migration_runs", ["status"])


def downgrade():
    if not _table_exists("tenant_migration_runs"):
        return
    op.drop_index("ix_tenant_migration_runs_status", table_name="tenant_migration_runs")
    op.drop_index("ix_tenant_migration_runs_migration_key", table_name="tenant_migration_runs")
    op.drop_index("ix_tenant_migration_runs_target_scope", table_name="tenant_migration_runs")
    op.drop_index("ix_tenant_migration_runs_tenant_key", table_name="tenant_migration_runs")
    op.drop_index("ix_tenant_migration_runs_id", table_name="tenant_migration_runs")
    op.drop_table("tenant_migration_runs")
