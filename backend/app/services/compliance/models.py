"""
Compliance models — data structures for rule evaluation results.

Defines the core types used throughout the compliance engine:
- RuleStatus: PASS/FAIL/WARNING/NOT_VERIFIABLE/NOT_APPLICABLE
- RuleSeverity: LOW/MEDIUM/HIGH/CRITICAL
- RuleResult: Individual rule evaluation outcome
- ComplianceSummary: Aggregate counts
- ComplianceOverallStatus: Final assessment
"""

from __future__ import annotations

from enum import Enum
from typing import Optional
from dataclasses import dataclass, field, asdict


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class RuleStatus(str, Enum):
    """Possible outcomes for a single rule evaluation."""
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    NOT_VERIFIABLE = "NOT_VERIFIABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class RuleSeverity(str, Enum):
    """Severity classification for rule violations."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class OverallStatus(str, Enum):
    """Final compliance assessment status."""
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    INCOMPLETE = "INCOMPLETE"


class InspectionContext(str, Enum):
    """Context in which the inspection is performed."""
    PHYSICAL_PACKAGE = "PHYSICAL_PACKAGE"
    RETAIL = "RETAIL"
    E_COMMERCE = "E_COMMERCE"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class RuleResult:
    """
    Outcome of evaluating a single compliance rule.

    Every rule must produce exactly one RuleResult.  The result preserves
    the original evidence so downstream consumers can verify the assessment
    independently.
    """
    rule_id: str
    rule_name: str
    legal_basis: str
    status: RuleStatus
    severity: RuleSeverity
    field: Optional[str]
    message: str
    evidence: Optional[str] = None
    confidence: str = "MEDIUM"

    def to_dict(self) -> dict:
        """Serialize to a plain dictionary."""
        d = asdict(self)
        d["status"] = self.status.value
        d["severity"] = self.severity.value
        return d


@dataclass
class ComplianceSummary:
    """Aggregate counts of rule outcomes."""
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    not_verifiable: int = 0
    not_applicable: int = 0
    rules_checked: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Overall status calculation
# ---------------------------------------------------------------------------

def calculate_overall_status(results: list[RuleResult]) -> OverallStatus:
    """
    Derive the final compliance assessment from individual rule results.

    Logic:
    - Any FAIL (especially CRITICAL/HIGH) → NON_COMPLIANT
    - No FAIL, has WARNING(s) → REVIEW_REQUIRED
    - No FAIL, no WARNING, has NOT_VERIFIABLE → COMPLIANT
      (not verifiable ≠ non-compliant; system cannot verify, so it
       does not penalize)
    - All applicable rules PASS → COMPLIANT
    - All rules NOT_APPLICABLE → INCOMPLETE
    """
    statuses = [r.status for r in results]

    has_fail = RuleStatus.FAIL in statuses
    has_warning = RuleStatus.WARNING in statuses

    applicable = [s for s in statuses if s not in (RuleStatus.NOT_APPLICABLE, RuleStatus.NOT_VERIFIABLE)]

    if has_fail:
        return OverallStatus.NON_COMPLIANT

    if has_warning:
        return OverallStatus.REVIEW_REQUIRED

    if all(s == RuleStatus.NOT_APPLICABLE for s in statuses):
        return OverallStatus.INCOMPLETE

    # If no PASS at all (all NOT_VERIFIABLE/NOT_APPLICABLE), it's INCOMPLETE
    has_any_pass = RuleStatus.PASS in statuses
    if not has_any_pass and not has_fail and not has_warning:
        return OverallStatus.INCOMPLETE

    if applicable and all(s == RuleStatus.PASS for s in applicable):
        return OverallStatus.COMPLIANT

    # No FAIL, no WARNING — even if some are NOT_VERIFIABLE, treat as COMPLIANT
    # (the system couldn't verify but found no issues)
    if not has_fail and not has_warning:
        return OverallStatus.COMPLIANT

    return OverallStatus.REVIEW_REQUIRED


def build_summary(results: list[RuleResult]) -> ComplianceSummary:
    """Count each status category across all rule results."""
    return ComplianceSummary(
        passed=sum(1 for r in results if r.status == RuleStatus.PASS),
        failed=sum(1 for r in results if r.status == RuleStatus.FAIL),
        warnings=sum(1 for r in results if r.status == RuleStatus.WARNING),
        not_verifiable=sum(1 for r in results if r.status == RuleStatus.NOT_VERIFIABLE),
        not_applicable=sum(1 for r in results if r.status == RuleStatus.NOT_APPLICABLE),
        rules_checked=len(results),
    )
