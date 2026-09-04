"""add reports table and update user model

Revision ID: e1aba83953d1
Revises: 71fbe2d625d5
Create Date: 2026-09-03 15:50:30.114799

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e1aba83953d1'
down_revision: Union[str, Sequence[str], None] = '71fbe2d625d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add reports table and update users table."""
    # Create reports table
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("inspection_id", sa.Integer(), nullable=False),
        sa.Column("generated_by", sa.Integer(), nullable=False),
        sa.Column("report_number", sa.String(length=50), nullable=False),
        sa.Column("report_status", sa.String(length=50), nullable=False),
        sa.Column("report_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["generated_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["inspection_id"], ["inspections.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("inspection_id"),
    )
    op.create_index(op.f("ix_reports_id"), "reports", ["id"], unique=False)
    op.create_index(op.f("ix_reports_report_number"), "reports", ["report_number"], unique=True)

    # Update users table - add new columns
    op.add_column("users", sa.Column("full_name", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("username", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"))
    op.add_column("users", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    # Copy name to full_name for existing users
    op.execute("UPDATE users SET full_name = name WHERE full_name IS NULL")
    op.execute("UPDATE users SET username = email WHERE username IS NULL")

    # Make full_name and username non-nullable after backfill
    op.alter_column("users", "full_name", nullable=False)
    op.alter_column("users", "username", nullable=False)


def downgrade() -> None:
    """Remove reports table and revert users table changes."""
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "updated_at")
    op.drop_column("users", "is_active")
    op.drop_column("users", "username")
    op.drop_column("users", "full_name")

    op.drop_index(op.f("ix_reports_report_number"), table_name="reports")
    op.drop_index(op.f("ix_reports_id"), table_name="reports")
    op.drop_table("reports")
