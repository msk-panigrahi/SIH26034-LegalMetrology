"""add compliance_results table

Revision ID: 71fbe2d625d5
Revises: 60a4523a29e6
Create Date: 2026-09-03 13:53:10.517129

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '71fbe2d625d5'
down_revision: Union[str, Sequence[str], None] = '60a4523a29e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create compliance_results table for storing full compliance evaluations."""
    op.create_table(
        "compliance_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("inspection_id", sa.Integer(), nullable=False),
        sa.Column("overall_status", sa.String(length=50), nullable=False),
        sa.Column("rule_version", sa.String(length=50), nullable=False),
        sa.Column("rules_checked", sa.Integer(), nullable=False),
        sa.Column("passed_count", sa.Integer(), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False),
        sa.Column("warning_count", sa.Integer(), nullable=False),
        sa.Column("not_verifiable_count", sa.Integer(), nullable=False),
        sa.Column("not_applicable_count", sa.Integer(), nullable=False),
        sa.Column("results_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["inspection_id"], ["inspections.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("inspection_id"),
    )
    op.create_index(op.f("ix_compliance_results_id"), "compliance_results", ["id"], unique=False)


def downgrade() -> None:
    """Drop compliance_results table."""
    op.drop_index(op.f("ix_compliance_results_id"), table_name="compliance_results")
    op.drop_table("compliance_results")
