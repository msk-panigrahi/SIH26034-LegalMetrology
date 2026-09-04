"""add ocr_results table for field extraction

Revision ID: 60a4523a29e6
Revises: a1b2c3d4e5f6
Create Date: 2026-09-03 10:56:17.505395

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '60a4523a29e6'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create ocr_results table for storing OCR text and extracted fields."""
    op.create_table(
        "ocr_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("inspection_id", sa.Integer(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("ocr_confidence", sa.Float(), nullable=True),
        sa.Column("extracted_fields", sa.JSON(), nullable=True),
        sa.Column("extraction_status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["inspection_id"], ["inspections.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("inspection_id"),
    )
    op.create_index(op.f("ix_ocr_results_id"), "ocr_results", ["id"], unique=False)


def downgrade() -> None:
    """Drop ocr_results table."""
    op.drop_index(op.f("ix_ocr_results_id"), table_name="ocr_results")
    op.drop_table("ocr_results")
