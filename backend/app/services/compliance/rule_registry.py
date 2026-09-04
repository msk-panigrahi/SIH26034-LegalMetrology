"""
Rule registry — central list of all compliance rules in evaluation order.

Import this module to get access to ``RULE_REGISTRY``, an ordered list of
rule instances that the ComplianceEngine will iterate over.
"""

from __future__ import annotations

from app.services.compliance.base_rule import BaseRule

from app.services.compliance.rules.declaration_rules import (
    LM001CommodityNameRule,
    LM002ResponsibleEntityRule,
    LM003AddressRule,
    LM004CountryOfOriginRule,
)
from app.services.compliance.rules.quantity_rules import (
    LM005NetQuantityRule,
)
from app.services.compliance.rules.mrp_rules import (
    LM006MRPRule,
    LM007UnitSalePriceRule,
)
from app.services.compliance.rules.date_rules import (
    LM008DateDeclarationRule,
    LM009BestBeforeRule,
)
from app.services.compliance.rules.package_rules import (
    LM010ConsumerCareRule,
    LM011DimensionsRule,
    LM012LegibilityRule,
    LM013MultiPieceRule,
)


# Ordered list of rule instances — the engine evaluates them in this order.
RULE_REGISTRY: list[BaseRule] = [
    LM001CommodityNameRule(),
    LM002ResponsibleEntityRule(),
    LM003AddressRule(),
    LM004CountryOfOriginRule(),
    LM005NetQuantityRule(),
    LM006MRPRule(),
    LM007UnitSalePriceRule(),
    LM008DateDeclarationRule(),
    LM009BestBeforeRule(),
    LM010ConsumerCareRule(),
    LM011DimensionsRule(),
    LM012LegibilityRule(),
    LM013MultiPieceRule(),
]
