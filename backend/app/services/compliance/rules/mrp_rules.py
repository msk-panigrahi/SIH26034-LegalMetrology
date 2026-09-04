"""
MRP rules — LM-006 and LM-007.

Validates Maximum Retail Price declaration and, where sufficient data
exists, the unit sale price.
"""

from __future__ import annotations

import re
import math

from app.services.compliance.base_rule import BaseRule
from app.services.compliance.context import ComplianceContext
from app.services.compliance.models import (
    RuleResult,
    RuleStatus,
    RuleSeverity,
)

# ---------------------------------------------------------------------------

_MRP_LABEL = re.compile(r"MRP|MAXIMUM\s+RETAIL\s+PRICE", re.IGNORECASE)


class LM006MRPRule(BaseRule):
    """Rule 6 — Maximum Retail Price declaration."""

    rule_id = "LM-006"
    rule_name = "MRP Declaration"
    legal_basis = "Rule 6(1)(f)"

    def evaluate(self, ctx: ComplianceContext) -> RuleResult:
        mrp_value = ctx.nested_field("mrp", "value")
        mrp_currency = ctx.nested_field("mrp", "currency")
        mrp_source = ctx.nested_field("mrp", "source")
        raw = ctx.raw_text or ""

        # --- No MRP extracted ---
        if mrp_value is None:
            if not ctx.has_raw_text:
                return RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    legal_basis=self.legal_basis,
                    status=RuleStatus.NOT_VERIFIABLE,
                    severity=RuleSeverity.HIGH,
                    field="mrp",
                    message="No OCR text available to verify MRP declaration.",
                    evidence=None,
                    confidence="LOW",
                )

            # Check if the MRP label exists but value was not extracted
            if _MRP_LABEL.search(raw):
                m = _MRP_LABEL.search(raw)
                start = max(0, m.start())
                end = min(len(raw), m.end() + 60)
                snippet = raw[start:end].strip()
                return RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    legal_basis=self.legal_basis,
                    status=RuleStatus.WARNING,
                    severity=RuleSeverity.HIGH,
                    field="mrp",
                    message="MRP label found but numeric value could not be extracted.",
                    evidence=snippet,
                    confidence="LOW",
                )

            # OCR text exists but MRP label is not found → FAIL (mandatory declaration missing)
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.FAIL,
                severity=RuleSeverity.CRITICAL,
                field="mrp",
                message="MRP declaration is required but was not found in the package text.",
                evidence=None,
                confidence="MEDIUM",
            )

        # --- MRP extracted: validate ---
        if mrp_value <= 0:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.FAIL,
                severity=RuleSeverity.CRITICAL,
                field="mrp",
                message="The detected MRP value is zero or negative, which is invalid.",
                evidence=mrp_source,
                confidence="HIGH",
            )

        if mrp_value > 500000:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.WARNING,
                severity=RuleSeverity.MEDIUM,
                field="mrp",
                message=(
                    f"The detected MRP (₹{mrp_value:,.2f}) is unusually high. "
                    "Please verify manually."
                ),
                evidence=mrp_source,
                confidence="MEDIUM",
            )

        # Currency validation
        if mrp_currency and mrp_currency not in ("INR", "₹", "Rs", "Rs."):
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.WARNING,
                severity=RuleSeverity.MEDIUM,
                field="mrp",
                message=f"Unexpected currency '{mrp_currency}' detected for MRP.",
                evidence=mrp_source,
                confidence="MEDIUM",
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            legal_basis=self.legal_basis,
            status=RuleStatus.PASS,
            severity=RuleSeverity.HIGH,
            field="mrp",
            message="MRP declaration was detected with a valid numeric value.",
            evidence=mrp_source or f"₹{mrp_value:,.2f}",
            confidence="HIGH",
        )


# ---------------------------------------------------------------------------
# LM-007 — Unit Sale Price
# ---------------------------------------------------------------------------

# Units for which unit-price calculation is legally meaningful
_WEIGHT_UNITS = {"g", "gm", "gms", "kg", "kgs", "mg"}
_VOLUME_UNITS = {"ml", "l", "ltr", "ltrs", "litre", "liter"}


class LM007UnitSalePriceRule(BaseRule):
    """Unit sale price validation."""

    rule_id = "LM-007"
    rule_name = "Unit Sale Price"
    legal_basis = "Rule 6(1)(f) / applicable unit-sale-price provisions"

    def evaluate(self, ctx: ComplianceContext) -> RuleResult:
        mrp_value = ctx.nested_field("mrp", "value")
        nq_value = ctx.nested_field("net_quantity", "value")
        nq_unit = ctx.nested_field("net_quantity", "unit")
        raw = ctx.raw_text or ""

        # Check if unit sale price is explicitly declared in OCR text
        usp_label = re.search(
            r"(?:USP|UNIT\s+SALE\s+PRICE|PRICE\s+PER)",
            raw,
            re.IGNORECASE,
        )

        # We need MRP and net quantity to calculate
        if mrp_value is None or nq_value is None or nq_unit is None:
            if usp_label:
                # USP label found but we can't verify it
                start = max(0, usp_label.start())
                end = min(len(raw), usp_label.end() + 40)
                snippet = raw[start:end].strip()
                return RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    legal_basis=self.legal_basis,
                    status=RuleStatus.WARNING,
                    severity=RuleSeverity.MEDIUM,
                    field="unit_sale_price",
                    message="A unit-sale-price label was found but could not be fully verified.",
                    evidence=snippet,
                    confidence="LOW",
                )

            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.NOT_VERIFIABLE,
                severity=RuleSeverity.MEDIUM,
                field="unit_sale_price",
                message=(
                    "Insufficient data to verify unit sale price. "
                    "Both MRP and net quantity are required."
                ),
                evidence=None,
                confidence="LOW",
            )

        # Normalise to base units for calculation
        unit_lower = nq_unit.lower()
        quantity_grams = None
        price_basis = None

        if unit_lower in _WEIGHT_UNITS:
            if unit_lower == "kg":
                quantity_grams = nq_value * 1000
            elif unit_lower == "mg":
                quantity_grams = nq_value / 1000
            else:
                quantity_grams = nq_value
            price_basis = "per gram" if quantity_grams < 1000 else "per kg"
        elif unit_lower in _VOLUME_UNITS:
            if unit_lower == "l":
                quantity_ml = nq_value * 1000
            else:
                quantity_ml = nq_value
            price_basis = "per ml" if quantity_ml < 1000 else "per litre"
        else:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.NOT_APPLICABLE,
                severity=RuleSeverity.LOW,
                field="unit_sale_price",
                message=f"Unit sale price calculation is not applicable for unit '{nq_unit}'.",
                evidence=None,
                confidence="LOW",
            )

        # Calculate expected unit price
        if price_basis == "per gram" and quantity_grams:
            unit_price = mrp_value / quantity_grams
        elif price_basis == "per kg" and quantity_grams:
            unit_price = mrp_value / (quantity_grams / 1000)
        elif price_basis == "per ml":
            unit_price = mrp_value / quantity_ml if quantity_ml else None
        elif price_basis == "per litre":
            unit_price = mrp_value / (quantity_ml / 1000) if quantity_ml else None
        else:
            unit_price = None

        if unit_price is None or unit_price <= 0:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.NOT_VERIFIABLE,
                severity=RuleSeverity.MEDIUM,
                field="unit_sale_price",
                message="Could not calculate unit sale price from available data.",
                evidence=None,
                confidence="LOW",
            )

        # Check if OCR mentions a declared USP and whether it is consistent
        if usp_label:
            # Try to extract the declared USP value
            usp_match = re.search(
                r"(?:USP|UNIT\s+SALE\s+PRICE|PRICE\s+PER)\s*[:=]?\s*"
                r"[₹Rs\.]*\s*(\d+[\d,.]*)",
                raw,
                re.IGNORECASE,
            )
            if usp_match:
                try:
                    declared_usp = float(usp_match.group(1).replace(",", ""))
                    # Allow 10% tolerance for rounding
                    tolerance = max(declared_usp * 0.10, 0.01)
                    if abs(declared_usp - unit_price) <= tolerance:
                        return RuleResult(
                            rule_id=self.rule_id,
                            rule_name=self.rule_name,
                            legal_basis=self.legal_basis,
                            status=RuleStatus.PASS,
                            severity=RuleSeverity.MEDIUM,
                            field="unit_sale_price",
                            message=f"Declared USP is consistent with calculated unit price ({price_basis}).",
                            evidence=f"Declared: {declared_usp}, Calculated: {unit_price:.4f}",
                            confidence="MEDIUM",
                        )
                    else:
                        return RuleResult(
                            rule_id=self.rule_id,
                            rule_name=self.rule_name,
                            legal_basis=self.legal_basis,
                            status=RuleStatus.FAIL,
                            severity=RuleSeverity.MEDIUM,
                            field="unit_sale_price",
                            message=f"Declared USP ({declared_usp}) is inconsistent with calculated unit price ({unit_price:.4f}).",
                            evidence=f"Declared: {declared_usp}, Calculated: {unit_price:.4f}",
                            confidence="MEDIUM",
                        )
                except (ValueError, IndexError):
                    pass

        # No USP declared — information is insufficient for a definitive result
        calculated_str = f"₹{unit_price:.4f} {price_basis}"
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            legal_basis=self.legal_basis,
            status=RuleStatus.NOT_VERIFIABLE,
            severity=RuleSeverity.MEDIUM,
            field="unit_sale_price",
            message=(
                f"No unit sale price declaration was detected. "
                f"Expected approximately {calculated_str} based on "
                f"MRP ₹{mrp_value} and net quantity {nq_value} {nq_unit}."
            ),
            evidence=f"MRP: ₹{mrp_value}, Net Qty: {nq_value} {nq_unit}",
            confidence="MEDIUM",
        )
