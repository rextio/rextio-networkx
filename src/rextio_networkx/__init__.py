"""Exact NetworkX 3.5 adapters for rextio-networkx (public alpha).

The public Python functions are the forced-fallback half of the contract.  The
plugin lowers the same calls to generated Rust.  Validation is deliberately
narrow and happens before NetworkX sees the values so native and fallback mode
have the same dynamic contract and error precedence.
"""

from __future__ import annotations

import math
from typing import Any, TypeAlias

from rextio_networkx.__about__ import __version__
from rextio_networkx.plugin import RextioNetworkxPlugin, plugin

I64_MIN = -(2**63)
I64_MAX = 2**63 - 1

# Materialized boundary types.
NodeI64: TypeAlias = int
EdgeListI64: TypeAlias = list[tuple[int, int]]
WeightedEdgeListI64F64: TypeAlias = list[tuple[int, int, float]]
ComponentList: TypeAlias = list[set[int]]
BfsEdgesI64: TypeAlias = list[tuple[int, int]]
DijkstraLengthsI64: TypeAlias = dict[int, int | float]
ShortestPathLengthsI64: TypeAlias = dict[int, int]

# Resident annotations.  Their runtime value in fallback mode is an exact
# ``networkx.Graph``; their native value is an opaque petgraph-owned structure.
# ``Any`` keeps import cheap and avoids importing NetworkX merely for typing.
GraphI64: TypeAlias = Any
WeightedGraphI64F64: TypeAlias = Any


def _validate_node(value: object, where: str) -> int:
    """Return an exact signed-i64 Python int or raise the stable contract error."""
    if type(value) is not int:
        raise TypeError(f"rextio-networkx: {where} must be an exact int")
    if value < I64_MIN or value > I64_MAX:
        raise OverflowError(f"rextio-networkx: {where} is outside signed-i64 range")
    return value


def _validate_unweighted_edges(edges: object) -> EdgeListI64:
    """Validate an exact list of exact 2-tuples, strictly left-to-right."""
    if type(edges) is not list:
        raise TypeError("rextio-networkx: edges must be an exact list")
    validated: EdgeListI64 = []
    for index, edge in enumerate(edges):
        if type(edge) is not tuple:
            raise TypeError(f"rextio-networkx: edges[{index}] must be an exact tuple")
        if len(edge) != 2:
            raise TypeError(f"rextio-networkx: edges[{index}] must contain exactly 2 items")
        u = _validate_node(edge[0], f"edges[{index}][0]")
        v = _validate_node(edge[1], f"edges[{index}][1]")
        validated.append((u, v))
    return validated


def _validate_weighted_edges(edges: object) -> WeightedEdgeListI64F64:
    """Validate exact weighted tuples before any duplicate is deduplicated."""
    if type(edges) is not list:
        raise TypeError("rextio-networkx: edges must be an exact list")
    validated: WeightedEdgeListI64F64 = []
    for index, edge in enumerate(edges):
        if type(edge) is not tuple:
            raise TypeError(f"rextio-networkx: edges[{index}] must be an exact tuple")
        if len(edge) != 3:
            raise TypeError(f"rextio-networkx: edges[{index}] must contain exactly 3 items")
        u = _validate_node(edge[0], f"edges[{index}][0]")
        v = _validate_node(edge[1], f"edges[{index}][1]")
        weight = edge[2]
        if type(weight) is not float:
            raise TypeError(f"rextio-networkx: edges[{index}][2] must be an exact float")
        if not math.isfinite(weight) or weight < 0.0:
            raise ValueError(
                f"rextio-networkx: edges[{index}][2] must be a finite non-negative float"
            )
        validated.append((u, v, weight))
    return validated


def connected_components_from_edgelist(edges: EdgeListI64) -> ComponentList:
    """Return ``list(nx.connected_components(nx.from_edgelist(edges)))`` exactly."""
    import networkx as nx

    checked = _validate_unweighted_edges(edges)
    return list(nx.connected_components(nx.from_edgelist(checked)))


def graph_from_edgelist(edges: EdgeListI64) -> GraphI64:
    """Build the exact unweighted fallback graph used by the resident route."""
    import networkx as nx

    checked = _validate_unweighted_edges(edges)
    graph = nx.Graph()
    graph.add_edges_from(checked)
    graph.graph["__rextio_networkx_graph_i64__"] = True
    return graph


def connected_components(graph: GraphI64) -> ComponentList:
    """Return ``list(nx.connected_components(graph))`` for a resident graph."""
    import networkx as nx

    if type(graph) is not nx.Graph or not graph.graph.get("__rextio_networkx_graph_i64__", False):
        raise TypeError("rextio-networkx: graph must be produced by graph_from_edgelist")
    return list(nx.connected_components(graph))


def number_of_nodes(graph: GraphI64) -> int:
    """Return the exact number of nodes in a resident unweighted graph."""
    import networkx as nx

    if type(graph) is not nx.Graph or not graph.graph.get("__rextio_networkx_graph_i64__", False):
        raise TypeError("rextio-networkx: graph must be produced by graph_from_edgelist")
    return graph.number_of_nodes()


def number_of_edges(graph: GraphI64) -> int:
    """Return the exact number of edges in a resident unweighted graph."""
    import networkx as nx

    if type(graph) is not nx.Graph or not graph.graph.get("__rextio_networkx_graph_i64__", False):
        raise TypeError("rextio-networkx: graph must be produced by graph_from_edgelist")
    return graph.number_of_edges()


def number_connected_components(graph: GraphI64) -> int:
    """Return the exact NetworkX 3.5 connected-component count."""
    import networkx as nx

    if type(graph) is not nx.Graph or not graph.graph.get("__rextio_networkx_graph_i64__", False):
        raise TypeError("rextio-networkx: graph must be produced by graph_from_edgelist")
    return nx.number_connected_components(graph)


def is_connected(graph: GraphI64) -> bool:
    """Return the exact NetworkX 3.5 connectivity predicate."""
    import networkx as nx

    if type(graph) is not nx.Graph or not graph.graph.get("__rextio_networkx_graph_i64__", False):
        raise TypeError("rextio-networkx: graph must be produced by graph_from_edgelist")
    return nx.is_connected(graph)


def weighted_graph_from_edgelist(edges: WeightedEdgeListI64F64) -> WeightedGraphI64F64:
    """Build the exact weighted fallback graph used by the resident route."""
    import networkx as nx

    checked = _validate_weighted_edges(edges)
    graph = nx.Graph()
    graph.add_weighted_edges_from(checked)
    graph.graph["__rextio_networkx_weighted_graph_i64_f64__"] = True
    return graph


def bfs_edges(graph: GraphI64, source: NodeI64) -> BfsEdgesI64:
    """Return ``list(nx.bfs_edges(graph, source))`` with exact NetworkX order."""
    import networkx as nx

    if type(graph) is not nx.Graph or not graph.graph.get("__rextio_networkx_graph_i64__", False):
        raise TypeError("rextio-networkx: graph must be produced by graph_from_edgelist")
    checked_source = _validate_node(source, "source")
    if checked_source not in graph:
        raise nx.NetworkXError(f"The node {checked_source} is not in the graph.")
    return list(nx.bfs_edges(graph, checked_source))


def single_source_shortest_path_lengths(
    graph: GraphI64,
    source: NodeI64,
) -> ShortestPathLengthsI64:
    """Return ``nx.single_source_shortest_path_length(graph, source)`` exactly."""
    import networkx as nx

    if type(graph) is not nx.Graph or not graph.graph.get("__rextio_networkx_graph_i64__", False):
        raise TypeError("rextio-networkx: graph must be produced by graph_from_edgelist")
    checked_source = _validate_node(source, "source")
    return nx.single_source_shortest_path_length(graph, checked_source)


def has_path(graph: GraphI64, source: NodeI64, target: NodeI64) -> bool:
    """Return NetworkX 3.5 ``has_path`` for one resident unweighted graph."""
    import networkx as nx

    if type(graph) is not nx.Graph or not graph.graph.get("__rextio_networkx_graph_i64__", False):
        raise TypeError("rextio-networkx: graph must be produced by graph_from_edgelist")
    checked_source = _validate_node(source, "source")
    checked_target = _validate_node(target, "target")
    return nx.has_path(graph, checked_source, checked_target)


def shortest_path_length(
    graph: GraphI64,
    source: NodeI64,
    target: NodeI64,
) -> int:
    """Return the exact unweighted NetworkX 3.5 source-target path length."""
    import networkx as nx

    if type(graph) is not nx.Graph or not graph.graph.get("__rextio_networkx_graph_i64__", False):
        raise TypeError("rextio-networkx: graph must be produced by graph_from_edgelist")
    checked_source = _validate_node(source, "source")
    checked_target = _validate_node(target, "target")
    return nx.shortest_path_length(graph, checked_source, checked_target)


def dijkstra_path_lengths(
    graph: WeightedGraphI64F64,
    source: NodeI64,
) -> DijkstraLengthsI64:
    """Return NetworkX 3.5 single-source Dijkstra path lengths exactly."""
    import networkx as nx

    if type(graph) is not nx.Graph or not graph.graph.get(
        "__rextio_networkx_weighted_graph_i64_f64__", False
    ):
        raise TypeError("rextio-networkx: graph must be produced by weighted_graph_from_edgelist")
    checked_source = _validate_node(source, "source")
    if checked_source not in graph:
        raise nx.NodeNotFound(f"Node {checked_source} not found in graph")
    return nx.single_source_dijkstra_path_length(
        graph,
        checked_source,
        weight="weight",
    )


__all__ = [
    "BfsEdgesI64",
    "ComponentList",
    "DijkstraLengthsI64",
    "EdgeListI64",
    "GraphI64",
    "NodeI64",
    "RextioNetworkxPlugin",
    "ShortestPathLengthsI64",
    "WeightedEdgeListI64F64",
    "WeightedGraphI64F64",
    "__version__",
    "bfs_edges",
    "connected_components",
    "connected_components_from_edgelist",
    "dijkstra_path_lengths",
    "graph_from_edgelist",
    "has_path",
    "is_connected",
    "number_connected_components",
    "number_of_edges",
    "number_of_nodes",
    "plugin",
    "shortest_path_length",
    "single_source_shortest_path_lengths",
    "weighted_graph_from_edgelist",
]
