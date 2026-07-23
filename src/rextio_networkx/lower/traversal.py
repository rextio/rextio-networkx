"""Rust expressions for resident graph construction and traversal."""

from __future__ import annotations

from rextio.plugins.api import ClaimSite, LoweredExpr, LoweringContext

from rextio_networkx.claim.traversal import (
    BFS_RULE,
    BFS_TARGET,
    DIJKSTRA_RULE,
    DIJKSTRA_TARGET,
    GRAPH_RULE,
    GRAPH_TARGET,
    SHORTEST_PATH_LENGTHS_RULE,
    SHORTEST_PATH_LENGTHS_TARGET,
    WEIGHTED_GRAPH_RULE,
    WEIGHTED_GRAPH_TARGET,
)
from rextio_networkx.diagnostics import (
    BFS_EDGES_I64,
    DIJKSTRA_LENGTHS_I64,
    EDGELIST_I64,
    GRAPH_I64,
    NODE_I64,
    SHORTEST_PATH_LENGTHS_I64,
    WEIGHTED_EDGELIST_I64_F64,
    WEIGHTED_GRAPH_I64_F64,
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


def _require_static_contract(
    claimed: ClaimSite,
    ctx: LoweringContext,
    *,
    target: str,
    rule_id: str,
    result_type: str,
    operand_types: tuple[str, ...],
) -> tuple[str, ...]:
    """Reject forged analysis metadata before emitting a traversal helper."""
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
        raise ValueError(f"rextio-networkx lowering contract mismatch for {target!r}")

    operands = tuple(ctx.operands)
    _require_operands(target, operands, len(operand_types))
    return operands


def _require_operands(target: str, operands: tuple[str, ...], count: int) -> None:
    if len(operands) != count:
        raise ValueError(
            f"rextio-networkx lowering for {target!r} requires exactly {count} "
            f"operands, got {len(operands)}"
        )


def try_lower(claimed: ClaimSite, ctx: LoweringContext) -> LoweredExpr | None:
    """Lower a recognized exact traversal call."""
    if claimed.target == GRAPH_TARGET:
        operands = _require_static_contract(
            claimed,
            ctx,
            target=GRAPH_TARGET,
            rule_id=GRAPH_RULE,
            result_type=GRAPH_I64,
            operand_types=(EDGELIST_I64,),
        )
        return LoweredExpr(
            rust=f"{GRAPH_FROM_EDGELIST}(&{operands[0]})",
            helpers=graph_constructor_helpers(),
        )
    if claimed.target == WEIGHTED_GRAPH_TARGET:
        operands = _require_static_contract(
            claimed,
            ctx,
            target=WEIGHTED_GRAPH_TARGET,
            rule_id=WEIGHTED_GRAPH_RULE,
            result_type=WEIGHTED_GRAPH_I64_F64,
            operand_types=(WEIGHTED_EDGELIST_I64_F64,),
        )
        return LoweredExpr(
            rust=f"{WEIGHTED_GRAPH_FROM_EDGELIST}(&{operands[0]})",
            helpers=weighted_graph_constructor_helpers(),
        )
    if claimed.target == BFS_TARGET:
        operands = _require_static_contract(
            claimed,
            ctx,
            target=BFS_TARGET,
            rule_id=BFS_RULE,
            result_type=BFS_EDGES_I64,
            operand_types=(GRAPH_I64, NODE_I64),
        )
        return LoweredExpr(
            rust=f"{BFS_EDGES}(py, &{operands[0]}, {operands[1]})?",
            helpers=bfs_helpers(),
        )
    if claimed.target == SHORTEST_PATH_LENGTHS_TARGET:
        operands = _require_static_contract(
            claimed,
            ctx,
            target=SHORTEST_PATH_LENGTHS_TARGET,
            rule_id=SHORTEST_PATH_LENGTHS_RULE,
            result_type=SHORTEST_PATH_LENGTHS_I64,
            operand_types=(GRAPH_I64, NODE_I64),
        )
        return LoweredExpr(
            rust=f"{SHORTEST_PATH_LENGTHS}(py, &{operands[0]}, {operands[1]})?",
            helpers=shortest_path_lengths_helpers(),
        )
    if claimed.target == DIJKSTRA_TARGET:
        operands = _require_static_contract(
            claimed,
            ctx,
            target=DIJKSTRA_TARGET,
            rule_id=DIJKSTRA_RULE,
            result_type=DIJKSTRA_LENGTHS_I64,
            operand_types=(WEIGHTED_GRAPH_I64_F64, NODE_I64),
        )
        return LoweredExpr(
            rust=f"{DIJKSTRA_LENGTHS}(py, &{operands[0]}, {operands[1]})?",
            helpers=dijkstra_helpers(),
        )
    return None


__all__ = ["try_lower"]
