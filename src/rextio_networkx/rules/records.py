"""Rule records for the API-1.3 NetworkX public alpha surface."""

from __future__ import annotations

from rextio.plugins.api import RuleRecord, RuleScope


def _native(
    rule_id: str,
    pattern: str,
    constraint: str,
    code: str,
    guidance: str,
) -> RuleRecord:
    return RuleRecord(
        id=rule_id,
        provider="rextio-networkx",
        scope=RuleScope(kind="call", pattern=pattern),
        constraint=constraint,
        outcome="native",
        diagnostic_code=code,
        guidance=guidance,
        stability="experimental",
        verified=True,
    )


_RULES = (
    _native(
        "rextio-networkx/connected-components-edgelist",
        "connected_components_from_edgelist(EdgeListI64)",
        "Exact NetworkX 3.5 edge-only connected-components value semantics on signed i64 nodes.",
        "RXTP-NETWORKX-001",
        "Use the typed EdgeListI64 adapter.",
    ),
    _native(
        "rextio-networkx/graph-from-edgelist",
        "graph_from_edgelist(EdgeListI64)",
        "Validates an exact raw edge list and builds an opaque resident petgraph UnGraph once, preserving NetworkX node, edge, and adjacency insertion order.",
        "RXTP-NETWORKX-002",
        "Feed the resident result directly to bfs_edges inside one generated function.",
    ),
    _native(
        "rextio-networkx/bfs-edges",
        "bfs_edges(GraphI64, NodeI64)",
        "Custom ordered BFS over the resident petgraph matches list(nx.bfs_edges(G, source)) including exact list/tuple order and missing-source behavior.",
        "RXTP-NETWORKX-003",
        "Use GraphI64 and NodeI64 annotations with no options or keywords.",
    ),
    _native(
        "rextio-networkx/weighted-graph-from-edgelist",
        "weighted_graph_from_edgelist(WeightedEdgeListI64F64)",
        "Validates every exact weighted occurrence before deduplication and builds a resident petgraph UnGraph with first-adjacency-order and last-weight-wins semantics.",
        "RXTP-NETWORKX-004",
        "Feed the resident result directly to dijkstra_path_lengths.",
    ),
    _native(
        "rextio-networkx/dijkstra-path-lengths",
        "dijkstra_path_lengths(WeightedGraphI64F64, NodeI64)",
        "Ordered Dijkstra matches nx.single_source_dijkstra_path_length(G, source, weight='weight'): finalize-order dict insertion, discovery-counter ties, int source distance, float reached distances, stale heaps, and finite-input cumulative infinity.",
        "RXTP-NETWORKX-005",
        "Use the exact weighted resident chain with finite non-negative float weights.",
    ),
    RuleRecord(
        id="rextio-networkx/unsupported-argument-type",
        provider="rextio-networkx",
        scope=RuleScope(kind="call", pattern="legacy connected-components adapter type miss"),
        constraint="The WP-1 adapter requires one resolved EdgeListI64 argument.",
        outcome="fallback",
        diagnostic_code="RXTP-NETWORKX-010",
        guidance="Annotate the edge list as EdgeListI64.",
        stability="experimental",
    ),
    RuleRecord(
        id="rextio-networkx/unsupported-node-representation",
        provider="rextio-networkx",
        scope=RuleScope(kind="type", pattern="non-exact or non-i64 node labels"),
        constraint="Nodes are exact Python ints in the signed-i64 range; bool, subclasses, objects, and arbitrary precision overflow fail closed.",
        outcome="fallback",
        diagnostic_code="RXTP-NETWORKX-011",
        guidance="Relabel nodes as exact signed-i64 Python ints.",
        stability="experimental",
    ),
    RuleRecord(
        id="rextio-networkx/unsupported-api",
        provider="rextio-networkx",
        scope=RuleScope(kind="call", pattern="NetworkX APIs outside the explicit adapters"),
        constraint="Directed/multigraph/object-label calls, dynamic options, depth/target/cutoff forms, and other NetworkX APIs are not claimed.",
        outcome="fallback",
        diagnostic_code="RXTP-NETWORKX-019",
        guidance="Keep unsupported NetworkX calls on the Python fallback.",
        stability="experimental",
    ),
    RuleRecord(
        id="rextio-networkx/traversal-static-contract",
        provider="rextio-networkx",
        scope=RuleScope(
            kind="call", pattern="recognized traversal adapter with a static contract miss"
        ),
        constraint="Wrong arity, any keyword/options, plain core int, unresolved or wrong plugin annotations, and cross-resident-type calls are rejected rather than guessed.",
        outcome="fallback",
        diagnostic_code="RXTP-NETWORKX-020",
        guidance="Use the exact positional Graph/WeightedGraph, edge-list, NodeI64, and result annotations.",
        stability="experimental",
    ),
)

_ORDERED = tuple(sorted(_RULES, key=lambda record: record.id))


def networkx_rule_records() -> tuple[RuleRecord, ...]:
    """Return stable rule records ordered by id."""
    return _ORDERED
