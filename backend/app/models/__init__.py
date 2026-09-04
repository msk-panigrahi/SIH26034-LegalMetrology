"""
Models package — imports all ORM models so Alembic / Base.metadata can discover them.
"""

from app.models.user import User
from app.models.product import Product
from app.models.inspection import Inspection
from app.models.declaration import Declaration
from app.models.compliance_finding import ComplianceFinding
from app.models.ocr_result import OCRResult
from app.models.compliance_result import ComplianceResult
from app.models.report import Report

__all__ = [
    "User",
    "Product",
    "Inspection",
    "Declaration",
    "ComplianceFinding",
    "OCRResult",
    "ComplianceResult",
    "Report",
]
