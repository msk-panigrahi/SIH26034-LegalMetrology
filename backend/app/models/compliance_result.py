"""
ComplianceResult model — stores the complete compliance evaluation for an inspection.

Unlike the existing ComplianceFinding model (which stores individual findings),
this model stores the full engine output including overall status, summary
counts, and all rule results as JSON.
"""

from datetime import datetime
from sqlalchemy import String, Integer, Text, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ComplianceResult(Base):
    """Stores the complete compliance evaluation for an inspection."""

    __tablename__ = "compliance_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    inspection_id: Mapped[int] = mapped_column(
        ForeignKey("inspections.id"), nullable=False, unique=True
    )
    overall_status: Mapped[str] = mapped_column(String(50), nullable=False)
    rule_version: Mapped[str] = mapped_column(String(50), nullable=False)
    rules_checked: Mapped[int] = mapped_column(Integer, nullable=False)
    passed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    not_verifiable_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    not_applicable_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    results_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    inspection = relationship("Inspection", backref="compliance_results")
