"""drop name column from users

Revision ID: 54a85198382a
Revises: e1aba83953d1
Create Date: 2026-09-03 15:59:49.808651

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '54a85198382a'
down_revision: Union[str, Sequence[str], None] = 'e1aba83953d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop the name column from users table."""
    op.drop_column('users', 'name')


def downgrade() -> None:
    """Add back the name column to users table."""
    op.add_column('users', sa.Column('name', sa.VARCHAR(length=255), nullable=False))
