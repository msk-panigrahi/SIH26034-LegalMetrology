"""
Extraction Router — provides endpoint for field extraction from OCR text.
Requires authentication with ownership verification.
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Inspection, User
from app.models.ocr_result import OCRResult
from app.services.field_extraction_service import extract_fields_from_text
from app.auth.dependencies import require_inspector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/inspections", tags=["extraction"])


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _check_ownership(inspection: Inspection, user: User) -> None:
    """Verify user owns this inspection or is admin."""
    if user.role != "ADMIN" and inspection.inspector_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied.")


# ---------------------------------------------------------------------------
# Pydantic response models
# ---------------------------------------------------------------------------

class MRPResponse(BaseModel):
    """MRP extraction response."""
    value: Optional[float] = None
    currency: str = "INR"
    source: Optional[str] = None
    confidence: str = "HIGH"


class NetQuantityResponse(BaseModel):
    """Net quantity extraction response."""
    value: Optional[float] = None
    unit: Optional[str] = None
    source: Optional[str] = None


class CustomerCareResponse(BaseModel):
    """Customer care extraction response."""
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None


class ExtractedFieldsResponse(BaseModel):
    """Response containing all extracted product fields."""
    product_name: Optional[str] = None
    brand_name: Optional[str] = None
    manufacturer: Optional[str] = None
    marketer: Optional[str] = None
    mrp: Optional[MRPResponse] = None
    net_quantity: Optional[NetQuantityResponse] = None
    pack_count: Optional[int] = None
    country_of_origin: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    best_before: Optional[str] = None
    batch_number: Optional[str] = None
    manufacturer_address: Optional[str] = None
    customer_care: Optional[CustomerCareResponse] = None


class ExtractionResponse(BaseModel):
    """Full response for field extraction endpoint."""
    inspection_id: int
    status: str
    fields: ExtractedFieldsResponse
    message: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post(
    "/{inspection_id}/extract-fields",
    summary="Extract structured product fields from OCR text",
    response_model=ExtractionResponse,
)
def extract_inspection_fields(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_inspector),
):
    """Extract structured product fields from OCR text."""
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if inspection is None:
        raise HTTPException(status_code=404, detail="Inspection not found.")

    _check_ownership(inspection, current_user)

    ocr_result = db.query(OCRResult).filter(OCRResult.inspection_id == inspection_id).first()
    if ocr_result is None:
        raise HTTPException(
            status_code=400,
            detail="OCR must be completed before field extraction.",
        )

    raw_text = ocr_result.raw_text
    if not raw_text or not raw_text.strip():
        raise HTTPException(status_code=400, detail="OCR result contains no text.")

    try:
        logger.info(f"Extracting fields for inspection {inspection_id}")
        extracted = extract_fields_from_text(raw_text)
        fields_dict = extracted.to_dict()

        ocr_result.extracted_fields = fields_dict
        ocr_result.extraction_status = "EXTRACTED"
        db.commit()

        return ExtractionResponse(
            inspection_id=inspection_id,
            status="FIELD_EXTRACTION_COMPLETE",
            fields=ExtractedFieldsResponse(**fields_dict),
            message="Product fields extracted successfully.",
        )
    except Exception as e:
        logger.exception(f"Field extraction failed for inspection {inspection_id}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Field extraction failed.")
