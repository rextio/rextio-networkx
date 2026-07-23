"""Exact resident connected-components fallback, claim, and lowering coverage."""

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
from rextio_networkx.claim.components import RESIDENT_CC_RULE, RESIDENT_CC_TARGET
from rextio_networkx.diagnostics import COMPONENT_LIST, GRAPH_I64
from rextio_networkx.lower import lower


@pytest.mark.parametrize(
    "edges",
    [
        [],
        [(0, 1), (1, 2), (10, 11)],
        [(4, 1), (1, 4), (4, 4), (20, 21)],
        [(-(2**63), 7), (2**63 - 1, 2**63 - 1)],
    ],
)
def test_fallback_matches_networkx_resident_components_exactly(
    edges: list[tuple[int, int]],
) -> None:
    before = deepcopy(edges)
    graph = rn.graph_from_edgelist(edges)
    graph_before = (list(graph.nodes), list(graph.edges), dict(graph.graph))

    actual = rn.connected_components(graph)
    expected = list(nx.connected_components(graph))

    assert type(actual) is list
    assert actual == expected
    assert all(type(component) is set for component in actual)
    assert edges == before
    assert (list(graph.nodes), list(graph.edges), dict(graph.graph)) == graph_before


def test_fallback_rejects_nonresident_graph() -> None:
    with pytest.raises(
        TypeError,
        match="graph must be produced by graph_from_edgelist",
    ):
        rn.connected_components(nx.Graph([(0, 1)]))


def _site(
    operand_types: tuple[str | None, ...] = (GRAPH_I64,),
    *,
    kind: str = "call",
    target: str = RESIDENT_CC_TARGET,
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


def _claimed() -> ClaimSite:
    return replace(_site(), rule_id=RESIDENT_CC_RULE, result_type=COMPONENT_LIST)


def _ctx(*operands: str) -> LoweringContext:
    return LoweringContext(operands=operands, target_language="rust", fresh_name=str)


def test_exact_static_shape_is_claimed() -> None:
    result = claim(_site(), None)
    assert isinstance(result, Claimed)
    assert (result.rule_id, result.result_type) == (RESIDENT_CC_RULE, COMPONENT_LIST)


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
    operand_types: tuple[str | None, ...],
    keywords: tuple[KeywordArg, ...],
) -> None:
    result = claim(_site(operand_types, keywords=keywords), None)
    assert isinstance(result, Rejected)
    assert result.diagnostic.code == "RXTP-NETWORKX-020"


def test_lowering_borrows_resident_graph_and_owns_no_constructor() -> None:
    lowered = lower(_claimed(), _ctx("graph"))
    assert lowered.rust == "__rxtnx_connected_components_graph_i64(py, &graph)?"
    helpers = "\n".join(lowered.helpers)
    assert "graph: &RxtNxGraphI64" in helpers
    assert "__rxtnx_graph_from_edgelist_i64" not in helpers


def test_lowering_rejects_wrong_operand_count() -> None:
    with pytest.raises(ValueError, match="exactly one operand"):
        lower(_claimed(), _ctx("graph", "extra"))


@pytest.mark.parametrize(
    "forged",
    [
        lambda site: replace(site, kind="binop"),
        lambda site: replace(site, target="rextio_networkx.connected_components_from_edgelist"),
        lambda site: replace(site, rule_id="rextio-networkx/forged"),
        lambda site: replace(site, result_type="list"),
        lambda site: replace(site, operand_types=("object",)),
        lambda site: replace(site, keywords=(KeywordArg(name="sort"),)),
        lambda site: replace(
            site,
            receiver=ReceiverMeta(arg_type="object", expr_kind="name", is_safe=True),
        ),
    ],
    ids=["kind", "target", "rule", "result", "operand-types", "keywords", "receiver"],
)
def test_lowering_rejects_forged_claim_metadata(forged) -> None:
    with pytest.raises(ValueError, match="lowering contract mismatch"):
        lower(forged(_claimed()), _ctx("graph"))


def test_lowering_rejects_forged_context_receiver() -> None:
    with pytest.raises(ValueError, match="lowering contract mismatch"):
        lower(_claimed(), replace(_ctx("graph"), receiver="forged"))
