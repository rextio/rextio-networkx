"""Unit/differential/claim/lowering coverage for exact traversal routes."""

from __future__ import annotations

import math
from copy import deepcopy
from dataclasses import replace

import networkx as nx
import pytest

import rextio_networkx as rn
from rextio.plugins.api import (
    Claimed,
    ClaimSite,
    KeywordArg,
    LoweringContext,
    NotCovered,
    ReceiverMeta,
    Rejected,
)
from rextio_networkx.claim import claim
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
from rextio_networkx.lower import lower


def bfs_product(edges: rn.EdgeListI64, source: rn.NodeI64) -> rn.BfsEdgesI64:
    """Fallback spelling identical to the generated resident chain."""
    return rn.bfs_edges(rn.graph_from_edgelist(edges), source)


def dijkstra_product(
    edges: rn.WeightedEdgeListI64F64,
    source: rn.NodeI64,
) -> rn.DijkstraLengthsI64:
    """Fallback spelling identical to the generated resident chain."""
    return rn.dijkstra_path_lengths(rn.weighted_graph_from_edgelist(edges), source)


def reference_bfs(edges: list[tuple[int, int]], source: int) -> list[tuple[int, int]]:
    graph = nx.Graph()
    graph.add_edges_from(edges)
    return list(nx.bfs_edges(graph, source))


def reference_dijkstra(edges: list[tuple[int, int, float]], source: int) -> dict[int, int | float]:
    graph = nx.Graph()
    graph.add_weighted_edges_from(edges)
    return nx.single_source_dijkstra_path_length(graph, source, weight="weight")


BFS_CASES = {
    "star-order": ([(0, 4), (0, 2), (0, 9), (0, 1)], 0),
    "diamond-order": ([(0, 2), (0, 1), (2, 3), (1, 3)], 0),
    "reversed-duplicate": ([(4, 1), (2, 4), (1, 4), (4, 2), (2, 3)], 4),
    "self-loop": ([(7, 7), (7, 8), (8, 8), (8, 9)], 7),
    "disconnected-low-reach": ([(0, 1), (10, 11), (11, 12)], 10),
    "negative": ([(-5, -2), (-2, 9), (100, 101)], -5),
    "i64-bound": ([(2**63 - 1, -(2**63)), (0, 2**63 - 1)], 0),
}


@pytest.mark.parametrize("case", BFS_CASES.values(), ids=BFS_CASES)
def test_bfs_fallback_matches_exact_networkx(case: tuple[list[tuple[int, int]], int]) -> None:
    edges, source = case
    before = deepcopy(edges)
    actual = bfs_product(edges, source)
    assert actual == reference_bfs(edges, source)
    assert type(actual) is list
    assert all(type(edge) is tuple and all(type(node) is int for node in edge) for edge in actual)
    assert edges == before


DIJKSTRA_CASES = {
    "basic": ([(0, 1, 1.5), (1, 2, 2.25), (0, 2, 10.0)], 0),
    "last-reversed-duplicate-wins": (
        [(0, 1, 9.0), (1, 0, 3.0), (0, 1, 5.0), (1, 2, 1.0)],
        0,
    ),
    "equal-distance-counter-tie": (
        [(0, 2, 1.0), (0, 1, 1.0), (2, 3, 1.0), (1, 4, 1.0)],
        0,
    ),
    "stale-decrease": ([(0, 1, 10.0), (0, 2, 1.0), (2, 1, 1.0), (1, 3, 1.0)], 0),
    "zero-signed-zero": ([(0, 1, -0.0), (0, 2, 0.0), (1, 3, 0.0)], 0),
    "self-loop-disconnected": ([(5, 5, 0.0), (5, 6, 2.0), (20, 21, 1.0)], 5),
    "cumulative-infinity": ([(0, 1, 1.0e308), (1, 2, 1.0e308)], 0),
    "infinity-then-finite-decrease": (
        [
            (0, 1, 1.0e308),
            (1, 3, 1.0e308),
            (0, 2, 1.7e308),
            (2, 3, 0.0),
        ],
        0,
    ),
}


def _ordered_distance_signature(result: dict[int, int | float]) -> list[tuple[int, type, str]]:
    return [
        (key, type(value), value.hex() if type(value) is float else str(value))
        for key, value in result.items()
    ]


@pytest.mark.parametrize("case", DIJKSTRA_CASES.values(), ids=DIJKSTRA_CASES)
def test_dijkstra_fallback_matches_exact_networkx(
    case: tuple[list[tuple[int, int, float]], int],
) -> None:
    edges, source = case
    before = deepcopy(edges)
    actual = dijkstra_product(edges, source)
    expected = reference_dijkstra(edges, source)
    assert list(actual.items()) == list(expected.items())
    assert _ordered_distance_signature(actual) == _ordered_distance_signature(expected)
    assert type(next(iter(actual))) is int
    assert type(actual[source]) is int and actual[source] == 0
    assert all(type(value) is float for key, value in actual.items() if key != source)
    assert edges == before


def _exception_signature(callable_) -> tuple[type[BaseException], str, tuple[object, ...]]:
    with pytest.raises(BaseException) as caught:
        callable_()
    error = caught.value
    return type(error), str(error), error.args


@pytest.mark.parametrize(
    ("edges", "message"),
    [
        ((0, 1), "rextio-networkx: edges must be an exact list"),
        ([[0, 1]], "rextio-networkx: edges[0] must be an exact tuple"),
        ([(0,)], "rextio-networkx: edges[0] must contain exactly 2 items"),
        ([(0, 1, 2)], "rextio-networkx: edges[0] must contain exactly 2 items"),
        ([(True, 1)], "rextio-networkx: edges[0][0] must be an exact int"),
        ([(0, 2**63)], "rextio-networkx: edges[0][1] is outside signed-i64 range"),
    ],
)
def test_bfs_edge_contract_exact_errors(edges: object, message: str) -> None:
    signature = _exception_signature(lambda: bfs_product(edges, False))  # type: ignore[arg-type]
    expected_type = OverflowError if "outside" in message else TypeError
    assert signature == (expected_type, message, (message,))


@pytest.mark.parametrize(
    ("edges", "error_type", "message"),
    [
        (((0, 1, 1.0),), TypeError, "rextio-networkx: edges must be an exact list"),
        ([(0, 1, 1)], TypeError, "rextio-networkx: edges[0][2] must be an exact float"),
        ([(0, 1, True)], TypeError, "rextio-networkx: edges[0][2] must be an exact float"),
        (
            [(0, 1, -1.0)],
            ValueError,
            "rextio-networkx: edges[0][2] must be a finite non-negative float",
        ),
        (
            [(0, 1, math.nan)],
            ValueError,
            "rextio-networkx: edges[0][2] must be a finite non-negative float",
        ),
        (
            [(0, 1, math.inf)],
            ValueError,
            "rextio-networkx: edges[0][2] must be a finite non-negative float",
        ),
        (
            [(0, 1, -math.inf)],
            ValueError,
            "rextio-networkx: edges[0][2] must be a finite non-negative float",
        ),
    ],
)
def test_dijkstra_edge_contract_exact_errors(
    edges: object, error_type: type[BaseException], message: str
) -> None:
    assert _exception_signature(lambda: dijkstra_product(edges, False)) == (  # type: ignore[arg-type]
        error_type,
        message,
        (message,),
    )


class IntSubclass(int):
    """Deliberately rejected exact-type adversary."""


class FloatSubclass(float):
    """Deliberately rejected exact-type adversary."""


class TupleSubclass(tuple):
    """Deliberately rejected exact-type adversary."""


class ListSubclass(list):
    """Deliberately rejected exact-type adversary."""


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (
            lambda: bfs_product(ListSubclass([(0, 1)]), 0),
            "rextio-networkx: edges must be an exact list",
        ),
        (
            lambda: bfs_product([TupleSubclass((0, 1))], 0),
            "rextio-networkx: edges[0] must be an exact tuple",
        ),
        (
            lambda: bfs_product([(IntSubclass(0), 1)], 0),
            "rextio-networkx: edges[0][0] must be an exact int",
        ),
        (
            lambda: dijkstra_product([(0, 1, FloatSubclass(1.0))], 0),
            "rextio-networkx: edges[0][2] must be an exact float",
        ),
    ],
)
def test_exact_type_subclasses_are_rejected(call, message: str) -> None:
    assert _exception_signature(call) == (TypeError, message, (message,))


@pytest.mark.parametrize("source", [True, False, IntSubclass(0), 2**63, -(2**63) - 1])
def test_source_contract_is_exact_and_stable(source: object) -> None:
    bfs_signature = _exception_signature(lambda: bfs_product([(0, 1)], source))  # type: ignore[arg-type]
    dijkstra_signature = _exception_signature(
        lambda: dijkstra_product([(0, 1, 1.0)], source)  # type: ignore[arg-type]
    )
    error_type = (
        OverflowError if type(source) is int and not (-(2**63) <= source < 2**63) else TypeError
    )
    phrase = (
        "is outside signed-i64 range" if error_type is OverflowError else "must be an exact int"
    )
    message = f"rextio-networkx: source {phrase}"
    assert bfs_signature == dijkstra_signature == (error_type, message, (message,))


def test_missing_sources_match_networkx_exactly() -> None:
    bfs_sig = _exception_signature(lambda: bfs_product([], -9))
    assert bfs_sig == (
        nx.NetworkXError,
        "The node -9 is not in the graph.",
        ("The node -9 is not in the graph.",),
    )
    dijkstra_sig = _exception_signature(lambda: dijkstra_product([], -9))
    assert dijkstra_sig == (
        nx.NodeNotFound,
        "Node -9 not found in graph",
        ("Node -9 not found in graph",),
    )


@pytest.mark.parametrize("graph", [nx.Graph(), nx.DiGraph(), nx.MultiGraph(), object()])
def test_unproven_or_wrong_graph_objects_are_rejected(graph: object) -> None:
    message = "rextio-networkx: graph must be produced by graph_from_edgelist"
    assert _exception_signature(lambda: rn.bfs_edges(graph, 0)) == (  # type: ignore[arg-type]
        TypeError,
        message,
        (message,),
    )


def test_weighted_unproven_graph_is_rejected() -> None:
    message = "rextio-networkx: graph must be produced by weighted_graph_from_edgelist"
    assert _exception_signature(lambda: rn.dijkstra_path_lengths(nx.Graph(), 0)) == (
        TypeError,
        message,
        (message,),
    )


def test_complete_edges_precede_source_validation_and_invalid_duplicate_is_not_hidden() -> None:
    assert _exception_signature(lambda: bfs_product([(0, 1), (True, 1)], False))[1] == (
        "rextio-networkx: edges[1][0] must be an exact int"
    )
    assert (
        _exception_signature(lambda: dijkstra_product([(0, 1, 1.0), (1, 0, math.nan)], False))[1]
        == "rextio-networkx: edges[1][2] must be a finite non-negative float"
    )


def _site(target: str, operand_types: tuple[str | None, ...], keywords=()) -> ClaimSite:
    return ClaimSite(
        kind="call",
        target=target,
        operand_types=operand_types,
        file_path="app.py",
        line=4,
        column=8,
        keywords=tuple(keywords),
    )


@pytest.mark.parametrize(
    ("target", "types", "rule", "result"),
    [
        (GRAPH_TARGET, (EDGELIST_I64,), GRAPH_RULE, GRAPH_I64),
        (BFS_TARGET, (GRAPH_I64, NODE_I64), BFS_RULE, BFS_EDGES_I64),
        (
            SHORTEST_PATH_LENGTHS_TARGET,
            (GRAPH_I64, NODE_I64),
            SHORTEST_PATH_LENGTHS_RULE,
            SHORTEST_PATH_LENGTHS_I64,
        ),
        (
            WEIGHTED_GRAPH_TARGET,
            (WEIGHTED_EDGELIST_I64_F64,),
            WEIGHTED_GRAPH_RULE,
            WEIGHTED_GRAPH_I64_F64,
        ),
        (
            DIJKSTRA_TARGET,
            (WEIGHTED_GRAPH_I64_F64, NODE_I64),
            DIJKSTRA_RULE,
            DIJKSTRA_LENGTHS_I64,
        ),
    ],
)
def test_exact_static_traversal_shapes_are_claimed(target, types, rule, result) -> None:
    claimed = claim(_site(target, types), None)
    assert isinstance(claimed, Claimed)
    assert (claimed.rule_id, claimed.result_type) == (rule, result)


@pytest.mark.parametrize(
    ("target", "types", "keywords"),
    [
        (GRAPH_TARGET, (), ()),
        (GRAPH_TARGET, (None,), ()),
        (GRAPH_TARGET, ("list[tuple[int,int]]",), ()),
        (BFS_TARGET, (GRAPH_I64, "int"), ()),
        (BFS_TARGET, (GRAPH_I64,), ()),
        (BFS_TARGET, (GRAPH_I64, NODE_I64), (KeywordArg(name="depth_limit"),)),
        (SHORTEST_PATH_LENGTHS_TARGET, (GRAPH_I64, NODE_I64), (KeywordArg(name="cutoff"),)),
        (DIJKSTRA_TARGET, (WEIGHTED_GRAPH_I64_F64, None), ()),
        (DIJKSTRA_TARGET, (GRAPH_I64, NODE_I64), ()),
        (DIJKSTRA_TARGET, (WEIGHTED_GRAPH_I64_F64, NODE_I64), (KeywordArg(name="cutoff"),)),
    ],
)
def test_every_recognized_static_miss_is_plugin_rejected(target, types, keywords) -> None:
    result = claim(_site(target, types, keywords), None)
    assert isinstance(result, Rejected)
    assert result.diagnostic.code == "RXTP-NETWORKX-020"


def test_unrelated_target_is_not_covered() -> None:
    assert isinstance(claim(_site("networkx.bfs_edges", (GRAPH_I64, NODE_I64)), None), NotCovered)


def _claimed(target: str, types: tuple[str, ...], rule: str, result: str) -> ClaimSite:
    return ClaimSite(
        kind="call",
        target=target,
        operand_types=types,
        file_path="",
        line=0,
        column=0,
        rule_id=rule,
        result_type=result,
    )


def _ctx(*operands: str) -> LoweringContext:
    return LoweringContext(
        operands=operands,
        target_language="rust",
        fresh_name=lambda prefix: prefix,
    )


def test_lowering_builds_once_and_borrows_resident_consumers() -> None:
    constructor = lower(
        _claimed(GRAPH_TARGET, (EDGELIST_I64,), GRAPH_RULE, GRAPH_I64),
        _ctx("edges"),
    )
    bfs = lower(
        _claimed(BFS_TARGET, (GRAPH_I64, NODE_I64), BFS_RULE, BFS_EDGES_I64),
        _ctx("graph", "source"),
    )
    assert constructor.rust == "__rxtnx_graph_from_edgelist_i64(&edges)"
    assert bfs.rust == "__rxtnx_bfs_edges_i64(py, &graph, source)?"
    joined = "\n".join(constructor.helpers)
    assert "petgraph::graph::UnGraph<i64, ()>" in joined
    assert "adjacency_order" in joined
    assert "is_exact_instance_of::<pyo3::types::PyList>" in joined


def test_shortest_path_lengths_lowering_uses_ordered_bfs_helper() -> None:
    lowered = lower(
        _claimed(
            SHORTEST_PATH_LENGTHS_TARGET,
            (GRAPH_I64, NODE_I64),
            SHORTEST_PATH_LENGTHS_RULE,
            SHORTEST_PATH_LENGTHS_I64,
        ),
        _ctx("graph", "source"),
    )
    assert lowered.rust == "__rxtnx_single_source_shortest_path_lengths_i64(py, &graph, source)?"
    assert "result.set_item(graph.graph[source_node], 0_i64)" in "\n".join(lowered.helpers)


def test_dijkstra_lowering_is_ordered_partial_cmp_not_total_cmp() -> None:
    lowered = lower(
        _claimed(
            DIJKSTRA_TARGET,
            (WEIGHTED_GRAPH_I64_F64, NODE_I64),
            DIJKSTRA_RULE,
            DIJKSTRA_LENGTHS_I64,
        ),
        _ctx("graph", "source"),
    )
    assert lowered.rust == "__rxtnx_dijkstra_lengths_i64_f64(py, &graph, source)?"
    joined = "\n".join(lowered.helpers)
    assert "partial_cmp" in joined
    assert "total_cmp" not in joined
    assert "counter" in joined
    assert "edge_weight(edge)" in joined
    assert "result.set_item(label, 0_i64)" in joined


def test_lowering_operand_guards_survive_without_asserts() -> None:
    site = _claimed(BFS_TARGET, (GRAPH_I64, NODE_I64), BFS_RULE, BFS_EDGES_I64)
    with pytest.raises(ValueError, match="requires exactly 2 operands"):
        lower(site, _ctx("graph"))


@pytest.mark.parametrize(
    ("target", "types", "rule", "result", "operands"),
    [
        (GRAPH_TARGET, (EDGELIST_I64,), GRAPH_RULE, GRAPH_I64, ("edges",)),
        (BFS_TARGET, (GRAPH_I64, NODE_I64), BFS_RULE, BFS_EDGES_I64, ("graph", "source")),
        (
            SHORTEST_PATH_LENGTHS_TARGET,
            (GRAPH_I64, NODE_I64),
            SHORTEST_PATH_LENGTHS_RULE,
            SHORTEST_PATH_LENGTHS_I64,
            ("graph", "source"),
        ),
        (
            WEIGHTED_GRAPH_TARGET,
            (WEIGHTED_EDGELIST_I64_F64,),
            WEIGHTED_GRAPH_RULE,
            WEIGHTED_GRAPH_I64_F64,
            ("edges",),
        ),
        (
            DIJKSTRA_TARGET,
            (WEIGHTED_GRAPH_I64_F64, NODE_I64),
            DIJKSTRA_RULE,
            DIJKSTRA_LENGTHS_I64,
            ("graph", "source"),
        ),
    ],
)
@pytest.mark.parametrize(
    "forged",
    [
        lambda site: replace(site, kind="binop"),
        lambda site: replace(site, rule_id="rextio-networkx/forged"),
        lambda site: replace(site, result_type="rextio-networkx/forged"),
        lambda site: replace(site, operand_types=("rextio-networkx/forged",)),
        lambda site: replace(site, keywords=(KeywordArg(name="cutoff"),)),
        lambda site: replace(
            site,
            receiver=ReceiverMeta(arg_type="object", expr_kind="name", is_safe=True),
        ),
    ],
    ids=["kind", "rule", "result", "operand-types", "keywords", "receiver"],
)
def test_traversal_lowering_rejects_forged_claim_metadata(
    target: str,
    types: tuple[str, ...],
    rule: str,
    result: str,
    operands: tuple[str, ...],
    forged,
) -> None:
    with pytest.raises(ValueError, match="lowering contract mismatch"):
        lower(forged(_claimed(target, types, rule, result)), _ctx(*operands))


@pytest.mark.parametrize(
    ("target", "types", "rule", "result", "operands"),
    [
        (BFS_TARGET, (GRAPH_I64, NODE_I64), BFS_RULE, BFS_EDGES_I64, ("graph", "source")),
        (
            SHORTEST_PATH_LENGTHS_TARGET,
            (GRAPH_I64, NODE_I64),
            SHORTEST_PATH_LENGTHS_RULE,
            SHORTEST_PATH_LENGTHS_I64,
            ("graph", "source"),
        ),
        (
            DIJKSTRA_TARGET,
            (WEIGHTED_GRAPH_I64_F64, NODE_I64),
            DIJKSTRA_RULE,
            DIJKSTRA_LENGTHS_I64,
            ("graph", "source"),
        ),
    ],
)
def test_traversal_lowering_rejects_forged_context_receiver(
    target: str,
    types: tuple[str, ...],
    rule: str,
    result: str,
    operands: tuple[str, ...],
) -> None:
    with pytest.raises(ValueError, match="lowering contract mismatch"):
        lower(
            _claimed(target, types, rule, result),
            replace(_ctx(*operands), receiver="forged_receiver"),
        )
