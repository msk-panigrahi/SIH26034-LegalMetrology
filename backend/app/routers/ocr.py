"""
OCR Router — provides endpoint to trigger OCR on existing inspection images.
Requires authentication with ownership verification.
"""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Inspection, User
from app.models.ocr_result import OCRResult
from app.services.ocr_service import extract_text_from_image
from app.auth.dependencies import require_inspector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/inspections", tags=["ocr"])

# ---------------------------------------------------------------------------

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads" / "inspections"


def _check_ownership(inspection: Inspection, user: User) -> None:
    """Verify user owns this inspection or is admin."""
    if user.role != "ADMIN" and inspection.inspector_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied.")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post(
    "/{inspection_id}/ocr",
    summary="Extract text from inspection image using OCR",
    response_model=None,
)
def run_ocr_on_inspection(
    inspection_id: int,
    language: str = "eng",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_inspector),
):
    """Trigger OCR processing on an inspection's uploaded image."""
    # --- Find the inspection record ----------------------------------------
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if inspection is None:
        raise HTTPException(status_code=404, detail="Inspection not found.")

    # --- Ownership check ---------------------------------------------------
    _check_ownership(inspection, current_user)

    # --- Validate image path -----------------------------------------------
    if not inspection.image_path:
        raise HTTPException(status_code=404, detail="Inspection has no associated image.")

    image_path = UPLOAD_DIR / inspection.image_path.replace("inspections/", "")
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image file not found on disk.")

    # --- Run OCR -----------------------------------------------------------
    logger.info(f"Running OCR on inspection {inspection_id}: {image_path.name}")
    ocr_result = extract_text_from_image(image_path, language=language)

    if not ocr_result["success"]:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {ocr_result['error']}")

    # --- Store OCR result in database --------------------------------------
    existing_result = db.query(OCRResult).filter(OCRResult.inspection_id == inspection_id).first()

    if existing_result:
        existing_result.raw_text = ocr_result["raw_text"]
        existing_result.ocr_confidence = ocr_result["confidence"]
        existing_result.extraction_status = "PENDING"
        existing_result.extracted_fields = None
    else:
        db_result = OCRResult(
            inspection_id=inspection_id,
            raw_text=ocr_result["raw_text"],
            ocr_confidence=ocr_result["confidence"],
            extraction_status="PENDING",
        )
        db.add(db_result)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    inspection.status = "OCR_COMPLETE"
    db.commit()

    return {
        "inspection_id": inspection_id,
        "filename": image_path.name,
        "status": "OCR_COMPLETE",
        "ocr": {
            "raw_text": ocr_result["raw_text"],
            "confidence": ocr_result["confidence"],
            "word_count": ocr_result["word_count"],
            "language": language,
            "psm_used": ocr_result.get("psm_used"),
            "strategy": ocr_result.get("strategy"),
        },
        "message": "OCR text extraction completed successfully.",
    }
