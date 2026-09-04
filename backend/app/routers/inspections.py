"""
Inspections Router — provides inspection history and details.
"""

import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc, func as sql_func

from app.database import get_db
from app.models import Inspection, User
from app.models.ocr_result import OCRResult
from app.models.compliance_result import ComplianceResult
from app.models.report import Report
from app.auth.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/inspections", tags=["inspections"])


def _check_ownership(inspection: Inspection, user: User) -> None:
    if user.role != "ADMIN" and inspection.inspector_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied.")


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class InspectionListItem(BaseModel):
    """Summary item in inspection list."""
    id: int
    filename: Optional[str] = None
    product_name: Optional[str] = None
    overall_status: Optional[str] = None
    created_at: Optional[str] = None
    inspector_id: int


class InspectionListResponse(BaseModel):
    """Paginated list of inspections."""
    items: list[InspectionListItem]
    page: int
    page_size: int
    total: int


class InspectionDetailResponse(BaseModel):
    """Detailed inspection view."""
    id: int
    status: str
    image_path: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None
    inspector_id: int
    inspector_name: Optional[str] = None
    product_name: Optional[str] = None
    product_category: Optional[str] = None
    ocr_status: Optional[str] = None
    ocr_confidence: Optional[float] = None
    raw_text: Optional[str] = None
    extracted_fields: Optional[dict] = None
    compliance_status: Optional[str] = None
    compliance_summary: Optional[dict] = None
    has_report: bool = False


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get(
    "",
    summary="List inspections with pagination and filtering",
    response_model=InspectionListResponse,
)
def list_inspections(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List inspections.

    For inspectors: returns only their own inspections.
    For admins: returns all inspections.
    """
    query = db.query(Inspection)

    # Ownership filter
    if current_user.role != "ADMIN":
        query = query.filter(Inspection.inspector_id == current_user.id)

    # Status filter — filter on compliance overall_status, not inspection status
    if status:
        status_upper = status.upper()
        if status_upper == "INCOMPLETE":
            # Incomplete = inspections that have no compliance result at all
            compliant_ids_sub = db.query(ComplianceResult.inspection_id).subquery()
            query = query.filter(
                ~Inspection.id.in_(sql_func.select(compliant_ids_sub.c.inspection_id))
            )
        else:
            # Filter by compliance result status
            query = query.join(
                ComplianceResult, ComplianceResult.inspection_id == Inspection.id
            ).filter(ComplianceResult.overall_status == status_upper)

    # Search filter (by product name via product relationship)
    if search:
        from app.models.product import Product
        query = query.join(Product).filter(
            Product.product_name.ilike(f"%{search}%")
        )

    total = query.count()
    items = query.order_by(desc(Inspection.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    result_items = []
    for insp in items:
        comp = db.query(ComplianceResult).filter(
            ComplianceResult.inspection_id == insp.id
        ).first()

        # Get product name
        product_name = None
        if insp.product:
            product_name = insp.product.product_name

        result_items.append(InspectionListItem(
            id=insp.id,
            filename=insp.image_path.split("/")[-1] if insp.image_path else None,
            product_name=product_name,
            overall_status=comp.overall_status if comp else None,
            created_at=insp.created_at.isoformat() if insp.created_at else None,
            inspector_id=insp.inspector_id,
        ))

    return InspectionListResponse(
        items=result_items,
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/{inspection_id}",
    summary="Get detailed inspection view",
    response_model=InspectionDetailResponse,
)
def get_inspection_detail(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a consolidated inspection view with all available data."""
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if inspection is None:
        raise HTTPException(status_code=404, detail="Inspection not found.")

    _check_ownership(inspection, current_user)

    # Gather related data
    ocr_result = db.query(OCRResult).filter(OCRResult.inspection_id == inspection_id).first()
    comp_result = db.query(ComplianceResult).filter(ComplianceResult.inspection_id == inspection_id).first()
    report = db.query(Report).filter(Report.inspection_id == inspection_id).first()

    # Inspector info
    inspector = db.query(User).filter(User.id == inspection.inspector_id).first()

    # Product info
    product_name = None
    product_category = None
    if inspection.product:
        product_name = inspection.product.product_name
        product_category = inspection.product.category

    # Compliance summary
    comp_summary = None
    if comp_result:
        comp_summary = {
            "overall_status": comp_result.overall_status,
            "rules_checked": comp_result.rules_checked,
            "passed": comp_result.passed_count,
            "failed": comp_result.failed_count,
            "warnings": comp_result.warning_count,
            "not_verifiable": comp_result.not_verifiable_count,
        }

    return InspectionDetailResponse(
        id=inspection.id,
        status=inspection.status,
        image_path=inspection.image_path,
        notes=inspection.notes,
        created_at=inspection.created_at.isoformat() if inspection.created_at else None,
        inspector_id=inspection.inspector_id,
        inspector_name=inspector.full_name if inspector else None,
        product_name=product_name,
        product_category=product_category,
        ocr_status=ocr_result.extraction_status if ocr_result else None,
        ocr_confidence=ocr_result.ocr_confidence if ocr_result else None,
        raw_text=ocr_result.raw_text if ocr_result else None,
        extracted_fields=ocr_result.extracted_fields if ocr_result else None,
        compliance_status=comp_result.overall_status if comp_result else None,
        compliance_summary=comp_summary,
        has_report=report is not None,
    )
