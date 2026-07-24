"""Lowering for the connected-components edge-list route."""

from __future__ import annotations

from rextio.plugins.api import ClaimSite, LoweredExpr, LoweringContext

from rextio_networkx import rust_snippets
from rextio_networkx.claim.components import (
    CC_RULE,
    CC_TARGET,
    IS_CONNECTED_RULE,
    IS_CONNECTED_TARGET,
    NUMBER_CONNECTED_COMPONENTS_RULE,
    NUMBER_CONNECTED_COMPONENTS_TARGET,
    RESIDENT_CC_RULE,
    RESIDENT_CC_TARGET,
)
from rextio_networkx.diagnostics import COMPONENT_LIST, EDGELIST_I64, GRAPH_I64


def _require_static_contract(
    claimed: ClaimSite,
    ctx: LoweringContext,
    *,
    target: str,
    rule_id: str,
    result_type: str,
    operand_types: tuple[str, ...],
) -> tuple[str, ...]:
    """Reject forged claim metadata before emitting the components helper.

    A ``ClaimSite`` originates in core analysis, but plugin lowerers are a
    trust boundary: they must not turn a caller-supplied rule or result type
    into Rust merely because its target happens to look familiar.
    """
    if (
        claimed.kind != "call"
        or claimed.target != target
        or claimed.rule_id != rule_id
        or claimed.result_type != result_type
        or claimed.operand_types != operand_types
        or claimed.keywords
        or claimed.receiver is not None
        or ctx.receiver is not None
    ):
        raise ValueError(
            f"rextio-networkx connected-components lowering contract mismatch for {target!r}"
        )

    operands = tuple(ctx.operands)
    # Explicit ValueError (not assert) so the guard survives python -O and
    # fails closed on malformed LoweringContext metadata rather than emitting
    # bad Rust.
    if len(operands) != len(operand_types):
        raise ValueError(
            "rextio-networkx connected-components lowering requires exactly one "
            f"operand, got {len(operands)}"
        )
    return operands


def try_lower(claimed: ClaimSite, ctx: LoweringContext) -> LoweredExpr | None:
    """Return a lowered expression for the adapter call, or None if not this lane."""
    if claimed.target == RESIDENT_CC_TARGET:
        operands = _require_static_contract(
            claimed,
            ctx,
            target=RESIDENT_CC_TARGET,
            rule_id=RESIDENT_CC_RULE,
            result_type=COMPONENT_LIST,
            operand_types=(GRAPH_I64,),
        )
        return LoweredExpr(
            rust=f"{rust_snippets.resident_cc_call_name()}(py, &{operands[0]})?",
            helpers=rust_snippets.resident_cc_helpers(),
        )
    if claimed.target == NUMBER_CONNECTED_COMPONENTS_TARGET:
        operands = _require_static_contract(
            claimed,
            ctx,
            target=NUMBER_CONNECTED_COMPONENTS_TARGET,
            rule_id=NUMBER_CONNECTED_COMPONENTS_RULE,
            result_type="int",
            operand_types=(GRAPH_I64,),
        )
        return LoweredExpr(
            rust=f"{rust_snippets.number_connected_components_call_name()}(&{operands[0]})?",
            helpers=rust_snippets.number_connected_components_helpers(),
        )
    if claimed.target == IS_CONNECTED_TARGET:
        operands = _require_static_contract(
            claimed,
            ctx,
            target=IS_CONNECTED_TARGET,
            rule_id=IS_CONNECTED_RULE,
            result_type="bool",
            operand_types=(GRAPH_I64,),
        )
        return LoweredExpr(
            rust=f"{rust_snippets.is_connected_call_name()}(py, &{operands[0]})?",
            helpers=rust_snippets.is_connected_helpers(),
        )
    if claimed.target != CC_TARGET:
        return None
    operands = _require_static_contract(
        claimed,
        ctx,
        target=CC_TARGET,
        rule_id=CC_RULE,
        result_type=COMPONENT_LIST,
        operand_types=(EDGELIST_I64,),
    )
    name = rust_snippets.cc_call_name()
    helpers = rust_snippets.cc_helpers()
    # The API-1.3 materialized boundary has already converted the raw list to
    # ``RxtNxEdgeListI64`` with exact validation. Borrow that owned typed value;
    # the helper builds petgraph and returns a Python list, hence ``?``.
    return LoweredExpr(
        rust=f"{name}(py, &{operands[0]})?",
        helpers=helpers,
    )
