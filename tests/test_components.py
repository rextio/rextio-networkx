"""Unit tests for the adapter, claim decisions, and lowering emission.

Tests-first coverage of the covered semantics and the fail-closed paths: the
public/fallback adapter against NetworkX, the deterministic claim router, and
the Rust emission shape. These do not require Cargo; the native<->fallback
value equivalence is certified under Cargo in ``tests/e2e``.
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from rextio.plugins.api import (
    CallableMeta,
    Claimed,
    ClaimExpr,
    ClaimLiteral,
    ClaimSite,
    KeywordArg,
    LoweringContext,
    NotCovered,
    ReceiverMeta,
    Rejected,
)

import rextio_networkx as rn
from rextio_networkx.claim import claim
from rextio_networkx.claim.components import (
    CC_RULE,
    CC_TARGET,
    IS_CONNECTED_RULE,
    IS_CONNECTED_TARGET,
    NUMBER_CONNECTED_COMPONENTS_RULE,
    NUMBER_CONNECTED_COMPONENTS_TARGET,
    RESIDENT_CC_RULE,
    RESIDENT_CC_TARGET,
)
from rextio_networkx.diagnostics import COMPONENT_LIST, EDGELIST_I64, GRAPH_I64
from rextio_networkx.lower import lower
from rextio_networkx.plugin_types import plugin_type_keys

nx = pytest.importorskip("networkx")


def _site(operand_types, *, kind="call", target=CC_TARGET, keywords=()):
    return ClaimSite(
        kind=kind,
        target=target,
        operand_types=tuple(operand_types),
        file_path="",
        line=0,
        column=0,
        keywords=tuple(keywords),
    )


# --- Public / fallback adapter -------------------------------------------


def test_adapter_matches_networkx_exactly(covered_case: list[tuple[int, int]]) -> None:
    expected = list(nx.connected_components(nx.from_edgelist(covered_case)))
    assert rn.connected_components_from_edgelist(covered_case) == expected


def test_adapter_returns_list_of_sets() -> None:
    result = rn.connected_components_from_edgelist([(0, 1), (2, 3)])
    assert isinstance(result, list)
    assert all(isinstance(component, set) for component in result)


def test_adapter_component_order_is_by_first_node_insertion() -> None:
    # Node 7 is inserted first, then 9, then 1 — components follow that order.
    edges = [(7, 8), (9, 9), (8, 7), (1, 2), (2, 3), (3, 1)]
    result = rn.connected_components_from_edgelist(edges)
    assert result == [{7, 8}, {9}, {1, 2, 3}]


def test_adapter_empty_is_empty_list() -> None:
    assert rn.connected_components_from_edgelist([]) == []


def test_annotation_aliases_are_typing_aliases() -> None:
    assert rn.EdgeListI64 == list[tuple[int, int]]
    assert rn.ComponentList == list[set[int]]


# --- Claim decisions ------------------------------------------------------


def test_claim_edgelist_argument_is_claimed() -> None:
    result = claim(_site([EDGELIST_I64]), None)
    assert isinstance(result, Claimed)
    assert result.rule_id == CC_RULE
    assert result.result_type == COMPONENT_LIST
    assert result.operand_mode == "direct"


def test_claim_result_type_is_a_registered_plugin_type_key() -> None:
    result = claim(_site([EDGELIST_I64]), None)
    assert isinstance(result, Claimed)
    assert result.result_type in plugin_type_keys()


def test_claim_known_but_unsupported_argument_is_rejected() -> None:
    result = claim(_site(["list[int]"]), None)
    assert isinstance(result, Rejected)
    assert result.diagnostic.code == "RXTP-NETWORKX-010"
    assert result.diagnostic.suggestion


def test_claim_unresolved_argument_is_not_covered() -> None:
    assert isinstance(claim(_site([None]), None), NotCovered)


def test_claim_wrong_arity_is_not_covered() -> None:
    assert isinstance(claim(_site([EDGELIST_I64, EDGELIST_I64]), None), NotCovered)
    assert isinstance(claim(_site([]), None), NotCovered)


def test_claim_keyword_call_is_not_covered() -> None:
    site = _site([EDGELIST_I64], keywords=[KeywordArg(name="copy")])
    assert isinstance(claim(site, None), NotCovered)


def test_claim_other_target_is_not_covered() -> None:
    assert isinstance(
        claim(_site([EDGELIST_I64], target="networkx.from_edgelist"), None), NotCovered
    )
    assert isinstance(
        claim(_site([EDGELIST_I64], target="networkx.connected_components"), None),
        NotCovered,
    )


def test_claim_binop_site_is_not_covered() -> None:
    assert isinstance(claim(_site([EDGELIST_I64], kind="binop", target="+"), None), NotCovered)


def test_claim_is_deterministic() -> None:
    first = claim(_site([EDGELIST_I64]), None)
    second = claim(_site([EDGELIST_I64]), None)
    assert first == second


# --- Lowering emission ----------------------------------------------------


def _claimed_site():
    return ClaimSite(
        kind="call",
        target=CC_TARGET,
        operand_types=(EDGELIST_I64,),
        file_path="",
        line=0,
        column=0,
        rule_id=CC_RULE,
        result_type=COMPONENT_LIST,
    )


def _ctx(operands=("edges",)):
    return LoweringContext(
        operands=tuple(operands),
        target_language="rust",
        fresh_name=lambda prefix: f"{prefix}_0",
    )


def test_lower_emits_petgraph_helper_call() -> None:
    expr = lower(_claimed_site(), _ctx())
    assert expr.rust == "__rxtnx_connected_components_i64(py, &edges)?"
    # Granular exact-text helpers travel together so API-1.3 signature support
    # can deduplicate shared boundary/struct items against claim-local support.
    assert len(expr.helpers) == len(set(expr.helpers))
    joined = "\n".join(expr.helpers)
    assert "petgraph::graph::" in joined
    assert "petgraph::unionfind::UnionFind" in joined
    assert "pyo3::types::PyList::empty(py)" in joined
    assert "pyo3::types::PySet::empty(py)" in joined
    assert expr.uses == ()


def test_lower_helper_rejects_bool_labels_at_the_boundary() -> None:
    # The node-label extractor refuses a Python bool (an int subclass) so the
    # native leg cannot silently coerce True/False to 1/0 and diverge in element
    # type from the NetworkX fallback.
    joined = "\n".join(lower(_claimed_site(), _ctx()).helpers)
    assert "__rxtnx_parse_exact_i64" in joined
    assert "is_exact_instance_of::<pyo3::types::PyInt>" in joined
    assert "PyTypeError::new_err" in joined
    # The API-1.3 raw boundary validates into an owned typed list before use.
    assert "edges: &pyo3::Bound<'_, pyo3::types::PyAny>" in joined


def test_lower_helper_returns_pyresult_bound_list() -> None:
    joined = "\n".join(lower(_claimed_site(), _ctx()).helpers)
    assert "-> pyo3::PyResult<pyo3::Bound<'py, pyo3::types::PyList>>" in joined
    assert ") -> pyo3::PyResult<i64>" in joined


def test_lower_wrong_target_returns_none_via_router_error() -> None:
    site = ClaimSite(
        kind="call",
        target="networkx.from_edgelist",
        operand_types=(EDGELIST_I64,),
        file_path="",
        line=0,
        column=0,
        rule_id=CC_RULE,
        result_type=COMPONENT_LIST,
    )
    with pytest.raises(ValueError, match="cannot lower unclaimed site"):
        lower(site, _ctx())


def test_lower_fails_closed_on_wrong_operand_count() -> None:
    with pytest.raises(ValueError, match="exactly one operand"):
        lower(_claimed_site(), _ctx(operands=("a", "b")))


@pytest.mark.parametrize(
    "forged",
    [
        lambda site: replace(site, kind="binop"),
        lambda site: replace(site, target="rextio_networkx.graph_from_edgelist"),
        lambda site: replace(site, rule_id="rextio-networkx/forged"),
        lambda site: replace(site, result_type="rextio-networkx/forged"),
        lambda site: replace(site, operand_types=("rextio-networkx/forged",)),
        lambda site: replace(site, keywords=(KeywordArg(name="copy"),)),
        lambda site: replace(
            site,
            receiver=ReceiverMeta(arg_type="object", expr_kind="name", is_safe=True),
        ),
    ],
    ids=["kind", "target", "rule", "result", "operand-types", "keywords", "receiver"],
)
def test_lower_rejects_forged_claim_metadata(forged) -> None:
    """Lowering must independently enforce every static call-shape invariant."""
    with pytest.raises(ValueError):
        lower(forged(_claimed_site()), _ctx())


def test_lower_rejects_forged_context_receiver() -> None:
    with pytest.raises(ValueError, match="lowering contract mismatch"):
        lower(_claimed_site(), replace(_ctx(), receiver="edges"))


_COMPONENT_LOWERING_LANES = (
    (CC_TARGET, CC_RULE, COMPONENT_LIST, EDGELIST_I64),
    (RESIDENT_CC_TARGET, RESIDENT_CC_RULE, COMPONENT_LIST, GRAPH_I64),
    (
        NUMBER_CONNECTED_COMPONENTS_TARGET,
        NUMBER_CONNECTED_COMPONENTS_RULE,
        "int",
        GRAPH_I64,
    ),
    (IS_CONNECTED_TARGET, IS_CONNECTED_RULE, "bool", GRAPH_I64),
)


def _component_lane_site(
    target: str,
    rule_id: str,
    result_type: str,
    operand_type: str,
) -> ClaimSite:
    return ClaimSite(
        kind="call",
        target=target,
        operand_types=(operand_type,),
        file_path="",
        line=0,
        column=0,
        rule_id=rule_id,
        result_type=result_type,
    )


def _matching_call_expression(site: ClaimSite) -> ClaimExpr:
    return ClaimExpr(
        kind="call",
        target=site.target,
        result_type=site.result_type,
        children=(
            ClaimExpr(
                kind="leaf",
                result_type=site.operand_types[0],
                leaf_index=0,
                leaf_kind="name",
            ),
        ),
    )


@pytest.mark.parametrize(
    ("target", "rule_id", "result_type", "operand_type"),
    _COMPONENT_LOWERING_LANES,
)
def test_component_lanes_accept_aligned_nonliteral_and_matching_expression_metadata(
    target: str,
    rule_id: str,
    result_type: str,
    operand_type: str,
) -> None:
    site = _component_lane_site(target, rule_id, result_type, operand_type)
    site = replace(
        site,
        operand_literals=(ClaimLiteral(),),
        expression=_matching_call_expression(site),
    )

    assert lower(site, _ctx()).rust


@pytest.mark.parametrize(
    ("target", "rule_id", "result_type", "operand_type"),
    _COMPONENT_LOWERING_LANES,
)
@pytest.mark.parametrize(
    "forge",
    [
        lambda site: replace(
            site,
            operand_literals=(ClaimLiteral(is_literal=True, value=0),),
        ),
        lambda site: replace(
            site,
            operand_literals=(ClaimLiteral(), ClaimLiteral()),
        ),
        lambda site: replace(
            site,
            callables=(CallableMeta(arg_index=0, qualname="app.callback"),),
        ),
        lambda site: replace(
            site,
            expression=ClaimExpr(
                kind="binop",
                target="+",
                result_type=site.result_type,
                children=(
                    ClaimExpr(kind="leaf", leaf_index=0, leaf_kind="name"),
                    ClaimExpr(kind="leaf", leaf_index=1, leaf_kind="name"),
                ),
            ),
        ),
        lambda site: replace(
            site,
            expression=ClaimExpr(
                kind="call",
                target="rextio_networkx.forged",
                result_type=site.result_type,
            ),
        ),
        lambda site: replace(
            site,
            expression=ClaimExpr(
                kind="call",
                target=site.target,
                result_type="rextio-networkx/forged",
            ),
        ),
    ],
    ids=[
        "literal-operand",
        "misaligned-operand-literals",
        "callable",
        "expression-kind",
        "expression-target",
        "expression-result",
    ],
)
def test_component_lanes_reject_extended_forged_claim_metadata(
    target: str,
    rule_id: str,
    result_type: str,
    operand_type: str,
    forge,
) -> None:
    site = _component_lane_site(target, rule_id, result_type, operand_type)

    with pytest.raises(ValueError, match="lowering contract mismatch"):
        lower(forge(site), _ctx())


def _with_forged_backend(ctx: LoweringContext) -> LoweringContext:
    object.__setattr__(ctx, "backend", "standalone-rust")
    return ctx


@pytest.mark.parametrize(
    ("target", "rule_id", "result_type", "operand_type"),
    _COMPONENT_LOWERING_LANES,
)
@pytest.mark.parametrize(
    "forge",
    [
        lambda ctx: replace(ctx, target_language="python"),
        lambda ctx: _with_forged_backend(ctx),
        lambda ctx: replace(ctx, leaf_operands=("forged",)),
    ],
    ids=["target-language", "backend", "leaf-operands"],
)
def test_component_lanes_reject_forged_lowering_context(
    target: str,
    rule_id: str,
    result_type: str,
    operand_type: str,
    forge,
) -> None:
    site = _component_lane_site(target, rule_id, result_type, operand_type)

    with pytest.raises(ValueError, match="lowering contract mismatch"):
        lower(site, forge(_ctx()))


def test_component_extended_contract_survives_optimized_interpreter() -> None:
    program = (
        "from rextio.plugins.api import ClaimLiteral, ClaimSite, LoweringContext\n"
        "from rextio_networkx.claim.components import CC_RULE, CC_TARGET\n"
        "from rextio_networkx.diagnostics import COMPONENT_LIST, EDGELIST_I64\n"
        "from rextio_networkx.lower import lower\n"
        "site = ClaimSite(kind='call', target=CC_TARGET, operand_types=(EDGELIST_I64,), "
        "file_path='', line=0, column=0, rule_id=CC_RULE, result_type=COMPONENT_LIST, "
        "operand_literals=(ClaimLiteral(is_literal=True, value=0),))\n"
        "ctx = LoweringContext(operands=('edges',), target_language='rust', fresh_name=str)\n"
        "try:\n"
        "    lower(site, ctx)\n"
        "except ValueError:\n"
        "    print('guard-fired')\n"
        "else:\n"
        "    raise SystemExit('extended metadata guard did not fire under -O')\n"
    )
    completed = subprocess.run(
        [sys.executable, "-O", "-c", program],
        capture_output=True,
        text=True,
        check=True,
        env={
            **os.environ,
            "PYTHONPATH": os.pathsep.join(
                [
                    str(Path(__file__).parents[1] / "src"),
                    os.environ.get("PYTHONPATH", ""),
                ]
            ),
        },
    )
    assert "guard-fired" in completed.stdout
