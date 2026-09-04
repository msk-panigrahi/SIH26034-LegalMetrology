"""
OCRResult model — stores OCR text and extracted fields from package images.

This model persists OCR results and field extractions so they can be
reused without re-running OCR processing.
"""

from datetime import datetime
from sqlalchemy import String, Text, Float, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class OCRResult(Base):
    """Stores raw OCR text and extracted fields for an inspection."""

    __tablename__ = "ocr_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    inspection_id: Mapped[int] = mapped_column(
        ForeignKey("inspections.id"), nullable=False, unique=True
    )
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    ocr_confidence: Mapped[float] = mapped_column(Float, nullable=True)
    extracted_fields: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    extraction_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="PENDING"
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    inspection = relationship("Inspection", backref="ocr_result")
