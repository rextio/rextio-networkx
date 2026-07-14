"""Lower router: dispatch claimed sites to feature-owned lower modules."""

from __future__ import annotations

from rextio.plugins.api import ClaimSite, LoweredExpr, LoweringContext

from rextio_networkx.lower import components

__all__ = ["lower"]


def lower(claimed: ClaimSite, ctx: LoweringContext) -> LoweredExpr:
    """Emit the Rust expression for a previously claimed site.

    The emitted expression calls one deterministic ``petgraph`` helper and ends
    with ``?``; the helper ``fn`` travels in ``helpers`` and is deduplicated by
    exact text in core codegen.
    """
    result = components.try_lower(claimed, ctx)
    if result is not None:
        return result
    raise ValueError(
        f"rextio-networkx cannot lower unclaimed site: {claimed.kind} {claimed.target!r}"
    )
