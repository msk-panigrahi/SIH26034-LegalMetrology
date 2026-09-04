"""
Declaration rules — LM-001 to LM-004.

These rules check the fundamental declaratory requirements that appear
on every pre-packaged commodity under the Legal Metrology (Packaged
Commodities) Rules, 2011.
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
# LM-001 — Common / Generic Name
# ---------------------------------------------------------------------------

# Well-known commodity type words that satisfy the generic-name requirement
# when they appear in the product_name field or the raw text.
_GENERIC_TYPE_WORDS = re.compile(
    r"(?:BATHING\s+BAR|SOAP|BISCUIT[S]?|CHIPS|NOODLES|MASALA|"
    r"DETERGENT|WASHING\s+POWDER|SHAMPOO|CREAM|POWDER|PASTE|"
    r"TOOTH[PASTE]?|OIL|GHEE|RICE|FLOUR|SALT|SUGAR|"
    r"JUICE|MILK|WATER|BEVERAGE|SNACK[S]?|CHOCOLATE|"
    r"WAFFLE[S]?|BREAD|COOKI[ES]+|PULSES|ATTA|Maida|"
    r"HAIR\s+OIL|FACE\s+WASH|MOISTURISER|MOISTURIZER|"
    r"LIQUID|DISHWASH|FLOOR\s+CLEANER|AIR\s+FRESHENER)",
    re.IGNORECASE,
)


class LM001CommodityNameRule(BaseRule):
    """Rule 6(1)(b) — Common or generic name of the commodity."""

    rule_id = "LM-001"
    rule_name = "Common / Generic Name"
    legal_basis = "Rule 6(1)(b)"

    def evaluate(self, ctx: ComplianceContext) -> RuleResult:
        product_name = ctx.field("product_name")
        raw = ctx.raw_text or ""

        # Strategy 1: Check extracted product_name for a generic type word
        if product_name and _GENERIC_TYPE_WORDS.search(product_name):
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.PASS,
                severity=RuleSeverity.HIGH,
                field="product_name",
                message=(
                    "The package declares a common/generic commodity name."
                ),
                evidence=product_name,
                confidence="HIGH",
            )

        # Strategy 2: Scan raw OCR text for a generic type word
        m = _GENERIC_TYPE_WORDS.search(raw)
        if m:
            start = max(0, m.start() - 30)
            end = min(len(raw), m.end() + 30)
            snippet = raw[start:end].strip()
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.PASS,
                severity=RuleSeverity.HIGH,
                field="product_name",
                message="A generic commodity name was detected in the package text.",
                evidence=snippet,
                confidence="MEDIUM",
            )

        # Strategy 3: If product_name exists but has no generic word,
        # treat as PASS with lower confidence (most packages have this)
        if product_name:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.PASS,
                severity=RuleSeverity.MEDIUM,
                field="product_name",
                message=(
                    "A product name was detected on the package."
                ),
                evidence=product_name,
                confidence="MEDIUM",
            )

        # No usable information
        if not ctx.has_raw_text:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.NOT_VERIFIABLE,
                severity=RuleSeverity.MEDIUM,
                field="product_name",
                message="No OCR text available to verify the commodity name.",
                evidence=None,
                confidence="LOW",
            )

        # OCR text exists but no product name found → FAIL (mandatory declaration missing)
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            legal_basis=self.legal_basis,
            status=RuleStatus.FAIL,
            severity=RuleSeverity.HIGH,
            field="product_name",
            message=(
                "Common / generic commodity name is required but could not "
                "be identified from the package text."
            ),
            evidence=None,
            confidence="MEDIUM",
        )


# ---------------------------------------------------------------------------
# LM-002 — Manufacturer / Packer / Importer Declaration
# ---------------------------------------------------------------------------

_ENTITY_LABELS = re.compile(
    r"(?:MFG\.?\s*BY|MANUFACTURED?\s+BY|MANUFACTURER|"
    r"PACKED\s+BY|PACKAGED\s+BY|IMPORTED?\s+BY|"
    r"MARKETED?\s+BY|MKTD?\.?\s*BY|BRAND\s+OWNER)",
    re.IGNORECASE,
)


class LM002ResponsibleEntityRule(BaseRule):
    """Rule 6(1)(a) — Responsible manufacturer/packer/importer declaration."""

    rule_id = "LM-002"
    rule_name = "Manufacturer / Packer / Importer Declaration"
    legal_basis = "Rule 6(1)(a)"

    def evaluate(self, ctx: ComplianceContext) -> RuleResult:
        manufacturer = ctx.field("manufacturer")
        marketer = ctx.field("marketer")

        if manufacturer:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.PASS,
                severity=RuleSeverity.HIGH,
                field="manufacturer",
                message="A manufacturer/packer declaration was detected.",
                evidence=manufacturer,
                confidence="HIGH",
            )

        if marketer:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.PASS,
                severity=RuleSeverity.MEDIUM,
                field="marketer",
                message="A marketer/brand-owner declaration was detected.",
                evidence=marketer,
                confidence="MEDIUM",
            )

        # Check raw text for entity labels
        raw_match = _ENTITY_LABELS.search(ctx.raw_text or "")
        if raw_match:
            start = max(0, raw_match.start())
            end = min(len(ctx.raw_text), raw_match.end() + 80)
            snippet = ctx.raw_text[start:end].strip()
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.WARNING,
                severity=RuleSeverity.MEDIUM,
                field="manufacturer",
                message="An entity declaration label was found but extraction was incomplete.",
                evidence=snippet,
                confidence="LOW",
            )

        if not ctx.has_raw_text:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.NOT_VERIFIABLE,
                severity=RuleSeverity.HIGH,
                field="manufacturer",
                message="No OCR text available to verify the responsible entity declaration.",
                evidence=None,
                confidence="LOW",
            )

        # OCR text exists but no manufacturer found → FAIL (mandatory declaration missing)
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            legal_basis=self.legal_basis,
            status=RuleStatus.FAIL,
            severity=RuleSeverity.CRITICAL,
            field="manufacturer",
            message=(
                "Manufacturer / packer / importer declaration is required "
                "but was not found in the package text."
            ),
            evidence=None,
            confidence="MEDIUM",
        )


# ---------------------------------------------------------------------------
# LM-003 — Address Declaration
# ---------------------------------------------------------------------------

_ADDRESS_INDICATORS = re.compile(
    r"(?:SURVEY\s+NO|PLOT\s+NO|P\.?O\.?\s*BOX|ROAD|STREET|"
    r"VILLAGE|DISTRICT|PIN\s*CODE|STATE|ZONE|PHASE|"
    r"BLOCK|SECTOR|NAGAR|COLONY|MARG|LANE|"
    r"\d{6})",  # Indian PIN code
    re.IGNORECASE,
)


class LM003AddressRule(BaseRule):
    """Address of manufacturer/packer/importer."""

    rule_id = "LM-003"
    rule_name = "Address Declaration"
    legal_basis = "Rule 6(1)(a)"

    def evaluate(self, ctx: ComplianceContext) -> RuleResult:
        address = ctx.field("manufacturer_address")

        if address and len(address) >= 10:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.PASS,
                severity=RuleSeverity.HIGH,
                field="manufacturer_address",
                message="A manufacturer/packer address was detected.",
                evidence=address[:200],
                confidence="HIGH",
            )

        # Check raw text for address indicators near manufacturer
        raw = ctx.raw_text or ""
        if _ADDRESS_INDICATORS.search(raw):
            m = _ADDRESS_INDICATORS.search(raw)
            start = max(0, m.start() - 40)
            end = min(len(raw), m.end() + 60)
            snippet = raw[start:end].strip()
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.WARNING,
                severity=RuleSeverity.MEDIUM,
                field="manufacturer_address",
                message="Address-like text was found but could not be fully extracted.",
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
                field="manufacturer_address",
                message="No OCR text available to verify the address declaration.",
                evidence=None,
                confidence="LOW",
            )

        # OCR text exists but no address found → WARNING (important but not always clearly detectable)
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            legal_basis=self.legal_basis,
            status=RuleStatus.WARNING,
            severity=RuleSeverity.MEDIUM,
            field="manufacturer_address",
            message=(
                "Manufacturer address could not be fully verified from the "
                "package text. Officer review may be needed."
            ),
            evidence=None,
            confidence="LOW",
        )


# ---------------------------------------------------------------------------
# LM-004 — Country of Origin
# ---------------------------------------------------------------------------

class LM004CountryOfOriginRule(BaseRule):
    """Country of origin (particularly relevant for imported products)."""

    rule_id = "LM-004"
    rule_name = "Country of Origin"
    legal_basis = "Rule 6(1)(a)"

    def evaluate(self, ctx: ComplianceContext) -> RuleResult:
        country = ctx.field("country_of_origin")

        if country:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.PASS,
                severity=RuleSeverity.MEDIUM,
                field="country_of_origin",
                message="Country of origin declaration was detected.",
                evidence=country,
                confidence="HIGH",
            )

        # Check if text mentions "MADE IN" or "COUNTRY OF ORIGIN"
        raw = ctx.raw_text or ""
        if re.search(r"(?:MADE\s+IN|COUNTRY\s+OF\s+ORIGIN)", raw, re.IGNORECASE):
            m = re.search(r"(?:MADE\s+IN|COUNTRY\s+OF\s+ORIGIN).{0,30}", raw, re.IGNORECASE)
            snippet = m.group(0).strip() if m else None
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                legal_basis=self.legal_basis,
                status=RuleStatus.WARNING,
                severity=RuleSeverity.MEDIUM,
                field="country_of_origin",
                message="Country-of-origin label found but value could not be extracted.",
                evidence=snippet,
                confidence="LOW",
            )

        # Domestic product: absence is typically not a violation
        # Country of origin declaration is mandatory only for imported products
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            legal_basis=self.legal_basis,
            status=RuleStatus.NOT_APPLICABLE,
            severity=RuleSeverity.LOW,
            field="country_of_origin",
            message=(
                "Country of origin was not explicitly declared. This is "
                "typically required for imported products. For domestic "
                "products, this declaration may not be mandatory."
            ),
            evidence=None,
            confidence="LOW",
        )
