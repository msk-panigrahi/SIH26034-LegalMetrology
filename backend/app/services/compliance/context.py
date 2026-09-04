"""
Compliance context — bundles all data needed by the rule evaluation engine.

The context is constructed once per inspection and passed to every rule.
It provides read-only access to the raw OCR text, the extracted fields,
and inspection metadata.
"""

from __future__ import annotations

from typing import Any, Optional
from dataclasses import dataclass, field

from app.services.compliance.models import InspectionContext


@dataclass
class ComplianceContext:
    """
    Immutable bundle of inspection data used by all compliance rules.

    Attributes:
        inspection_id: Database ID of the inspection.
        raw_text: Full OCR-extracted text from the package image.
        extracted_fields: Structured field dictionary produced by the
            field extraction service (may be None if extraction was skipped).
        ocr_confidence: Average OCR confidence score (0–100).
        inspection_context: Physical, retail, e-commerce, or unknown.
        rule_version: Version tag for the rule set being applied.
        product_category: Optional category hint (food, cosmetic, etc.).
    """

    inspection_id: int
    raw_text: str
    extracted_fields: Optional[dict[str, Any]] = None
    ocr_confidence: Optional[float] = None
    inspection_context: InspectionContext = InspectionContext.UNKNOWN
    rule_version: str = "LM-PCR-2026"
    product_category: Optional[str] = None

    # -- Convenience helpers -------------------------------------------------

    @property
    def has_raw_text(self) -> bool:
        """True if there is substantive OCR text to work with."""
        return bool(self.raw_text and self.raw_text.strip())

    @property
    def has_extracted_fields(self) -> bool:
        """True if the field extraction step produced a result."""
        return self.extracted_fields is not None and len(self.extracted_fields) > 0

    def field(self, name: str) -> Optional[Any]:
        """Return a single extracted field value, or None."""
        if not self.extracted_fields:
            return None
        return self.extracted_fields.get(name)

    def nested_field(self, parent: str, child: str) -> Optional[Any]:
        """Return a nested extracted field value, or None."""
        parent_val = self.field(parent)
        if parent_val is None or not isinstance(parent_val, dict):
            return None
        return parent_val.get(child)

    # -- Raw-text search helpers ---------------------------------------------

    def text_contains(self, pattern: str, flags: int = 0) -> bool:
        """Check whether the raw OCR text matches a regex."""
        import re
        return bool(re.search(pattern, self.raw_text, flags))

    def text_find(self, pattern: str, flags: int = 0) -> Optional[str]:
        """Return the first match of a regex in the raw text, or None."""
        import re
        m = re.search(pattern, self.raw_text, flags)
        return m.group(0) if m else None
