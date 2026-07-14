"""Lowering for the connected-components edge-list route."""

from __future__ import annotations

from rextio.plugins.api import ClaimSite, LoweredExpr, LoweringContext

from rextio_networkx import rust_snippets
from rextio_networkx.claim.components import CC_TARGET


def try_lower(claimed: ClaimSite, ctx: LoweringContext) -> LoweredExpr | None:
    """Return a lowered expression for the adapter call, or None if not this lane."""
    if claimed.kind != "call" or claimed.target != CC_TARGET:
        return None
    # Covered lower-time invariant: exactly one rendered operand (the edge list).
    # Explicit ValueError (not assert) so the guard survives python -O and fails
    # closed on malformed LoweringContext metadata rather than emitting bad Rust.
    if len(ctx.operands) != 1:
        raise ValueError(
            "rextio-networkx connected-components lowering requires exactly one "
            f"operand, got {len(ctx.operands)}"
        )
    name = rust_snippets.cc_call_name()
    helper = rust_snippets.cc_helper()
    # The helper takes the `py` token (in scope for plugin-typed functions) and
    # a borrow of the edge-list operand; it returns PyResult, so end with `?`.
    return LoweredExpr(
        rust=f"{name}(py, &{ctx.operands[0]})?",
        helpers=(helper,),
    )
