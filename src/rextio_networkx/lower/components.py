"""Lowering for the connected-components edge-list route."""

from __future__ import annotations

from rextio.plugins.api import ClaimSite, LoweredExpr, LoweringContext

from rextio_networkx import rust_snippets
from rextio_networkx.claim.components import CC_RULE, CC_TARGET
from rextio_networkx.diagnostics import COMPONENT_LIST, EDGELIST_I64


def _require_static_contract(claimed: ClaimSite, ctx: LoweringContext) -> tuple[str, ...]:
    """Reject forged claim metadata before emitting the components helper.

    A ``ClaimSite`` originates in core analysis, but plugin lowerers are a
    trust boundary: they must not turn a caller-supplied rule or result type
    into Rust merely because its target happens to look familiar.
    """
    if (
        claimed.kind != "call"
        or claimed.target != CC_TARGET
        or claimed.rule_id != CC_RULE
        or claimed.result_type != COMPONENT_LIST
        or claimed.operand_types != (EDGELIST_I64,)
        or claimed.keywords
        or claimed.receiver is not None
        or ctx.receiver is not None
    ):
        raise ValueError("rextio-networkx connected-components lowering contract mismatch")

    operands = tuple(ctx.operands)
    # Explicit ValueError (not assert) so the guard survives python -O and
    # fails closed on malformed LoweringContext metadata rather than emitting
    # bad Rust.
    if len(operands) != 1:
        raise ValueError(
            "rextio-networkx connected-components lowering requires exactly one "
            f"operand, got {len(operands)}"
        )
    return operands


def try_lower(claimed: ClaimSite, ctx: LoweringContext) -> LoweredExpr | None:
    """Return a lowered expression for the adapter call, or None if not this lane."""
    if claimed.target != CC_TARGET:
        return None
    operands = _require_static_contract(claimed, ctx)
    name = rust_snippets.cc_call_name()
    helpers = rust_snippets.cc_helpers()
    # The API-1.3 materialized boundary has already converted the raw list to
    # ``RxtNxEdgeListI64`` with exact validation. Borrow that owned typed value;
    # the helper builds petgraph and returns a Python list, hence ``?``.
    return LoweredExpr(
        rust=f"{name}(py, &{operands[0]})?",
        helpers=helpers,
    )
