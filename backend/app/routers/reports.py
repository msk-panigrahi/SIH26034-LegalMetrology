"""
Reports Router — handles report generation, retrieval, and PDF serving.
"""

import logging
import os
from typing import Optional
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func

from app.database import get_db
from app.models import Inspection, User
from app.models.ocr_result import OCRResult
from app.models.compliance_result import ComplianceResult
from app.models.report import Report
from app.auth.dependencies import require_inspector
from app.services.pdf_service import generate_pdf_report, STORAGE_DIR

logger = logging.getLogger(__name__)

router = APIRouter(tags=["reports"])


def _check_ownership(inspection: Inspection, user: User) -> None:
    if user.role != "ADMIN" and inspection.inspector_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied.")


def _generate_report_number(db: Session) -> str:
    """Generate a unique sequential report number like LM-2026-000001."""
    year = datetime.now(timezone.utc).year
    # Count existing reports for this year
    count = db.query(Report).filter(
        Report.report_number.like(f"LM-{year}-%")
    ).count()
    return f"LM-{year}-{count + 1:06d}"


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class ReportResponse(BaseModel):
    """Full report response."""
    id: int
    report_number: str
    inspection_id: int
    generated_by: int
    report_status: str
    report_data: Optional[dict] = None
    created_at: Optional[str] = None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post(
    "/api/inspections/{inspection_id}/report",
    summary="Generate an inspection report",
    response_model=ReportResponse,
    status_code=201,
)
def generate_report(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_inspector),
):
    """Generate a consolidated inspection report."""
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if inspection is None:
        raise HTTPException(status_code=404, detail="Inspection not found.")

    _check_ownership(inspection, current_user)

    # Check if report already exists
    existing = db.query(Report).filter(Report.inspection_id == inspection_id).first()
    if existing:
        return ReportResponse(
            id=existing.id,
            report_number=existing.report_number,
            inspection_id=existing.inspection_id,
            generated_by=existing.generated_by,
            report_status=existing.report_status,
            report_data=existing.report_data,
            created_at=existing.created_at.isoformat() if existing.created_at else None,
        )

    # Gather data
    ocr_result = db.query(OCRResult).filter(OCRResult.inspection_id == inspection_id).first()
    comp_result = db.query(ComplianceResult).filter(ComplianceResult.inspection_id == inspection_id).first()

    # Build report data
    report_data = {
        "report_number": _generate_report_number(db),
        "inspection": {
            "id": inspection.id,
            "date": inspection.created_at.isoformat() if inspection.created_at else None,
            "image_path": inspection.image_path,
            "status": inspection.status,
        },
        "inspector": {
            "id": current_user.id,
            "name": current_user.full_name,
        },
        "product": ocr_result.extracted_fields if ocr_result and ocr_result.extracted_fields else {},
        "compliance": {
            "overall_status": comp_result.overall_status if comp_result else "NOT_EVALUATED",
            "rules_checked": comp_result.rules_checked if comp_result else 0,
            "passed": comp_result.passed_count if comp_result else 0,
            "failed": comp_result.failed_count if comp_result else 0,
            "warnings": comp_result.warning_count if comp_result else 0,
            "not_verifiable": comp_result.not_verifiable_count if comp_result else 0,
        },
        "findings": (
            comp_result.results_json.get("rules", []) if comp_result and comp_result.results_json else []
        ),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    report = Report(
        inspection_id=inspection_id,
        generated_by=current_user.id,
        report_number=report_data["report_number"],
        report_status="GENERATED",
        report_data=report_data,
    )
    db.add(report)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(report)

    return ReportResponse(
        id=report.id,
        report_number=report.report_number,
        inspection_id=report.inspection_id,
        generated_by=report.generated_by,
        report_status=report.report_status,
        report_data=report.report_data,
        created_at=report.created_at.isoformat() if report.created_at else None,
    )


@router.get(
    "/api/inspections/{inspection_id}/report",
    summary="Retrieve inspection report",
    response_model=ReportResponse,
)
def get_report(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_inspector),
):
    """Retrieve the report for an inspection."""
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if inspection is None:
        raise HTTPException(status_code=404, detail="Inspection not found.")

    _check_ownership(inspection, current_user)

    report = db.query(Report).filter(Report.inspection_id == inspection_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="No report found for this inspection.")

    return ReportResponse(
        id=report.id,
        report_number=report.report_number,
        inspection_id=report.inspection_id,
        generated_by=report.generated_by,
        report_status=report.report_status,
        report_data=report.report_data,
        created_at=report.created_at.isoformat() if report.created_at else None,
    )


# ---------------------------------------------------------------------------
# POST — Generate PDF for an inspection
# ---------------------------------------------------------------------------

@router.post(
    "/api/inspections/{inspection_id}/report/pdf",
    summary="Generate PDF report for an inspection",
)
def generate_pdf(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_inspector),
):
    """Generate a PDF report and store it on disk."""
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if inspection is None:
        raise HTTPException(status_code=404, detail="Inspection not found.")

    _check_ownership(inspection, current_user)

    # Gather data
    ocr_result = db.query(OCRResult).filter(OCRResult.inspection_id == inspection_id).first()
    comp_result = db.query(ComplianceResult).filter(ComplianceResult.inspection_id == inspection_id).first()
    report = db.query(Report).filter(Report.inspection_id == inspection_id).first()

    if not report:
        raise HTTPException(status_code=400, detail="Report must be generated before PDF.")

    # Inspector info
    inspector = db.query(User).filter(User.id == inspection.inspector_id).first()

    # Build inspection data for PDF
    inspection_data = {
        'id': inspection.id,
        'date': inspection.created_at.strftime('%d %B %Y') if inspection.created_at else '—',
        'inspector_name': inspector.full_name if inspector else '—',
        'inspector_username': inspector.username if inspector else '—',
        'ocr_confidence': ocr_result.ocr_confidence if ocr_result else None,
        'image_path': None,
    }

    # Resolve image path
    if inspection.image_path:
        upload_dir = Path(__file__).resolve().parent.parent.parent / "uploads"
        image_file = upload_dir / inspection.image_path
        if image_file.exists():
            inspection_data['image_path'] = str(image_file)

    extracted_fields = ocr_result.extracted_fields if ocr_result and ocr_result.extracted_fields else {}

    compliance_data = {
        'overall_status': comp_result.overall_status if comp_result else 'NOT_EVALUATED',
        'summary': {
            'rules_checked': comp_result.rules_checked if comp_result else 0,
            'passed': comp_result.passed_count if comp_result else 0,
            'failed': comp_result.failed_count if comp_result else 0,
            'warnings': comp_result.warning_count if comp_result else 0,
            'not_verifiable': comp_result.not_verifiable_count if comp_result else 0,
            'not_applicable': comp_result.not_applicable_count if comp_result else 0,
        },
        'findings': (
            comp_result.results_json.get('rules', []) if comp_result and comp_result.results_json else []
        ),
    }

    try:
        pdf_path = generate_pdf_report(
            report_number=report.report_number,
            inspection_data=inspection_data,
            extracted_fields=extracted_fields,
            compliance_data=compliance_data,
            image_path=inspection_data.get('image_path'),
        )
        return {
            'message': 'PDF report generated successfully.',
            'pdf_path': pdf_path,
            'report_number': report.report_number,
        }
    except Exception as e:
        logger.exception(f"PDF generation failed for inspection {inspection_id}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


# ---------------------------------------------------------------------------
# GET — Serve PDF file (PUBLIC — no authentication required)
# ---------------------------------------------------------------------------

@router.get(
    "/api/inspections/{inspection_id}/report/pdf",
    summary="Download or view PDF report",
)
def serve_pdf(
    inspection_id: int,
    db: Session = Depends(get_db),
):
    """Serve the PDF report file. This endpoint is PUBLIC."""
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if inspection is None:
        raise HTTPException(status_code=404, detail="Inspection not found.")

    report = db.query(Report).filter(Report.inspection_id == inspection_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="No report found for this inspection.")

    pdf_path = STORAGE_DIR / f"report_{inspection_id}.pdf"
    if not pdf_path.exists():
        # Try to generate the PDF on the fly
        try:
            ocr_result = db.query(OCRResult).filter(OCRResult.inspection_id == inspection_id).first()
            comp_result = db.query(ComplianceResult).filter(ComplianceResult.inspection_id == inspection_id).first()
            inspector = db.query(User).filter(User.id == inspection.inspector_id).first()

            inspection_data = {
                'id': inspection.id,
                'date': inspection.created_at.strftime('%d %B %Y') if inspection.created_at else '—',
                'inspector_name': inspector.full_name if inspector else '—',
                'inspector_username': inspector.username if inspector else '—',
                'ocr_confidence': ocr_result.ocr_confidence if ocr_result else None,
                'image_path': None,
            }

            if inspection.image_path:
                upload_dir = Path(__file__).resolve().parent.parent.parent / "uploads"
                image_file = upload_dir / inspection.image_path
                if image_file.exists():
                    inspection_data['image_path'] = str(image_file)

            extracted_fields = ocr_result.extracted_fields if ocr_result and ocr_result.extracted_fields else {}

            compliance_data = {
                'overall_status': comp_result.overall_status if comp_result else 'NOT_EVALUATED',
                'summary': {
                    'rules_checked': comp_result.rules_checked if comp_result else 0,
                    'passed': comp_result.passed_count if comp_result else 0,
                    'failed': comp_result.failed_count if comp_result else 0,
                    'warnings': comp_result.warning_count if comp_result else 0,
                    'not_verifiable': comp_result.not_verifiable_count if comp_result else 0,
                    'not_applicable': comp_result.not_applicable_count if comp_result else 0,
                },
                'findings': (
                    comp_result.results_json.get('rules', []) if comp_result and comp_result.results_json else []
                ),
            }

            pdf_path = Path(generate_pdf_report(
                report_number=report.report_number,
                inspection_data=inspection_data,
                extracted_fields=extracted_fields,
                compliance_data=compliance_data,
                image_path=inspection_data.get('image_path'),
            ))
        except Exception as e:
            logger.exception(f"PDF generation failed on-the-fly for inspection {inspection_id}")
            raise HTTPException(status_code=500, detail="PDF report could not be generated.")

    filename = f"LegalMetriX_Report_{report.report_number}.pdf"
    return FileResponse(
        path=str(pdf_path),
        filename=filename,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
        },
    )
