"""
Report model — stores generated inspection reports.
"""

from datetime import datetime
from sqlalchemy import String, Text, Integer, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Report(Base):
    """Stores a generated inspection report."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    inspection_id: Mapped[int] = mapped_column(
        ForeignKey("inspections.id"), nullable=False, unique=True
    )
    generated_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    report_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    report_status: Mapped[str] = mapped_column(String(50), nullable=False, default="GENERATED")
    report_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    inspection = relationship("Inspection", backref="reports")
    generator = relationship("User", backref="generated_reports")
