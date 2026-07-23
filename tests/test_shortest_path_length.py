"""Exact fallback, claim, and lowering coverage for source-target path length."""

from __future__ import annotations

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
    SHORTEST_PATH_LENGTH_RULE,
    SHORTEST_PATH_LENGTH_TARGET,
)
from rextio_networkx.diagnostics import GRAPH_I64, NODE_I64
from rextio_networkx.lower import lower


@pytest.mark.parametrize(
    ("edges", "source", "target", "expected"),
    [
        ([(0, 1), (1, 2)], 0, 2, 2),
        ([(7, 7), (7, 8)], 7, 7, 0),
        ([(4, 1), (1, 4), (4, 2)], 2, 1, 2),
        ([(2**63 - 1, -(2**63))], 2**63 - 1, -(2**63), 1),
    ],
)
def test_fallback_matches_networkx_shortest_path_length_exactly(
    edges: list[tuple[int, int]],
    source: int,
    target: int,
    expected: int,
) -> None:
    graph = rn.graph_from_edgelist(edges)
    actual = rn.shortest_path_length(graph, source, target)

    assert type(actual) is int
    assert actual == expected
    assert actual == nx.shortest_path_length(graph, source, target)


@pytest.mark.parametrize(
    ("source", "target", "expected"),
    [
        (0, 11, (nx.NetworkXNoPath, "No path between 0 and 11.")),
        (0, -1, (nx.NodeNotFound, "Target -1 is not in G")),
        (-1, 0, (nx.NodeNotFound, "Source -1 is not in G")),
        (-1, -2, (nx.NodeNotFound, "Source -1 is not in G")),
    ],
)
def test_fallback_preserves_exact_error_and_endpoint_precedence(
    source: int,
    target: int,
    expected: tuple[type[BaseException], str],
) -> None:
    graph = rn.graph_from_edgelist([(0, 1), (10, 11)])
    with pytest.raises(BaseException) as caught:
        rn.shortest_path_length(graph, source, target)
    error = caught.value
    assert (type(error), str(error), error.args) == (
        expected[0],
        expected[1],
        (expected[1],),
    )


def _site(
    operand_types: tuple[str, ...] = (GRAPH_I64, NODE_I64, NODE_I64),
    *,
    kind: str = "call",
    target: str = SHORTEST_PATH_LENGTH_TARGET,
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
    return replace(_site(), rule_id=SHORTEST_PATH_LENGTH_RULE, result_type="int")


def _ctx(*operands: str) -> LoweringContext:
    return LoweringContext(operands=operands, target_language="rust", fresh_name=str)


def test_exact_static_shape_is_claimed() -> None:
    result = claim(_site(), None)
    assert isinstance(result, Claimed)
    assert (result.rule_id, result.result_type) == (SHORTEST_PATH_LENGTH_RULE, "int")


@pytest.mark.parametrize(
    ("operand_types", "keywords"),
    [
        ((GRAPH_I64, NODE_I64), ()),
        ((GRAPH_I64, NODE_I64, NODE_I64, NODE_I64), ()),
        ((GRAPH_I64, NODE_I64, "int"), ()),
        ((GRAPH_I64, NODE_I64, NODE_I64), (KeywordArg(name="weight"),)),
    ],
)
def test_static_misses_are_plugin_rejected(
    operand_types: tuple[str, ...],
    keywords: tuple[KeywordArg, ...],
) -> None:
    result = claim(_site(operand_types, keywords=keywords), None)
    assert isinstance(result, Rejected)
    assert result.diagnostic.code == "RXTP-NETWORKX-020"


def test_lowering_borrows_resident_graph_and_returns_int() -> None:
    lowered = lower(_claimed(), _ctx("graph", "source", "target"))
    assert lowered.rust == "__rxtnx_shortest_path_length_i64(py, &graph, source, target)?"
    helpers = "\n".join(lowered.helpers)
    assert "Source {} is not in G" in helpers
    assert "Target {} is not in G" in helpers
    assert "No path between {} and {}." in helpers


def test_lowering_rejects_wrong_operand_count() -> None:
    with pytest.raises(ValueError, match="requires exactly 3 operands"):
        lower(_claimed(), _ctx("graph", "source"))


@pytest.mark.parametrize(
    "forged",
    [
        lambda site: replace(site, kind="binop"),
        lambda site: replace(site, target="rextio_networkx.has_path"),
        lambda site: replace(site, rule_id="rextio-networkx/forged"),
        lambda site: replace(site, result_type="bool"),
        lambda site: replace(site, operand_types=(GRAPH_I64, NODE_I64, "int")),
        lambda site: replace(site, keywords=(KeywordArg(name="weight"),)),
        lambda site: replace(
            site,
            receiver=ReceiverMeta(arg_type="object", expr_kind="name", is_safe=True),
        ),
    ],
    ids=["kind", "target", "rule", "result", "operand-types", "keywords", "receiver"],
)
def test_lowering_rejects_forged_claim_metadata(forged) -> None:
    with pytest.raises(ValueError, match="lowering contract mismatch"):
        lower(forged(_claimed()), _ctx("graph", "source", "target"))


def test_lowering_rejects_forged_context_receiver() -> None:
    with pytest.raises(ValueError, match="lowering contract mismatch"):
        lower(_claimed(), replace(_ctx("graph", "source", "target"), receiver="forged"))
