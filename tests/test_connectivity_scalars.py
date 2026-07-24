"""Exact fallback, claim, and lowering coverage for resident connectivity scalars."""

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
from rextio_networkx.claim.components import (
    IS_CONNECTED_RULE,
    IS_CONNECTED_TARGET,
    NUMBER_CONNECTED_COMPONENTS_RULE,
    NUMBER_CONNECTED_COMPONENTS_TARGET,
)
from rextio_networkx.diagnostics import GRAPH_I64
from rextio_networkx.lower import lower


@pytest.mark.parametrize(
    ("edges", "expected_count", "expected_connected"),
    [
        ([], 0, None),
        ([(0, 1)], 1, True),
        ([(0, 1), (1, 2), (10, 11)], 2, False),
        ([(4, 1), (1, 4), (4, 4)], 1, True),
        ([(-(2**63), 7), (2**63 - 1, 2**63 - 1)], 2, False),
    ],
)
def test_fallback_connectivity_scalars_match_networkx_exactly(
    edges: list[tuple[int, int]],
    expected_count: int,
    expected_connected: bool | None,
) -> None:
    before = deepcopy(edges)
    graph = rn.graph_from_edgelist(edges)
    graph_before = (list(graph.nodes), list(graph.edges), dict(graph.graph))

    count = rn.number_connected_components(graph)
    assert type(count) is int
    assert count == expected_count == nx.number_connected_components(graph)

    if expected_connected is None:
        with pytest.raises(nx.NetworkXPointlessConcept) as caught:
            rn.is_connected(graph)
        error = caught.value
        assert (type(error), str(error), error.args) == (
            nx.NetworkXPointlessConcept,
            "Connectivity is undefined for the null graph.",
            ("Connectivity is undefined for the null graph.",),
        )
    else:
        connected = rn.is_connected(graph)
        assert type(connected) is bool
        assert connected is expected_connected is nx.is_connected(graph)

    assert edges == before
    assert (list(graph.nodes), list(graph.edges), dict(graph.graph)) == graph_before


@pytest.mark.parametrize("query", [rn.number_connected_components, rn.is_connected])
def test_fallback_connectivity_scalars_reject_nonresident_graph(query) -> None:
    with pytest.raises(TypeError, match="graph must be produced by graph_from_edgelist"):
        query(nx.Graph([(0, 1)]))


QUERY_CASES = (
    (
        NUMBER_CONNECTED_COMPONENTS_TARGET,
        NUMBER_CONNECTED_COMPONENTS_RULE,
        "int",
        "__rxtnx_number_connected_components_i64(&graph)?",
    ),
    (
        IS_CONNECTED_TARGET,
        IS_CONNECTED_RULE,
        "bool",
        "__rxtnx_is_connected_i64(py, &graph)?",
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


def _claimed(target: str, rule: str, result_type: str) -> ClaimSite:
    return replace(_site(target), rule_id=rule, result_type=result_type)


def _ctx(*operands: str) -> LoweringContext:
    return LoweringContext(operands=operands, target_language="rust", fresh_name=str)


@pytest.mark.parametrize(("target", "rule", "result_type", "_rust"), QUERY_CASES)
def test_exact_static_shapes_are_claimed(
    target: str,
    rule: str,
    result_type: str,
    _rust: str,
) -> None:
    result = claim(_site(target), None)
    assert isinstance(result, Claimed)
    assert (result.rule_id, result.result_type) == (rule, result_type)


@pytest.mark.parametrize(("target", "_rule", "_result_type", "_rust"), QUERY_CASES)
@pytest.mark.parametrize(
    ("operand_types", "keywords"),
    [
        ((), ()),
        ((GRAPH_I64, GRAPH_I64), ()),
        ((None,), ()),
        (("object",), ()),
        ((GRAPH_I64,), (KeywordArg(name="sort"),)),
    ],
)
def test_static_misses_are_plugin_rejected(
    target: str,
    _rule: str,
    _result_type: str,
    _rust: str,
    operand_types: tuple[str | None, ...],
    keywords: tuple[KeywordArg, ...],
) -> None:
    result = claim(_site(target, operand_types, keywords=keywords), None)
    assert isinstance(result, Rejected)
    assert result.diagnostic.code == "RXTP-NETWORKX-020"


@pytest.mark.parametrize(("target", "rule", "result_type", "rust"), QUERY_CASES)
def test_lowering_borrows_resident_graph_and_reuses_component_walk(
    target: str,
    rule: str,
    result_type: str,
    rust: str,
) -> None:
    lowered = lower(_claimed(target, rule, result_type), _ctx("graph"))
    assert lowered.rust == rust
    helpers = "\n".join(lowered.helpers)
    assert "graph: &RxtNxGraphI64" in helpers
    assert "fn __rxtnx_component_count_i64" in helpers
    assert "__rxtnx_graph_from_edgelist_i64" not in helpers
    if target == IS_CONNECTED_TARGET:
        assert "NetworkXPointlessConcept" in helpers
        assert "Connectivity is undefined for the null graph." in helpers


@pytest.mark.parametrize(("target", "rule", "result_type", "_rust"), QUERY_CASES)
def test_lowering_rejects_wrong_operand_count(
    target: str,
    rule: str,
    result_type: str,
    _rust: str,
) -> None:
    with pytest.raises(ValueError, match="exactly one operand"):
        lower(_claimed(target, rule, result_type), _ctx("graph", "extra"))


@pytest.mark.parametrize(("target", "rule", "result_type", "_rust"), QUERY_CASES)
@pytest.mark.parametrize(
    "forged",
    [
        lambda site: replace(site, kind="binop"),
        lambda site: replace(site, target="rextio_networkx.connected_components"),
        lambda site: replace(site, rule_id="rextio-networkx/forged"),
        lambda site: replace(site, result_type="rextio-networkx/forged"),
        lambda site: replace(site, operand_types=("object",)),
        lambda site: replace(site, keywords=(KeywordArg(name="sort"),)),
        lambda site: replace(
            site,
            receiver=ReceiverMeta(arg_type="object", expr_kind="name", is_safe=True),
        ),
    ],
    ids=["kind", "target", "rule", "result", "operand-types", "keywords", "receiver"],
)
def test_lowering_rejects_forged_claim_metadata(
    target: str,
    rule: str,
    result_type: str,
    _rust: str,
    forged,
) -> None:
    with pytest.raises(ValueError, match="lowering contract mismatch"):
        lower(forged(_claimed(target, rule, result_type)), _ctx("graph"))


@pytest.mark.parametrize(("target", "rule", "result_type", "_rust"), QUERY_CASES)
def test_lowering_rejects_forged_context_receiver(
    target: str,
    rule: str,
    result_type: str,
    _rust: str,
) -> None:
    with pytest.raises(ValueError, match="lowering contract mismatch"):
        lower(
            _claimed(target, rule, result_type),
            replace(_ctx("graph"), receiver="forged"),
        )
