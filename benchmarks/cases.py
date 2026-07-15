"""Deterministic product-route benchmark case generation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

Algorithm = Literal["components", "bfs", "dijkstra"]
Family = Literal["connected", "disconnected", "low-reach"]


@dataclass(frozen=True)
class BenchmarkCase:
    """One identical native/fallback input cell."""

    case_id: str
    algorithm: Algorithm
    family: Family
    requested_nodes: int
    edges: list[tuple[int, int]] | list[tuple[int, int, float]]
    source: int | None
    raw_node_occurrences: int
    raw_edges: int
    effective_nodes: int
    effective_edges: int
    reachable_nodes: int

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready representation."""
        return asdict(self)


def _segments(size: int, family: Family) -> list[tuple[int, int]]:
    if family == "connected":
        return [(0, size)]
    if family == "low-reach":
        return [(0, 2), (2, size)]
    quarter = size // 4
    boundaries = [0, quarter, quarter * 2, quarter * 3, size]
    return list(zip(boundaries[:-1], boundaries[1:], strict=True))


def _unweighted_edges(size: int, family: Family) -> list[tuple[int, int]]:
    edges: list[tuple[int, int]] = []
    for start, stop in _segments(size, family):
        edges.extend((node, node + 1) for node in range(start, stop - 1))
    # Deterministic reversed duplicates exercise the product's deduplication
    # cost without changing the effective graph or adjacency order.
    if edges:
        stride = max(1, len(edges) // 16)
        edges.extend((v, u) for u, v in edges[::stride])
    return edges


def _weighted_edges(size: int, family: Family) -> list[tuple[int, int, float]]:
    base = _unweighted_edges(size, family)
    weighted = [(u, v, 1.0 + ((u * 17 + v * 13) % 11) * 0.125) for u, v in base]
    # Last duplicate replaces the weight, exactly as NetworkX Graph does.
    if weighted:
        u, v, weight = weighted[len(weighted) // 3]
        weighted.append((v, u, weight + 0.25))
    return weighted


def _effective_counts(
    edges: list[tuple[int, int]] | list[tuple[int, int, float]],
) -> tuple[int, int]:
    nodes: set[int] = set()
    undirected: set[tuple[int, int]] = set()
    for edge in edges:
        u, v = edge[0], edge[1]
        nodes.update((u, v))
        undirected.add((u, v) if u <= v else (v, u))
    return len(nodes), len(undirected)


def make_case(algorithm: Algorithm, family: Family, size: int) -> BenchmarkCase:
    """Create one reproducible cell with explicit raw/effective counts."""
    if size < 4:
        raise ValueError("benchmark size must be at least four")
    edges = (
        _weighted_edges(size, family)
        if algorithm == "dijkstra"
        else _unweighted_edges(size, family)
    )
    effective_nodes, effective_edges = _effective_counts(edges)
    source = None if algorithm == "components" else 0
    if algorithm == "components" or family == "connected":
        reachable = effective_nodes
    elif family == "low-reach":
        reachable = 2
    else:
        reachable = size // 4
    return BenchmarkCase(
        case_id=f"{algorithm}-{family}-n{size}",
        algorithm=algorithm,
        family=family,
        requested_nodes=size,
        edges=edges,
        source=source,
        raw_node_occurrences=len(edges) * 2,
        raw_edges=len(edges),
        effective_nodes=effective_nodes,
        effective_edges=effective_edges,
        reachable_nodes=reachable,
    )


def benchmark_cases(sizes: tuple[int, ...]) -> list[BenchmarkCase]:
    """Return connected/disconnected/low-reach cells for all product routes."""
    cases: list[BenchmarkCase] = []
    for size in sizes:
        for family in ("connected", "disconnected"):
            cases.append(make_case("components", family, size))
        for algorithm in ("bfs", "dijkstra"):
            for family in ("connected", "disconnected", "low-reach"):
                cases.append(make_case(algorithm, family, size))
    return cases


__all__ = ["BenchmarkCase", "benchmark_cases", "make_case"]
