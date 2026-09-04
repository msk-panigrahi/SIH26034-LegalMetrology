"""
Declaration model — stores an OCR-extracted declaration from a package image.
"""

from datetime import datetime
from sqlalchemy import String, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Declaration(Base):
    __tablename__ = "declarations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    inspection_id: Mapped[int] = mapped_column(ForeignKey("inspections.id"), nullable=False)
    declaration_type: Mapped[str] = mapped_column(String(100), nullable=False)
    extracted_value: Mapped[str] = mapped_column(String(500), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    inspection = relationship("Inspection", backref="declarations")
