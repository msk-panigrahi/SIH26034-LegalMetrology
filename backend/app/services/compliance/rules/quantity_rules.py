"""
Quantity rules — LM-005.

Validates net quantity declarations including weight, volume, and
number-based quantities.
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


# Recognised units grouped by dimension
_WEIGHT_UNITS = {"g", "gm", "gms", "kg", "kgs", "mg"}
_VOLUME_UNITS = {"ml", "l", "ltr", "ltrs", "litre", "liter", "litres", "liters"}
_COUNT_UNITS = {"units", "unit", "pieces", "piece", "nos", "no"}
_LENGTH_UNITS = {"cm", "mm", "m", "inch", "inches"}
_ALL_UNITS = _WEIGHT_UNITS | _VOLUME_UNITS | _COUNT_UNITS | _LENGTH_UNITS

# Multi-pack / promotional indicators
_MULTI_PACK_INDICATORS = re.compile(
    r"(?:PACK\s+OF\s+\d+|\d+\s+UNITS?|\d+\s+PIECES?"
    r"|FREE|BONUS|COMBO|MULTI[\s-]?PACK|"
    r"\d+\s*[Xx]\s*\d+)",
    re.IGNORECASE,
)


class LM005NetQuantityRule(BaseRule):
    """Net quantity declaration validation."""

    rule_id = "LM-005"
    rule_name = "Net Quantity Declaration"
    legal_basis = "Rule 6(1)(d)"

    def evaluate(self, ctx: ComplianceContext) -> RuleResult:
        nq_value = ctx.nested_field("net_quantity", "value")
        nq_unit = ctx.nested_field("net_quantity", "unit")
        nq_source = ctx.nested_field("net_quantity", "source")
        pack_count = ctx.field("pack_count")
        raw = ctx.raw_text or ""

        # --- No quantity at all ---
        if nq_value is None and nq_unit is None:
            if not ctx.has_raw_text:
                return RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    legal_basis=self.legal_basis,
                    status=RuleStatus.NOT_VERIFIABLE,
                    severity=RuleSeverity.HIGH,
                    field="net_quantity",
                    message="No OCR text available to verify net quantity.",
                    evidence=None,
                    confidence="LOW",
                )
            # OCR text exists but no quantity found → FAIL (mandatory declaration missing)
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.FAIL,
                severity=RuleSeverity.CRITICAL,
                field="net_quantity",
                message="Net quantity declaration is required but was not found in the package text.",
                evidence=None,
                confidence="MEDIUM",
            )

        # --- Negative quantity ---
        if nq_value is not None and nq_value < 0:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.FAIL,
                severity=RuleSeverity.CRITICAL,
                field="net_quantity",
                message="A negative net quantity was detected, which is invalid.",
                evidence=nq_source,
                confidence="HIGH",
            )

        # --- Zero quantity ---
        if nq_value is not None and nq_value == 0:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.FAIL,
                severity=RuleSeverity.HIGH,
                field="net_quantity",
                message="A net quantity of zero was detected, which is invalid.",
                evidence=nq_source,
                confidence="HIGH",
            )

        # --- Unit not recognised ---
        if nq_unit and nq_unit.lower() not in _ALL_UNITS:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.WARNING,
                severity=RuleSeverity.MEDIUM,
                field="net_quantity",
                message=f"The detected unit '{nq_unit}' is not a commonly recognised unit.",
                evidence=nq_source,
                confidence="MEDIUM",
            )

        # --- Multi-pack ambiguity ---
        is_multi_pack = bool(pack_count and pack_count > 1)
        has_free = bool(re.search(r"\bFREE\b", raw, re.IGNORECASE))
        has_x_pattern = bool(re.search(r"\d+\s*[Xx]\s*\d+", raw))

        if is_multi_pack and (has_free or has_x_pattern):
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.WARNING,
                severity=RuleSeverity.MEDIUM,
                field="net_quantity",
                message=(
                    "Multi-pack or promotional quantity detected. "
                    "The relationship between unit quantity, pack count, "
                    "and free quantity could not be fully verified."
                ),
                evidence=nq_source,
                confidence="MEDIUM",
            )

        # --- Everything looks reasonable ---
        evidence_parts = []
        if nq_value is not None:
            evidence_parts.append(str(nq_value))
        if nq_unit:
            evidence_parts.append(nq_unit)
        evidence = " ".join(evidence_parts)
        if nq_source:
            evidence = nq_source

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            legal_basis=self.legal_basis,
            status=RuleStatus.PASS,
            severity=RuleSeverity.HIGH,
            field="net_quantity",
            message="Net quantity declaration was detected and appears valid.",
            evidence=evidence,
            confidence="HIGH",
        )
