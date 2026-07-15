"""Fail-closed claims for the two exact resident traversal chains."""

from __future__ import annotations

from rextio.plugins.api import Claimed, ClaimResult, ClaimSite

from rextio_networkx.diagnostics import (
    BFS_EDGES_I64,
    DIJKSTRA_LENGTHS_I64,
    EDGELIST_I64,
    GRAPH_I64,
    NODE_I64,
    WEIGHTED_EDGELIST_I64_F64,
    WEIGHTED_GRAPH_I64_F64,
    reject_site,
)

GRAPH_TARGET = "rextio_networkx.graph_from_edgelist"
BFS_TARGET = "rextio_networkx.bfs_edges"
WEIGHTED_GRAPH_TARGET = "rextio_networkx.weighted_graph_from_edgelist"
DIJKSTRA_TARGET = "rextio_networkx.dijkstra_path_lengths"

GRAPH_RULE = "rextio-networkx/graph-from-edgelist"
BFS_RULE = "rextio-networkx/bfs-edges"
WEIGHTED_GRAPH_RULE = "rextio-networkx/weighted-graph-from-edgelist"
DIJKSTRA_RULE = "rextio-networkx/dijkstra-path-lengths"

_TARGETS = frozenset({GRAPH_TARGET, BFS_TARGET, WEIGHTED_GRAPH_TARGET, DIJKSTRA_TARGET})


def try_claim(site: ClaimSite) -> ClaimResult | None:
    """Claim an exact traversal call or reject every recognized miss."""
    if site.kind != "call" or site.target not in _TARGETS:
        return None
    expected: tuple[str, ...]
    rule: str
    result_type: str
    if site.target == GRAPH_TARGET:
        expected = (EDGELIST_I64,)
        rule = GRAPH_RULE
        result_type = GRAPH_I64
        spelling = "graph_from_edgelist(EdgeListI64)"
    elif site.target == BFS_TARGET:
        expected = (GRAPH_I64, NODE_I64)
        rule = BFS_RULE
        result_type = BFS_EDGES_I64
        spelling = "bfs_edges(GraphI64, NodeI64)"
    elif site.target == WEIGHTED_GRAPH_TARGET:
        expected = (WEIGHTED_EDGELIST_I64_F64,)
        rule = WEIGHTED_GRAPH_RULE
        result_type = WEIGHTED_GRAPH_I64_F64
        spelling = "weighted_graph_from_edgelist(WeightedEdgeListI64F64)"
    else:
        expected = (WEIGHTED_GRAPH_I64_F64, NODE_I64)
        rule = DIJKSTRA_RULE
        result_type = DIJKSTRA_LENGTHS_I64
        spelling = "dijkstra_path_lengths(WeightedGraphI64F64, NodeI64)"

    if site.keywords or tuple(site.operand_types) != expected:
        return reject_site(site, expected=f"the positional shape {spelling}")
    return Claimed(rule_id=rule, result_type=result_type)


__all__ = [
    "BFS_RULE",
    "BFS_TARGET",
    "DIJKSTRA_RULE",
    "DIJKSTRA_TARGET",
    "GRAPH_RULE",
    "GRAPH_TARGET",
    "WEIGHTED_GRAPH_RULE",
    "WEIGHTED_GRAPH_TARGET",
    "try_claim",
]
