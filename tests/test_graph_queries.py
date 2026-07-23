"""Exact resident scalar graph-query fallback, claim, and lowering coverage."""

from __future__ import annotations

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
    ReceiverMeta,
    Rejected,
)
from rextio_networkx.claim import claim
from rextio_networkx.claim.traversal import (
    NUMBER_OF_EDGES_RULE,
    NUMBER_OF_EDGES_TARGET,
    NUMBER_OF_NODES_RULE,
    NUMBER_OF_NODES_TARGET,
)
from rextio_networkx.diagnostics import GRAPH_I64
from rextio_networkx.lower import lower


@pytest.mark.parametrize(
    ("edges", "expected_nodes", "expected_edges"),
    [
        ([], 0, 0),
        ([(0, 1)], 2, 1),
        ([(4, 1), (1, 4), (4, 4)], 2, 2),
        ([(-(2**63), 2**63 - 1), (0, 0), (10, 11)], 5, 3),
    ],
)
def test_fallback_counts_match_networkx_exactly(
    edges: list[tuple[int, int]],
    expected_nodes: int,
    expected_edges: int,
) -> None:
    before = deepcopy(edges)
    graph = rn.graph_from_edgelist(edges)
    graph_before = (list(graph.nodes), list(graph.edges), dict(graph.graph))

    nodes = rn.number_of_nodes(graph)
    edge_count = rn.number_of_edges(graph)

    assert type(nodes) is int and nodes == expected_nodes == graph.number_of_nodes()
    assert type(edge_count) is int and edge_count == expected_edges == graph.number_of_edges()
    assert edges == before
    assert (list(graph.nodes), list(graph.edges), dict(graph.graph)) == graph_before


@pytest.mark.parametrize("query", [rn.number_of_nodes, rn.number_of_edges])
def test_fallback_rejects_nonresident_graph(query) -> None:
    with pytest.raises(
        TypeError,
        match="graph must be produced by graph_from_edgelist",
    ):
        query(nx.Graph([(0, 1)]))


QUERY_CASES = (
    (
        NUMBER_OF_NODES_TARGET,
        NUMBER_OF_NODES_RULE,
        "__rxtnx_number_of_nodes_i64(&graph)?",
        "node count is outside signed-i64 range",
    ),
    (
        NUMBER_OF_EDGES_TARGET,
        NUMBER_OF_EDGES_RULE,
        "__rxtnx_number_of_edges_i64(&graph)?",
        "edge count is outside signed-i64 range",
    ),
)


def _site(
    target: str,
    operand_types: tuple[str | None, ...] = (GRAPH_I64,),
    *,
    kind: str = "call",
    keywords: tuple[KeywordArg, ...] = (),
    rule_id: str | None = None,
    result_type: str | None = None,
) -> ClaimSite:
    return ClaimSite(
        kind=kind,
        target=target,
        operand_types=operand_types,
        file_path="app.py",
        line=4,
        column=8,
        keywords=keywords,
        rule_id=rule_id,
        result_type=result_type,
    )


def _claimed(target: str, rule: str) -> ClaimSite:
    return replace(_site(target), rule_id=rule, result_type="int")


def _ctx(*operands: str) -> LoweringContext:
    return LoweringContext(operands=operands, target_language="rust", fresh_name=str)


@pytest.mark.parametrize(("target", "rule", "_rust", "_overflow"), QUERY_CASES)
def test_exact_static_shapes_are_claimed(
    target: str,
    rule: str,
    _rust: str,
    _overflow: str,
) -> None:
    result = claim(_site(target), None)
    assert isinstance(result, Claimed)
    assert (result.rule_id, result.result_type) == (rule, "int")


@pytest.mark.parametrize(("target", "_rule", "_rust", "_overflow"), QUERY_CASES)
@pytest.mark.parametrize(
    ("operand_types", "keywords"),
    [
        ((), ()),
        ((GRAPH_I64, GRAPH_I64), ()),
        ((None,), ()),
        (("object",), ()),
        ((GRAPH_I64,), (KeywordArg(name="weight"),)),
    ],
)
def test_static_misses_are_plugin_rejected(
    target: str,
    _rule: str,
    _rust: str,
    _overflow: str,
    operand_types: tuple[str | None, ...],
    keywords: tuple[KeywordArg, ...],
) -> None:
    result = claim(_site(target, operand_types, keywords=keywords), None)
    assert isinstance(result, Rejected)
    assert result.diagnostic.code == "RXTP-NETWORKX-020"


@pytest.mark.parametrize(("target", "rule", "rust", "overflow"), QUERY_CASES)
def test_lowering_borrows_resident_graph_and_checks_i64_count(
    target: str,
    rule: str,
    rust: str,
    overflow: str,
) -> None:
    lowered = lower(_claimed(target, rule), _ctx("graph"))
    assert lowered.rust == rust
    helpers = "\n".join(lowered.helpers)
    assert "graph: &RxtNxGraphI64" in helpers
    assert "i64::try_from" in helpers
    assert overflow in helpers


@pytest.mark.parametrize(("target", "rule", "_rust", "_overflow"), QUERY_CASES)
def test_lowering_rejects_wrong_operand_count(
    target: str,
    rule: str,
    _rust: str,
    _overflow: str,
) -> None:
    with pytest.raises(ValueError, match="requires exactly 1 operands"):
        lower(_claimed(target, rule), _ctx("graph", "extra"))


@pytest.mark.parametrize(("target", "rule", "_rust", "_overflow"), QUERY_CASES)
@pytest.mark.parametrize(
    "forged",
    [
        lambda site: replace(site, kind="binop"),
        lambda site: replace(site, rule_id="rextio-networkx/forged"),
        lambda site: replace(site, result_type="bool"),
        lambda site: replace(site, operand_types=("object",)),
        lambda site: replace(site, keywords=(KeywordArg(name="weight"),)),
        lambda site: replace(
            site,
            receiver=ReceiverMeta(arg_type="object", expr_kind="name", is_safe=True),
        ),
    ],
    ids=["kind", "rule", "result", "operand-types", "keywords", "receiver"],
)
def test_lowering_rejects_forged_claim_metadata(
    target: str,
    rule: str,
    _rust: str,
    _overflow: str,
    forged,
) -> None:
    with pytest.raises(ValueError, match="lowering contract mismatch"):
        lower(forged(_claimed(target, rule)), _ctx("graph"))


@pytest.mark.parametrize(("target", "rule", "_rust", "_overflow"), QUERY_CASES)
def test_lowering_rejects_forged_context_receiver(
    target: str,
    rule: str,
    _rust: str,
    _overflow: str,
) -> None:
    with pytest.raises(ValueError, match="lowering contract mismatch"):
        lower(
            _claimed(target, rule),
            replace(_ctx("graph"), receiver="forged"),
        )
