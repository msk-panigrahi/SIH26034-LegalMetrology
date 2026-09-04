"""
Dashboard Router — provides inspector and admin dashboard statistics.
"""

import logging
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func, case

from app.database import get_db
from app.models import Inspection, User
from app.models.compliance_result import ComplianceResult
from app.models.ocr_result import OCRResult
from app.models.report import Report
from app.auth.dependencies import get_current_user, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class InspectorStats(BaseModel):
    """Statistics for a single inspector."""
    inspector_id: int
    name: str
    total_inspections: int = 0
    compliant: int = 0
    non_compliant: int = 0
    review_required: int = 0
    incomplete: int = 0
    last_inspection_at: Optional[str] = None


class InspectorDashboardResponse(BaseModel):
    """Inspector dashboard statistics."""
    total_inspections: int = 0
    compliant: int = 0
    non_compliant: int = 0
    review_required: int = 0
    incomplete: int = 0
    avg_ocr_confidence: float = 0.0
    recent_inspections: list = []


class AdminDashboardResponse(BaseModel):
    """Admin dashboard statistics."""
    total_inspectors: int = 0
    active_inspectors: int = 0
    total_inspections: int = 0
    compliant: int = 0
    non_compliant: int = 0
    review_required: int = 0
    incomplete: int = 0
    avg_ocr_confidence: float = 0.0
    recent_inspections: list = []
    inspector_statistics: list = []


# ---------------------------------------------------------------------------
# Inspector Dashboard
# ---------------------------------------------------------------------------

@router.get(
    "/inspector",
    summary="Get inspector dashboard statistics",
    response_model=InspectorDashboardResponse,
)
def get_inspector_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return statistics for the currently logged-in inspector."""
    user_id = current_user.id

    # Count inspections by status
    total = db.query(Inspection).filter(Inspection.inspector_id == user_id).count()

    # Count compliance statuses
    compliant = db.query(ComplianceResult).join(Inspection).filter(
        Inspection.inspector_id == user_id,
        ComplianceResult.overall_status == "COMPLIANT",
    ).count()

    non_compliant = db.query(ComplianceResult).join(Inspection).filter(
        Inspection.inspector_id == user_id,
        ComplianceResult.overall_status == "NON_COMPLIANT",
    ).count()

    review_required = db.query(ComplianceResult).join(Inspection).filter(
        Inspection.inspector_id == user_id,
        ComplianceResult.overall_status == "REVIEW_REQUIRED",
    ).count()

    # Incomplete = inspections without compliance result
    compliant_count = compliant + non_compliant + review_required
    incomplete = total - compliant_count
    if incomplete < 0:
        incomplete = 0

    # Average OCR confidence
    avg_conf = db.query(sql_func.avg(OCRResult.ocr_confidence)).join(Inspection).filter(
        Inspection.inspector_id == user_id,
        OCRResult.ocr_confidence.isnot(None),
    ).scalar()
    avg_ocr_confidence = round(float(avg_conf), 2) if avg_conf else 0.0

    # Recent inspections (with product name and overall status)
    recent = db.query(Inspection).filter(
        Inspection.inspector_id == user_id
    ).order_by(Inspection.created_at.desc()).limit(5).all()

    recent_list = []
    for insp in recent:
        comp = db.query(ComplianceResult).filter(ComplianceResult.inspection_id == insp.id).first()
        product_name = None
        if insp.product:
            product_name = insp.product.product_name
        recent_list.append({
            "id": insp.id,
            "status": insp.status,
            "overall_status": comp.overall_status if comp else None,
            "product_name": product_name,
            "created_at": insp.created_at.isoformat() if insp.created_at else None,
        })

    return InspectorDashboardResponse(
        total_inspections=total,
        compliant=compliant,
        non_compliant=non_compliant,
        review_required=review_required,
        incomplete=incomplete,
        avg_ocr_confidence=avg_ocr_confidence,
        recent_inspections=recent_list,
    )


# ---------------------------------------------------------------------------
# Admin Dashboard
# ---------------------------------------------------------------------------

@router.get(
    "/admin",
    summary="Get admin dashboard statistics",
    response_model=AdminDashboardResponse,
)
def get_admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Return system-wide statistics. Admin only."""
    try:
        # Inspector counts
        total_inspectors = db.query(User).filter(User.role == "INSPECTOR").count()
        active_inspectors = db.query(User).filter(
            User.role == "INSPECTOR", User.is_active == True
        ).count()

        # Inspection counts
        total_inspections = db.query(Inspection).count()

        compliant = db.query(ComplianceResult).filter(
            ComplianceResult.overall_status == "COMPLIANT"
        ).count()

        non_compliant = db.query(ComplianceResult).filter(
            ComplianceResult.overall_status == "NON_COMPLIANT"
        ).count()

        review_required = db.query(ComplianceResult).filter(
            ComplianceResult.overall_status == "REVIEW_REQUIRED"
        ).count()

        compliance_count = compliant + non_compliant + review_required
        incomplete = total_inspections - compliance_count
        if incomplete < 0:
            incomplete = 0

        # Average OCR confidence (system-wide)
        avg_conf = db.query(sql_func.avg(OCRResult.ocr_confidence)).filter(
            OCRResult.ocr_confidence.isnot(None),
        ).scalar()
        avg_ocr_confidence = round(float(avg_conf), 2) if avg_conf else 0.0

        # Recent inspections (with product name)
        recent = db.query(Inspection).order_by(
            Inspection.created_at.desc()
        ).limit(10).all()

        recent_list = []
        for insp in recent:
            comp = db.query(ComplianceResult).filter(ComplianceResult.inspection_id == insp.id).first()
            product_name = None
            if insp.product:
                product_name = insp.product.product_name
            recent_list.append({
                "id": insp.id,
                "status": insp.status,
                "overall_status": comp.overall_status if comp else None,
                "product_name": product_name,
                "inspector_id": insp.inspector_id,
                "created_at": insp.created_at.isoformat() if insp.created_at else None,
            })

        # Per-inspector statistics
        inspectors = db.query(User).filter(User.role == "INSPECTOR").all()
        inspector_stats = []
        for insp_user in inspectors:
            insp_total = db.query(Inspection).filter(Inspection.inspector_id == insp_user.id).count()
            insp_compliant = db.query(ComplianceResult).join(Inspection).filter(
                Inspection.inspector_id == insp_user.id,
                ComplianceResult.overall_status == "COMPLIANT",
            ).count()
            insp_non_compliant = db.query(ComplianceResult).join(Inspection).filter(
                Inspection.inspector_id == insp_user.id,
                ComplianceResult.overall_status == "NON_COMPLIANT",
            ).count()
            insp_review = db.query(ComplianceResult).join(Inspection).filter(
                Inspection.inspector_id == insp_user.id,
                ComplianceResult.overall_status == "REVIEW_REQUIRED",
            ).count()

            last_inspection = db.query(Inspection).filter(
                Inspection.inspector_id == insp_user.id
            ).order_by(Inspection.created_at.desc()).first()

            insp_incomplete = insp_total - (insp_compliant + insp_non_compliant + insp_review)
            if insp_incomplete < 0:
                insp_incomplete = 0

            inspector_stats.append({
                "inspector_id": insp_user.id,
                "name": insp_user.full_name,
                "total_inspections": insp_total,
                "compliant": insp_compliant,
                "non_compliant": insp_non_compliant,
                "review_required": insp_review,
                "incomplete": insp_incomplete,
                "last_inspection_at": last_inspection.created_at.isoformat() if last_inspection and last_inspection.created_at else None,
            })

        return AdminDashboardResponse(
            total_inspectors=total_inspectors,
            active_inspectors=active_inspectors,
            total_inspections=total_inspections,
            compliant=compliant,
            non_compliant=non_compliant,
            review_required=review_required,
            incomplete=incomplete,
            avg_ocr_confidence=avg_ocr_confidence,
            recent_inspections=recent_list,
            inspector_statistics=inspector_stats,
        )
    except Exception as exc:
        logger.exception("Admin dashboard query failed")
        raise HTTPException(status_code=500, detail="Unable to load admin dashboard statistics.")
