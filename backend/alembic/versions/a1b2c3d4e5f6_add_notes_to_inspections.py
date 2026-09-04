"""add notes to inspections

Revision ID: a1b2c3d4e5f6
Revises: 7057ad1ca86c
Create Date: 2026-09-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '7057ad1ca86c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add notes column to inspections table."""
    op.add_column("inspections", sa.Column("notes", sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove notes column from inspections table."""
    op.drop_column("inspections", "notes")
