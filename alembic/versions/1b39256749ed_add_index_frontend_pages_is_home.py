"""add index on frontend_pages.is_home

Revision ID: 1b39256749ed
Revises: 8d6c7410e0b7
Create Date: 2026-04-02

Motivo: la consulta de página home pública filtra por is_home=True en cada
request. Sin índice eso provoca un full-scan de frontend_pages.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '1b39256749ed'
down_revision: Union[str, Sequence[str], None] = '8d6c7410e0b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        'ix_frontend_pages_is_home',
        'frontend_pages',
        ['is_home'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_frontend_pages_is_home', table_name='frontend_pages')
