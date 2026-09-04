"""
Base rule — abstract class that every compliance rule must implement.

Concrete rules inherit from BaseRule and override the `evaluate` method.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.services.compliance.context import ComplianceContext
from app.services.compliance.models import RuleResult


class BaseRule(ABC):
    """Abstract base class for all compliance rules."""

    # Subclasses must define these class-level attributes:
    rule_id: str          # e.g. "LM-001"
    rule_name: str        # e.g. "Common / Generic Name"
    legal_basis: str      # e.g. "Rule 6(1)(b)"

    @abstractmethod
    def evaluate(self, ctx: ComplianceContext) -> RuleResult:
        """
        Evaluate the rule against the supplied compliance context.

        Args:
            ctx: The compliance context containing OCR text, extracted
                 fields, and inspection metadata.

        Returns:
            A single RuleResult describing the outcome.
        """
        ...
