"""
Compliance Router — provides endpoints for Legal Metrology compliance evaluation.
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
from app.models.compliance_result import ComplianceResult
from app.services.compliance.engine import ComplianceEngine
from app.services.compliance.context import ComplianceContext
from app.services.compliance.models import (
    OverallStatus,
    InspectionContext,
)
from app.auth.dependencies import require_inspector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/inspections", tags=["compliance"])


def _check_ownership(inspection: Inspection, user: User) -> None:
    """Verify user owns this inspection or is admin."""
    if user.role != "ADMIN" and inspection.inspector_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied.")


# ---------------------------------------------------------------------------
# Pydantic response models
# ---------------------------------------------------------------------------

class RuleResultResponse(BaseModel):
    """Individual rule evaluation result."""
    rule_id: str
    rule_name: str
    legal_basis: str
    status: str
    severity: str
    field: Optional[str] = None
    message: str
    evidence: Optional[str] = None
    confidence: str = "MEDIUM"


class ComplianceSummaryResponse(BaseModel):
    """Aggregate counts of rule outcomes."""
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    not_verifiable: int = 0
    not_applicable: int = 0
    rules_checked: int = 0


class ComplianceResponse(BaseModel):
    """Full compliance evaluation response."""
    inspection_id: int
    overall_status: str
    rule_version: str
    summary: ComplianceSummaryResponse
    rules: list[RuleResultResponse]
    message: str


# ---------------------------------------------------------------------------
# POST — Run compliance evaluation
# ---------------------------------------------------------------------------

@router.post(
    "/{inspection_id}/compliance",
    summary="Run Legal Metrology compliance evaluation",
    response_model=ComplianceResponse,
)
def run_compliance_check(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_inspector),
):
    """Run the compliance validation engine on an inspection."""
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if inspection is None:
        raise HTTPException(status_code=404, detail="Inspection not found.")

    _check_ownership(inspection, current_user)

    ocr_result = db.query(OCRResult).filter(OCRResult.inspection_id == inspection_id).first()
    if ocr_result is None:
        raise HTTPException(status_code=409, detail="OCR must be completed first.")

    raw_text = ocr_result.raw_text or ""
    extracted_fields = ocr_result.extracted_fields
    ocr_confidence = ocr_result.ocr_confidence

    ctx = ComplianceContext(
        inspection_id=inspection_id,
        raw_text=raw_text,
        extracted_fields=extracted_fields,
        ocr_confidence=ocr_confidence,
        inspection_context=InspectionContext.UNKNOWN,
        rule_version="LM-PCR-2026",
        product_category=getattr(inspection, "product", None)
        and getattr(inspection.product, "category", None),
    )

    try:
        engine = ComplianceEngine(rule_version="LM-PCR-2026")
        overall_status, rule_results = engine.evaluate(ctx)

        from app.services.compliance.models import build_summary
        summary = build_summary(rule_results)

        rules_response = [
            RuleResultResponse(
                rule_id=r.rule_id,
                rule_name=r.rule_name,
                legal_basis=r.legal_basis,
                status=r.status.value,
                severity=r.severity.value,
                field=r.field,
                message=r.message,
                evidence=r.evidence,
                confidence=r.confidence,
            )
            for r in rule_results
        ]

        results_json = {"rules": [r.to_dict() for r in rule_results]}

        existing = db.query(ComplianceResult).filter(
            ComplianceResult.inspection_id == inspection_id
        ).first()

        if existing:
            existing.overall_status = overall_status.value
            existing.rule_version = "LM-PCR-2026"
            existing.rules_checked = summary.rules_checked
            existing.passed_count = summary.passed
            existing.failed_count = summary.failed
            existing.warning_count = summary.warnings
            existing.not_verifiable_count = summary.not_verifiable
            existing.not_applicable_count = summary.not_applicable
            existing.results_json = results_json
        else:
            db_result = ComplianceResult(
                inspection_id=inspection_id,
                overall_status=overall_status.value,
                rule_version="LM-PCR-2026",
                rules_checked=summary.rules_checked,
                passed_count=summary.passed,
                failed_count=summary.failed,
                warning_count=summary.warnings,
                not_verifiable_count=summary.not_verifiable,
                not_applicable_count=summary.not_applicable,
                results_json=results_json,
            )
            db.add(db_result)

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        return ComplianceResponse(
            inspection_id=inspection_id,
            overall_status=overall_status.value,
            rule_version="LM-PCR-2026",
            summary=ComplianceSummaryResponse(**summary.to_dict()),
            rules=rules_response,
            message="Compliance assessment completed.",
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Compliance evaluation failed for inspection %d", inspection_id)
        db.rollback()
        raise HTTPException(status_code=500, detail="Compliance evaluation failed.")


# ---------------------------------------------------------------------------
# GET — Retrieve stored compliance result
# ---------------------------------------------------------------------------

@router.get(
    "/{inspection_id}/compliance",
    summary="Retrieve stored compliance evaluation result",
    response_model=ComplianceResponse,
)
def get_compliance_result(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_inspector),
):
    """Retrieve the most recent stored compliance result for an inspection."""
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if inspection is None:
        raise HTTPException(status_code=404, detail="Inspection not found.")

    _check_ownership(inspection, current_user)

    comp_result = db.query(ComplianceResult).filter(
        ComplianceResult.inspection_id == inspection_id
    ).first()
    if comp_result is None:
        raise HTTPException(status_code=404, detail="No compliance result found.")

    rules_data = comp_result.results_json.get("rules", []) if comp_result.results_json else []

    rules_response = [
        RuleResultResponse(
            rule_id=r.get("rule_id", ""),
            rule_name=r.get("rule_name", ""),
            legal_basis=r.get("legal_basis", ""),
            status=r.get("status", ""),
            severity=r.get("severity", ""),
            field=r.get("field"),
            message=r.get("message", ""),
            evidence=r.get("evidence"),
            confidence=r.get("confidence", "MEDIUM"),
        )
        for r in rules_data
    ]

    return ComplianceResponse(
        inspection_id=inspection_id,
        overall_status=comp_result.overall_status,
        rule_version=comp_result.rule_version,
        summary=ComplianceSummaryResponse(
            passed=comp_result.passed_count,
            failed=comp_result.failed_count,
            warnings=comp_result.warning_count,
            not_verifiable=comp_result.not_verifiable_count,
            not_applicable=comp_result.not_applicable_count,
            rules_checked=comp_result.rules_checked,
        ),
        rules=rules_response,
        message="Compliance result retrieved successfully.",
    )
