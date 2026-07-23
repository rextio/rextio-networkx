"""Exact fallback, claim, and lowering coverage for shortest-path lengths."""

from __future__ import annotations

from copy import deepcopy

import networkx as nx
import pytest
from rextio.plugins.api import Claimed, ClaimSite, KeywordArg, LoweringContext, Rejected

import rextio_networkx as rn
from rextio_networkx.claim import claim
from rextio_networkx.claim.traversal import SHORTEST_PATH_LENGTHS_RULE, SHORTEST_PATH_LENGTHS_TARGET
from rextio_networkx.diagnostics import GRAPH_I64, NODE_I64, SHORTEST_PATH_LENGTHS_I64
from rextio_networkx.lower import lower


def _reference(edges: list[tuple[int, int]], source: int) -> dict[int, int]:
    graph = nx.Graph()
    graph.add_edges_from(edges)
    return nx.single_source_shortest_path_length(graph, source)


CASES = {
    "source-first-diamond-tie-order": ([(0, 2), (0, 1), (2, 3), (1, 3)], 0),
    "duplicate-and-reversed-edges": ([(4, 1), (2, 4), (1, 4), (4, 2), (2, 3)], 4),
    "self-loop": ([(7, 7), (7, 8), (8, 8), (8, 9)], 7),
    "disconnected": ([(0, 1), (1, 2), (10, 11)], 0),
    "non-contiguous-i64-labels": ([(-(2**63), 17), (17, 2**63 - 1), (900, 901)], -(2**63)),
}


@pytest.mark.parametrize("edges,source", CASES.values(), ids=CASES)
def test_fallback_matches_single_source_shortest_path_length_exactly(
    edges: list[tuple[int, int]], source: int
) -> None:
    before = deepcopy(edges)
    graph = rn.graph_from_edgelist(edges)
    graph_before = (list(graph.nodes), list(graph.edges), dict(graph.graph))

    actual = rn.single_source_shortest_path_lengths(graph, source)
    expected = _reference(edges, source)

    assert type(actual) is dict
    assert list(actual.items()) == list(expected.items())
    assert list(actual.items())[0] == (source, 0)
    assert all(type(node) is int and type(distance) is int for node, distance in actual.items())
    assert edges == before
    assert (list(graph.nodes), list(graph.edges), dict(graph.graph)) == graph_before


def test_missing_source_is_exact_networkx_node_not_found() -> None:
    graph = rn.graph_from_edgelist([(0, 1)])
    with pytest.raises(nx.NodeNotFound) as caught:
        rn.single_source_shortest_path_lengths(graph, -9)
    assert (str(caught.value), caught.value.args) == (
        "Node -9 not found in graph",
        ("Node -9 not found in graph",),
    )


def _site(types: tuple[str | None, ...], keywords=()) -> ClaimSite:
    return ClaimSite(
        kind="call",
        target=SHORTEST_PATH_LENGTHS_TARGET,
        operand_types=types,
        file_path="app.py",
        line=4,
        column=8,
        keywords=tuple(keywords),
    )


def test_exact_static_shape_is_claimed() -> None:
    result = claim(_site((GRAPH_I64, NODE_I64)), None)
    assert isinstance(result, Claimed)
    assert (result.rule_id, result.result_type) == (
        SHORTEST_PATH_LENGTHS_RULE,
        SHORTEST_PATH_LENGTHS_I64,
    )


@pytest.mark.parametrize(
    ("types", "keywords"),
    [
        ((GRAPH_I64,), ()),
        ((GRAPH_I64, "int"), ()),
        ((GRAPH_I64, NODE_I64), (KeywordArg(name="cutoff"),)),
        ((None, NODE_I64), ()),
    ],
)
def test_static_misses_are_rejected_not_guessed(types, keywords) -> None:
    result = claim(_site(types, keywords), None)
    assert isinstance(result, Rejected)
    assert result.diagnostic.code == "RXTP-NETWORKX-020"


def test_lowering_borrows_the_unweighted_resident_graph() -> None:
    site = ClaimSite(
        kind="call",
        target=SHORTEST_PATH_LENGTHS_TARGET,
        operand_types=(GRAPH_I64, NODE_I64),
        file_path="",
        line=0,
        column=0,
        rule_id=SHORTEST_PATH_LENGTHS_RULE,
        result_type=SHORTEST_PATH_LENGTHS_I64,
    )
    lowered = lower(
        site,
        LoweringContext(operands=("graph", "source"), target_language="rust", fresh_name=str),
    )
    assert lowered.rust == "__rxtnx_single_source_shortest_path_lengths_i64(py, &graph, source)?"
    assert "adjacency_order" in "\n".join(lowered.helpers)
