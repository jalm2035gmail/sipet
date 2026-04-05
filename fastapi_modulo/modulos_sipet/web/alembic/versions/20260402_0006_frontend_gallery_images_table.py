"""add frontend_gallery_images table

Revision ID: 20260402_0006
Revises: 20260402_0005
Create Date: 2026-04-02 14:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260402_0006"
down_revision = "20260402_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "frontend_gallery_images",
        sa.Column("id",         sa.String(),  primary_key=True),
        sa.Column("filename",   sa.String(),  nullable=False),
        sa.Column("orig_name",  sa.String(),  nullable=False, server_default=""),
        sa.Column("status",     sa.String(),  nullable=False, server_default="uploaded"),
        sa.Column("url",        sa.String(),  nullable=False, server_default=""),
        sa.Column("size_kb",    sa.Float(),   nullable=False, server_default="0"),
        sa.Column("error",      sa.String(),  nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_frontend_gallery_images_id",         "frontend_gallery_images", ["id"])
    op.create_index("ix_frontend_gallery_images_filename",   "frontend_gallery_images", ["filename"])
    op.create_index("ix_frontend_gallery_images_status",     "frontend_gallery_images", ["status"])
    op.create_index("ix_frontend_gallery_images_created_at", "frontend_gallery_images", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_frontend_gallery_images_created_at", table_name="frontend_gallery_images")
    op.drop_index("ix_frontend_gallery_images_status",     table_name="frontend_gallery_images")
    op.drop_index("ix_frontend_gallery_images_filename",   table_name="frontend_gallery_images")
    op.drop_index("ix_frontend_gallery_images_id",         table_name="frontend_gallery_images")
    op.drop_table("frontend_gallery_images")
