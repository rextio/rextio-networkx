"""Claim decisions for the connected-components edge-list route."""

from __future__ import annotations

from rextio.plugins.api import Claimed, ClaimResult, ClaimSite, NotCovered

from rextio_networkx.diagnostics import (
    COMPONENT_LIST,
    GRAPH_I64,
    is_edgelist_type,
    not_covered_or_rejected,
    reject_site,
)

#: The covered adapter call target (resolved dotted name).
CC_TARGET = "rextio_networkx.connected_components_from_edgelist"

#: The rule id this lane claims under (must match a described rule record).
CC_RULE = "rextio-networkx/connected-components-edgelist"

#: Resident graph consumer target and rule.
RESIDENT_CC_TARGET = "rextio_networkx.connected_components"
RESIDENT_CC_RULE = "rextio-networkx/connected-components-resident"
NUMBER_CONNECTED_COMPONENTS_TARGET = "rextio_networkx.number_connected_components"
NUMBER_CONNECTED_COMPONENTS_RULE = "rextio-networkx/number-connected-components"
IS_CONNECTED_TARGET = "rextio_networkx.is_connected"
IS_CONNECTED_RULE = "rextio-networkx/is-connected"

_RESIDENT_TARGETS = frozenset(
    {
        RESIDENT_CC_TARGET,
        NUMBER_CONNECTED_COMPONENTS_TARGET,
        IS_CONNECTED_TARGET,
    }
)


def try_claim(site: ClaimSite) -> ClaimResult | None:
    """Return a claim result for the adapter call, or None if not this lane."""
    if site.kind != "call" or site.target not in {CC_TARGET, *_RESIDENT_TARGETS}:
        return None
    if site.target == RESIDENT_CC_TARGET:
        if site.keywords or tuple(site.operand_types) != (GRAPH_I64,):
            return reject_site(
                site,
                expected="the positional shape connected_components(GraphI64)",
            )
        return Claimed(rule_id=RESIDENT_CC_RULE, result_type=COMPONENT_LIST)
    if site.target == NUMBER_CONNECTED_COMPONENTS_TARGET:
        if site.keywords or tuple(site.operand_types) != (GRAPH_I64,):
            return reject_site(
                site,
                expected="the positional shape number_connected_components(GraphI64)",
            )
        return Claimed(rule_id=NUMBER_CONNECTED_COMPONENTS_RULE, result_type="int")
    if site.target == IS_CONNECTED_TARGET:
        if site.keywords or tuple(site.operand_types) != (GRAPH_I64,):
            return reject_site(site, expected="the positional shape is_connected(GraphI64)")
        return Claimed(rule_id=IS_CONNECTED_RULE, result_type="bool")
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
