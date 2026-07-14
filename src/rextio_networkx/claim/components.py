"""Claim decisions for the connected-components edge-list route."""

from __future__ import annotations

from rextio.plugins.api import Claimed, ClaimResult, ClaimSite, NotCovered

from rextio_networkx.diagnostics import COMPONENT_LIST, is_edgelist_type, not_covered_or_rejected

#: The covered adapter call target (resolved dotted name).
CC_TARGET = "rextio_networkx.connected_components_from_edgelist"

#: The rule id this lane claims under (must match a described rule record).
CC_RULE = "rextio-networkx/connected-components-edgelist"


def try_claim(site: ClaimSite) -> ClaimResult | None:
    """Return a claim result for the adapter call, or None if not this lane."""
    if site.kind != "call" or site.target != CC_TARGET:
        return None
    if site.keywords:
        # The adapter takes a single positional argument; a keyword call is an
        # unsupported call SHAPE, so hand it back for core's own diagnostic.
        return NotCovered()
    operands = site.operand_types
    if len(operands) != 1:
        # Wrong arity is an unsupported call shape, not an argument-type
        # problem; NotCovered so core's RXT030 names the real cause.
        return NotCovered()
    (operand,) = operands
    if operand is None:
        # Unresolved argument: core continues as if the plugin did not exist.
        return NotCovered()
    if is_edgelist_type(operand):
        return Claimed(rule_id=CC_RULE, result_type=COMPONENT_LIST)
    # Known but unsupported argument type: deliver the plugin's guidance.
    return not_covered_or_rejected(site)
