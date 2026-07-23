"""Rust expressions for resident graph construction and traversal."""

from __future__ import annotations

from rextio.plugins.api import ClaimSite, LoweredExpr, LoweringContext

from rextio_networkx.claim.traversal import (
    BFS_TARGET,
    DIJKSTRA_TARGET,
    GRAPH_TARGET,
    SHORTEST_PATH_LENGTHS_TARGET,
    WEIGHTED_GRAPH_TARGET,
)
from rextio_networkx.rust_snippets.traversal import (
    BFS_EDGES,
    DIJKSTRA_LENGTHS,
    GRAPH_FROM_EDGELIST,
    SHORTEST_PATH_LENGTHS,
    WEIGHTED_GRAPH_FROM_EDGELIST,
    bfs_helpers,
    dijkstra_helpers,
    graph_constructor_helpers,
    shortest_path_lengths_helpers,
    weighted_graph_constructor_helpers,
)


def _require_operands(target: str, operands: tuple[str, ...], count: int) -> None:
    if len(operands) != count:
        raise ValueError(
            f"rextio-networkx lowering for {target!r} requires exactly {count} "
            f"operands, got {len(operands)}"
        )


def try_lower(claimed: ClaimSite, ctx: LoweringContext) -> LoweredExpr | None:
    """Lower a recognized exact traversal call."""
    if claimed.kind != "call":
        return None
    operands = tuple(ctx.operands)
    if claimed.target == GRAPH_TARGET:
        _require_operands(claimed.target, operands, 1)
        return LoweredExpr(
            rust=f"{GRAPH_FROM_EDGELIST}(&{operands[0]})",
            helpers=graph_constructor_helpers(),
        )
    if claimed.target == WEIGHTED_GRAPH_TARGET:
        _require_operands(claimed.target, operands, 1)
        return LoweredExpr(
            rust=f"{WEIGHTED_GRAPH_FROM_EDGELIST}(&{operands[0]})",
            helpers=weighted_graph_constructor_helpers(),
        )
    if claimed.target == BFS_TARGET:
        _require_operands(claimed.target, operands, 2)
        return LoweredExpr(
            rust=f"{BFS_EDGES}(py, &{operands[0]}, {operands[1]})?",
            helpers=bfs_helpers(),
        )
    if claimed.target == SHORTEST_PATH_LENGTHS_TARGET:
        _require_operands(claimed.target, operands, 2)
        return LoweredExpr(
            rust=f"{SHORTEST_PATH_LENGTHS}(py, &{operands[0]}, {operands[1]})?",
            helpers=shortest_path_lengths_helpers(),
        )
    if claimed.target == DIJKSTRA_TARGET:
        _require_operands(claimed.target, operands, 2)
        return LoweredExpr(
            rust=f"{DIJKSTRA_LENGTHS}(py, &{operands[0]}, {operands[1]})?",
            helpers=dijkstra_helpers(),
        )
    return None


__all__ = ["try_lower"]
