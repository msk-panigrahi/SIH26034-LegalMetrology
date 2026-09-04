"""
Package rules — LM-010 to LM-013.

Validates consumer care details, dimensions, legibility/prominence,
and multi-piece / group package requirements.
"""

from __future__ import annotations

import re

from app.services.compliance.base_rule import BaseRule
from app.services.compliance.context import ComplianceContext
from app.services.compliance.models import (
    RuleResult,
    RuleStatus,
    RuleSeverity,
)


# ---------------------------------------------------------------------------
# LM-010 — Consumer Care Details
# ---------------------------------------------------------------------------

_CARE_LABELS = re.compile(
    r"(?:CONSUMER\s+CARE|CUSTOMER\s+CARE|TOLL\s*FREE|"
    r"HELPLINE|CONSUMER\s+COMPLAINT|CUSTOMER\s+SERVICE|"
    r"LEVERCARE|CARE\s*[:=])",
    re.IGNORECASE,
)


class LM010ConsumerCareRule(BaseRule):
    """Consumer care / contact information."""

    rule_id = "LM-010"
    rule_name = "Consumer Care Details"
    legal_basis = "Rule 6(1)(g)"

    def evaluate(self, ctx: ComplianceContext) -> RuleResult:
        cc_phone = ctx.nested_field("customer_care", "phone")
        cc_email = ctx.nested_field("customer_care", "email")
        cc_address = ctx.nested_field("customer_care", "address")
        raw = ctx.raw_text or ""

        has_contact = bool(cc_phone or cc_email or cc_address)

        if has_contact:
            # At least one valid contact channel
            channels = []
            if cc_phone:
                channels.append(f"phone: {cc_phone}")
            if cc_email:
                channels.append(f"email: {cc_email}")
            if cc_address:
                channels.append("address")

            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.PASS,
                severity=RuleSeverity.MEDIUM,
                field="customer_care",
                message=f"Consumer care details detected ({', '.join(channels)}).",
                evidence=cc_phone or cc_email or cc_address,
                confidence="HIGH",
            )

        # Check raw text for care labels
        if _CARE_LABELS.search(raw):
            m = _CARE_LABELS.search(raw)
            start = max(0, m.start())
            end = min(len(raw), m.end() + 60)
            snippet = raw[start:end].strip()
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.WARNING,
                severity=RuleSeverity.MEDIUM,
                field="customer_care",
                message="A consumer-care label was found but contact details could not be extracted.",
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
                field="customer_care",
                message="No OCR text available to verify consumer care details.",
                evidence=None,
                confidence="LOW",
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            legal_basis=self.legal_basis,
            status=RuleStatus.NOT_VERIFIABLE,
            severity=RuleSeverity.MEDIUM,
            field="customer_care",
            message=(
                "Consumer care details could not be verified from the "
                "supplied image/OCR evidence."
            ),
            evidence=None,
            confidence="LOW",
        )


# ---------------------------------------------------------------------------
# LM-011 — Dimensions
# ---------------------------------------------------------------------------

_DIMENSION_UNITS = re.compile(
    r"(?:\d+[\d.]*\s*(?:cm|mm|m|inch|inches)\s*[Xx×]\s*\d+[\d.]*\s*(?:cm|mm|m|inch|inches))",
    re.IGNORECASE,
)


class LM011DimensionsRule(BaseRule):
    """Dimensions (conditional — applicable only when relevant)."""

    rule_id = "LM-011"
    rule_name = "Dimensions Declaration"
    legal_basis = "Rule 6 (where applicable)"

    def evaluate(self, ctx: ComplianceContext) -> RuleResult:
        raw = ctx.raw_text or ""

        if _DIMENSION_UNITS.search(raw):
            m = _DIMENSION_UNITS.search(raw)
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.PASS,
                severity=RuleSeverity.LOW,
                field="dimensions",
                message="Dimension declaration was detected.",
                evidence=m.group(0),
                confidence="HIGH",
            )

        # Dimensions are not universally required for all commodity types
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            legal_basis=self.legal_basis,
            status=RuleStatus.NOT_APPLICABLE,
            severity=RuleSeverity.LOW,
            field="dimensions",
            message="Dimension declaration is not applicable for this commodity type.",
            evidence=None,
            confidence="LOW",
        )


# ---------------------------------------------------------------------------
# LM-012 — Legibility / Prominence
# ---------------------------------------------------------------------------

class LM012LegibilityRule(BaseRule):
    """
    Legibility and prominence of declarations.

    IMPORTANT: OCR alone cannot reliably establish legal legibility.
    This rule returns NOT_APPLICABLE for automated scoring.
    The report notes that visual verification is required by the officer.
    """

    rule_id = "LM-012"
    rule_name = "Legibility / Prominence"
    legal_basis = "Rule 9"

    def evaluate(self, ctx: ComplianceContext) -> RuleResult:
        # OCR cannot determine visual prominence/legibility.
        # Return NOT_APPLICABLE to avoid penalizing packages.
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            legal_basis=self.legal_basis,
            status=RuleStatus.NOT_APPLICABLE,
            severity=RuleSeverity.LOW,
            field="visual_legibility",
            message=(
                "Visual legibility and prominence require officer verification. "
                "Not assessable by automated OCR system."
            ),
            evidence=None,
            confidence="LOW",
        )


# ---------------------------------------------------------------------------
# LM-013 — Multi-Piece / Group Package
# ---------------------------------------------------------------------------

_MULTI_PACK_PATTERNS = re.compile(
    r"(?:PACK\s+OF\s+\d+|\d+\s+UNITS?|\d+\s+PIECES?"
    r"|\d+\s*[Xx]\s*\d+|FREE|BONUS|COMBO|MULTI[\s-]?PACK)",
    re.IGNORECASE,
)


class LM013MultiPieceRule(BaseRule):
    """Multi-piece / group package detection and assessment."""

    rule_id = "LM-013"
    rule_name = "Multi-Piece / Group Package"
    legal_basis = "Rule 3 / applicable multi-piece provisions"

    def evaluate(self, ctx: ComplianceContext) -> RuleResult:
        pack_count = ctx.field("pack_count")
        raw = ctx.raw_text or ""

        # More specific indicators that this is truly a multi-pack
        multi_pack_indicators = re.compile(
            r"(?:PACK\s+OF\s+\d+|\d+\s*[Xx]\s*\d+|"
            r"FREE|BONUS|COMBO|MULTI[\s-]?PACK|"
            r"SET\s+OF\s+\d+)",
            re.IGNORECASE,
        )

        is_multi = False
        evidence_parts = []

        # Only flag as multi-pack with clear evidence
        multi_match = multi_pack_indicators.search(raw)
        if multi_match:
            is_multi = True
            evidence_parts.append(multi_match.group(0))

        # Also check pack_count, but only if strong indicators exist
        if pack_count and pack_count > 1 and multi_match:
            evidence_parts.append(f"Pack count: {pack_count}")

        if not is_multi:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.NOT_APPLICABLE,
                severity=RuleSeverity.LOW,
                field="pack_count",
                message="Single-piece package detected. Multi-piece rules are not applicable.",
                evidence=None,
                confidence="HIGH",
            )

        evidence = "; ".join(evidence_parts) if evidence_parts else None

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            legal_basis=self.legal_basis,
            status=RuleStatus.WARNING,
            severity=RuleSeverity.MEDIUM,
            field="pack_count",
            message=(
                "Multi-piece or group package detected. The system cannot "
                "verify that individual internal packages comply with all "
                "labelling requirements."
            ),
            evidence=evidence,
            confidence="MEDIUM",
        )
