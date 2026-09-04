"""
Date rules — LM-008 and LM-009.

Validates manufacturing date and best-before / use-by date declarations,
including date consistency when both are present.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from app.services.compliance.base_rule import BaseRule
from app.services.compliance.context import ComplianceContext
from app.services.compliance.models import (
    RuleResult,
    RuleStatus,
    RuleSeverity,
)

# ---------------------------------------------------------------------------
# Date parsing helpers
# ---------------------------------------------------------------------------

# Patterns that look like MM/YYYY or MM/DD/YYYY
_DATE_RE = re.compile(
    r"(?:(?:0[1-9]|1[0-2])[/\-\.](?:0[1-9]|[12]\d|3[01])[/\-\.](?:20)?\d{2})"
    r"|"
    r"(?:(?:0[1-9]|1[0-2])[/\-\.](?:20)?\d{2})",
)

_MONTH_NAMES = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4,
    "MAY": 5, "JUN": 6, "JUL": 7, "AUG": 8,
    "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}


def _parse_month_year(date_str: str) -> Optional[datetime]:
    """Best-effort parse of a date string to a datetime (first day of month)."""
    s = date_str.strip().upper()

    # MM/YYYY or MM-YYYY
    m = re.match(r"(0[1-9]|1[0-2])[/\-\.](20\d{2}|\d{2})", s)
    if m:
        month = int(m.group(1))
        year = int(m.group(2))
        if year < 100:
            year += 2000
        return datetime(year, month, 1)

    # MON YYYY
    m = re.match(r"([A-Z]{3})\s+(20\d{2}|\d{2})", s)
    if m and m.group(1) in _MONTH_NAMES:
        month = _MONTH_NAMES[m.group(1)]
        year = int(m.group(2))
        if year < 100:
            year += 2000
        return datetime(year, month, 1)

    # MM/DD/YYYY
    m = re.match(r"(0[1-9]|1[0-2])[/\-\.](0[1-9]|[12]\d|3[01])[/\-\.](20\d{2}|\d{2})", s)
    if m:
        month = int(m.group(1))
        day = int(m.group(2))
        year = int(m.group(3))
        if year < 100:
            year += 2000
        return datetime(year, month, day)

    return None


# ---------------------------------------------------------------------------
# LM-008 — Manufacturing / Packing / Import Date
# ---------------------------------------------------------------------------

_MFD_LABELS = re.compile(
    r"(?:MFD|MFG|MANUFACTURED?|PKD|PACKED|PACKED\s+ON|"
    r"DATE\s+OF\s+MANUFACTURE|MFG\s+DATE|PKD\s+DATE)",
    re.IGNORECASE,
)


class LM008DateDeclarationRule(BaseRule):
    """Manufacturing / packing / import date."""

    rule_id = "LM-008"
    rule_name = "Manufacturing / Packing Date Declaration"
    legal_basis = "Rule 6(1)(e)"

    def evaluate(self, ctx: ComplianceContext) -> RuleResult:
        mfg_date = ctx.field("manufacturing_date")
        raw = ctx.raw_text or ""

        if mfg_date:
            parsed = _parse_month_year(mfg_date)
            if parsed:
                return RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    legal_basis=self.legal_basis,
                    status=RuleStatus.PASS,
                    severity=RuleSeverity.HIGH,
                    field="manufacturing_date",
                    message="Manufacturing/packing date declaration was detected.",
                    evidence=f"MFG: {mfg_date}",
                    confidence="HIGH",
                )
            else:
                return RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    legal_basis=self.legal_basis,
                    status=RuleStatus.WARNING,
                    severity=RuleSeverity.MEDIUM,
                    field="manufacturing_date",
                    message=f"A manufacturing date was extracted ('{mfg_date}') but could not be normalised.",
                    evidence=mfg_date,
                    confidence="MEDIUM",
                )

        # Check raw text for MFD/MFG labels
        if _MFD_LABELS.search(raw):
            m = _MFD_LABELS.search(raw)
            start = max(0, m.start())
            end = min(len(raw), m.end() + 40)
            snippet = raw[start:end].strip()
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.WARNING,
                severity=RuleSeverity.MEDIUM,
                field="manufacturing_date",
                message="A manufacturing date label was found but the date value could not be extracted.",
                evidence=snippet,
                confidence="LOW",
            )

        if not ctx.has_raw_text:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.NOT_VERIFIABLE,
                severity=RuleSeverity.MEDIUM,
                field="manufacturing_date",
                message="No OCR text available to verify manufacturing date.",
                evidence=None,
                confidence="LOW",
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            legal_basis=self.legal_basis,
            status=RuleStatus.NOT_VERIFIABLE,
            severity=RuleSeverity.MEDIUM,
            field="manufacturing_date",
            message="Manufacturing/packing date could not be verified from the OCR evidence.",
            evidence=None,
            confidence="LOW",
        )


# ---------------------------------------------------------------------------
# LM-009 — Best Before / Use By / Expiry
# ---------------------------------------------------------------------------

_BEST_BEFORE_LABELS = re.compile(
    r"(?:USE\s+BEFORE|BEST\s+BEFORE|EXPIRY|EXP(?:IRY)?(?:\s+DATE)?)",
    re.IGNORECASE,
)


class LM009BestBeforeRule(BaseRule):
    """Best before / use-by / expiry date rule (conditional)."""

    rule_id = "LM-009"
    rule_name = "Best Before / Use By / Expiry Date"
    legal_basis = "Rule 6(1)(e) / applicable expiry provisions"

    def evaluate(self, ctx: ComplianceContext) -> RuleResult:
        expiry_date = ctx.field("expiry_date")
        best_before = ctx.field("best_before")
        mfg_date = ctx.field("manufacturing_date")
        raw = ctx.raw_text or ""

        # Check if the expiry label appears in raw text but extraction failed
        has_expiry_label = bool(_BEST_BEFORE_LABELS.search(raw))

        # Duration-based best_before (e.g., "24 months from Mfg") is valid
        if best_before and not expiry_date:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.PASS,
                severity=RuleSeverity.HIGH,
                field="expiry_date",
                message="A duration-based best-before declaration was detected.",
                evidence=f"Best Before: {best_before}",
                confidence="HIGH",
            )

        if expiry_date:
            parsed_expiry = _parse_month_year(expiry_date)
            parsed_mfg = _parse_month_year(mfg_date) if mfg_date else None

            # Date consistency check: expiry must be after manufacturing
            if parsed_expiry and parsed_mfg:
                if parsed_expiry <= parsed_mfg:
                    return RuleResult(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        legal_basis=self.legal_basis,
                        status=RuleStatus.FAIL,
                        severity=RuleSeverity.CRITICAL,
                        field="expiry_date",
                        message=(
                            f"The expiry date ({expiry_date}) is not after the "
                            f"manufacturing date ({mfg_date}), which is inconsistent."
                        ),
                        evidence=f"MFG: {mfg_date}, Expiry: {expiry_date}",
                        confidence="HIGH",
                    )

            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.PASS,
                severity=RuleSeverity.HIGH,
                field="expiry_date",
                message="Best before / expiry date declaration was detected.",
                evidence=f"Expiry: {expiry_date}",
                confidence="HIGH",
            )

        # Label found but value not extracted
        if has_expiry_label:
            m = _BEST_BEFORE_LABELS.search(raw)
            start = max(0, m.start())
            end = min(len(raw), m.end() + 60)
            snippet = raw[start:end].strip()
            # If there is a duration pattern nearby, it is still valid
            duration_match = re.search(r"\d+\s*(?:MONTHS?|DAYS?|YEARS?)\s+FROM", raw, re.IGNORECASE)
            if duration_match:
                return RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    legal_basis=self.legal_basis,
                    status=RuleStatus.PASS,
                    severity=RuleSeverity.HIGH,
                    field="expiry_date",
                    message="A duration-based best-before declaration was detected.",
                    evidence=snippet,
                    confidence="MEDIUM",
                )
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.WARNING,
                severity=RuleSeverity.HIGH,
                field="expiry_date",
                message="An expiry/best-before label was found but the date value could not be extracted.",
                evidence=snippet,
                confidence="LOW",
            )

        # Applicability is uncertain
        if not ctx.has_raw_text:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.NOT_VERIFIABLE,
                severity=RuleSeverity.MEDIUM,
                field="expiry_date",
                message="No OCR text available to verify expiry/best-before date.",
                evidence=None,
                confidence="LOW",
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            legal_basis=self.legal_basis,
            status=RuleStatus.NOT_VERIFIABLE,
            severity=RuleSeverity.MEDIUM,
            field="expiry_date",
            message=(
                "Best before / expiry date could not be verified. "
                "Applicability depends on the commodity type."
            ),
            evidence=None,
            confidence="LOW",
        )
