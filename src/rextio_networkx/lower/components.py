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
    helpers = rust_snippets.cc_helpers()
    # The helper takes the `py` token (in scope for plugin-typed functions) and
    # a borrow of the raw edge-list operand (a Bound<PyList>); it extracts each
    # node label to i64 at the boundary (rejecting bool / out-of-i64) and
    # returns PyResult, so end with `?`. Its node-label extractor travels
    # alongside it and both are deduplicated by exact text in core codegen.
    return LoweredExpr(
        rust=f"{name}(py, &{ctx.operands[0]})?",
        helpers=helpers,
    )
