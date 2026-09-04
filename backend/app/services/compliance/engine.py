"""
Compliance engine — orchestrates rule evaluation and builds the final result.

The engine receives a ComplianceContext, iterates over every registered rule,
collects results, and derives an overall compliance status.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.services.compliance.context import ComplianceContext
from app.services.compliance.models import (
    RuleResult,
    OverallStatus,
    calculate_overall_status,
    build_summary,
)
from app.services.compliance.rule_registry import RULE_REGISTRY

logger = logging.getLogger(__name__)


class ComplianceEngine:
    """
    Deterministic compliance evaluation engine.

    Usage::

        engine = ComplianceEngine()
        overall, results = engine.evaluate(context)
    """

    def __init__(self, rule_version: str = "LM-PCR-2026"):
        self.rule_version = rule_version

    def evaluate(
        self, ctx: ComplianceContext
    ) -> tuple[OverallStatus, list[RuleResult]]:
        """
        Run every registered rule against the supplied context.

        Args:
            ctx: Compliance context with OCR text and extracted fields.

        Returns:
            A tuple of (overall_status, list_of_rule_results).
        """
        results: list[RuleResult] = []

        for rule in RULE_REGISTRY:
            try:
                result = rule.evaluate(ctx)
                results.append(result)
                logger.debug(
                    "Rule %s → %s (%s)",
                    rule.rule_id,
                    result.status.value,
                    result.severity.value,
                )
            except Exception as exc:
                # A rule that crashes must not take down the whole evaluation.
                logger.exception("Rule %s raised an exception", rule.rule_id)
                results.append(
                    RuleResult(
                        rule_id=rule.rule_id,
                        rule_name=rule.rule_name,
                        legal_basis=rule.legal_basis,
                        status=RuleStatus.WARNING,
                        severity=RuleSeverity.MEDIUM,
                        field=None,
                        message=f"Rule evaluation failed internally: {exc}",
                        evidence=None,
                        confidence="LOW",
                    )
                )

        overall = calculate_overall_status(results)
        logger.info(
            "Compliance evaluation complete: %s  (%d rules checked)",
            overall.value,
            len(results),
        )
        return overall, results


# Avoid circular import at module level — import RuleStatus/RuleSeverity lazily
# for the except branch above.
from app.services.compliance.models import RuleStatus, RuleSeverity  # noqa: E402
