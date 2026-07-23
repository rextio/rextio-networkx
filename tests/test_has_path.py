"""Exact fallback, claim, and lowering coverage for resident ``has_path``."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import os
from pathlib import Path
import subprocess
import sys

import networkx as nx
import pytest

import rextio_networkx as rn
from rextio.plugins.api import Claimed, ClaimSite, KeywordArg, LoweringContext, ReceiverMeta, Rejected
from rextio_networkx.claim import claim
from rextio_networkx.claim.traversal import HAS_PATH_RULE, HAS_PATH_TARGET
from rextio_networkx.diagnostics import GRAPH_I64, NODE_I64
from rextio_networkx.lower import lower


@pytest.mark.parametrize(
    ("edges", "source", "target"),
    [
        ([(0, 1), (1, 2)], 0, 2),
        ([(0, 1), (10, 11)], 0, 11),
        ([(7, 7), (7, 8)], 7, 7),
        ([(4, 1), (1, 4), (4, 2)], 2, 1),
    ],
)
def test_fallback_matches_networkx_has_path_exactly(
    edges: list[tuple[int, int]], source: int, target: int
) -> None:
    before = deepcopy(edges)
    graph = rn.graph_from_edgelist(edges)
    graph_before = (list(graph.nodes), list(graph.edges), dict(graph.graph))

    actual = rn.has_path(graph, source, target)

    assert type(actual) is bool
    assert actual is nx.has_path(graph, source, target)
    assert edges == before
    assert (list(graph.nodes), list(graph.edges), dict(graph.graph)) == graph_before


@pytest.mark.parametrize(
    ("source", "target", "expected"),
    [
        (1, 2, (nx.NodeNotFound, "Target 2 is not in G", ("Target 2 is not in G",))),
        (2, 1, (nx.NodeNotFound, "Source 2 is not in G", ("Source 2 is not in G",))),
        (2, 3, (nx.NodeNotFound, "Source 2 is not in G", ("Source 2 is not in G",))),
    ],
)
def test_fallback_preserves_networkx_missing_endpoint_precedence(
    source: int,
    target: int,
    expected: tuple[type[BaseException], str, tuple[object, ...]],
) -> None:
    graph = rn.graph_from_edgelist([(0, 1)])
    with pytest.raises(BaseException) as caught:
        rn.has_path(graph, source, target)
    error = caught.value
    assert (type(error), str(error), error.args) == expected


def _site(
    operand_types: tuple[str, ...] = (GRAPH_I64, NODE_I64, NODE_I64),
    *,
    kind: str = "call",
    target: str = HAS_PATH_TARGET,
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
    return replace(_site(), rule_id=HAS_PATH_RULE, result_type="bool")


def _ctx(*operands: str) -> LoweringContext:
    return LoweringContext(operands=operands, target_language="rust", fresh_name=str)


def test_exact_static_shape_is_claimed() -> None:
    result = claim(_site(), None)
    assert isinstance(result, Claimed)
    assert (result.rule_id, result.result_type) == (HAS_PATH_RULE, "bool")


@pytest.mark.parametrize(
    ("operand_types", "keywords"),
    [
        ((GRAPH_I64, NODE_I64), ()),
        ((GRAPH_I64, NODE_I64, NODE_I64, NODE_I64), ()),
        ((GRAPH_I64, NODE_I64, "int"), ()),
        ((GRAPH_I64, NODE_I64, NODE_I64), (KeywordArg(name="cutoff"),)),
    ],
)
def test_static_misses_are_plugin_rejected(
    operand_types: tuple[str, ...], keywords: tuple[KeywordArg, ...]
) -> None:
    result = claim(_site(operand_types, keywords=keywords), None)
    assert isinstance(result, Rejected)
    assert result.diagnostic.code == "RXTP-NETWORKX-020"


def test_lowering_borrows_resident_graph_and_returns_bool() -> None:
    lowered = lower(_claimed(), _ctx("graph", "source", "target"))
    assert lowered.rust == "__rxtnx_has_path_i64(py, &graph, source, target)?"
    assert "Source {} is not in G" in "\n".join(lowered.helpers)
    assert "Target {} is not in G" in "\n".join(lowered.helpers)


def test_lowering_rejects_wrong_operand_count() -> None:
    with pytest.raises(ValueError, match="requires exactly 3 operands"):
        lower(_claimed(), _ctx("graph", "source"))


@pytest.mark.parametrize(
    "forged",
    [
        lambda site: replace(site, kind="binop"),
        lambda site: replace(site, target="rextio_networkx.bfs_edges"),
        lambda site: replace(site, rule_id="rextio-networkx/forged"),
        lambda site: replace(site, result_type="rextio-networkx/forged"),
        lambda site: replace(site, operand_types=(GRAPH_I64, NODE_I64, "int")),
        lambda site: replace(site, keywords=(KeywordArg(name="cutoff"),)),
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


def test_lower_metadata_contract_survives_optimized_interpreter() -> None:
    program = (
        "from rextio.plugins.api import ClaimSite, LoweringContext\n"
        "from rextio_networkx.claim.traversal import HAS_PATH_RULE, HAS_PATH_TARGET\n"
        "from rextio_networkx.diagnostics import GRAPH_I64, NODE_I64\n"
        "from rextio_networkx.lower import lower\n"
        "site = ClaimSite(kind='call', target=HAS_PATH_TARGET, "
        "operand_types=(GRAPH_I64, NODE_I64, NODE_I64), file_path='', line=0, column=0, "
        "rule_id=HAS_PATH_RULE, result_type='rextio-networkx/forged')\n"
        "ctx = LoweringContext(operands=('graph', 'source', 'target'), "
        "target_language='rust', fresh_name=str)\n"
        "try:\n"
        "    lower(site, ctx)\n"
        "except ValueError:\n"
        "    print('guard-fired')\n"
        "else:\n"
        "    raise SystemExit('metadata guard did not fire under -O')\n"
    )
    completed = subprocess.run(
        [sys.executable, "-O", "-c", program],
        capture_output=True,
        text=True,
        check=True,
        env={
            **os.environ,
            "PYTHONPATH": os.pathsep.join(
                [str(Path(__file__).parents[1] / "src"), os.environ.get("PYTHONPATH", "")]
            ),
        },
    )
    assert "guard-fired" in completed.stdout
