"""The real vertical slice: certification of the covered route under Cargo.

Builds a fixture project once through the core certification kit
(``rextio.plugins.testing``) with the REAL entry-point-discoverable plugin — no
monkeypatching — then asserts the native ``petgraph`` route was actually
selected and that the native and fallback legs return identical
``list[set[int]]`` values for the covered semantics (empty, duplicates,
self-loops, negative labels, multiple components, insertion order), including
hypothesis-driven inputs.

NetworkX and Hypothesis are mandatory dev/test dependencies (NetworkX is a
pinned runtime dependency the fallback leg delegates to), so they are imported
unconditionally at module scope. Cargo is the only environment gate: the whole
module is skipped unless ``cargo`` is on ``PATH``.
"""

from __future__ import annotations

import json
import shutil

import networkx as nx
import pytest
from hypothesis import given, settings, strategies as st

from rextio.plugins.testing import (
    CertificationError,
    CertifiedProject,
    build_certification_project,
    default_equals,
)

pytestmark = pytest.mark.skipif(
    shutil.which("cargo") is None, reason="real-cargo certification requires cargo on PATH"
)

# The covered semantics, each an undirected simple-graph edge list of signed i64
# labels (kept in step with tests/conftest.py::COVERED_EDGE_LISTS). Every case is
# compared native-vs-fallback and against NetworkX.
COVERED_EDGE_LISTS: dict[str, list[tuple[int, int]]] = {
    "empty": [],
    "single_edge": [(0, 1)],
    "self_loop": [(5, 5)],
    "self_loop_then_edge": [(5, 5), (5, 6)],
    "duplicate_edges": [(0, 1), (0, 1), (1, 2)],
    "chain": [(0, 1), (1, 2), (2, 3)],
    "disconnected": [(0, 1), (1, 2), (10, 11)],
    "negative_labels": [(-3, -4), (-4, -5), (100, -3)],
    "insertion_order": [(7, 8), (9, 9), (8, 7), (1, 2), (2, 3), (3, 1)],
    "reverse_seen_order": [(4, 3), (3, 2), (0, 1)],
    "i64_bounds": [(2**63 - 1, -(2**63)), (0, 2**63 - 1)],
}

KERNELS = """
import networkx as nx
from rextio_networkx import (
    ComponentList,
    EdgeListI64,
    connected_components_from_edgelist,
)


def components(edges: EdgeListI64) -> ComponentList:
    return connected_components_from_edgelist(edges)


# Intentionally NOT lowerable under core plugin API 1.2 (nested opaque calls,
# no boundary representation for the intermediate Graph / generator). Must stay
# on the Python fallback — proves the plugin fails closed rather than guessing.
def raw_spelling(edges: EdgeListI64) -> ComponentList:
    return list(nx.connected_components(nx.from_edgelist(edges)))
"""


@pytest.fixture(scope="module")
def project(tmp_path_factory: pytest.TempPathFactory) -> CertifiedProject:
    root = tmp_path_factory.mktemp("nx_certification")
    (root / "rextio.toml").write_text(
        '[rust]\nbuild_tool = "cargo"\n\n[plugins]\nenabled = ["rextio-networkx"]\n',
        encoding="utf-8",
    )
    package = root / "src" / "nx_app"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "kernels.py").write_text(KERNELS, encoding="utf-8")
    return build_certification_project(root)


def _components_equal(left: object, right: object) -> bool:
    """List-order-sensitive, set-order-insensitive equality for list[set[int]]."""
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(a == b for a, b in zip(left, right))
    return default_equals(left, right)


def _args_unmutated(left: object, right: object) -> bool:
    return left == right


def _route_of(project: CertifiedProject, qualname: str) -> tuple[str, str]:
    report = json.loads(
        (project.project_root / ".rextio" / "reports" / "check.json").read_text(encoding="utf-8")
    )
    for module in report["modules"]:
        for function in module["functions"]:
            if function["qualname"] == qualname:
                return function["route"], function["native_status"]
    raise AssertionError(f"{qualname} not found in check.json")


def test_native_route_was_selected(project: CertifiedProject) -> None:
    # Prove the covered route is native-plugin (not native-direct, not fallback)
    # and the plugin actually claimed the petgraph route.
    route, status = _route_of(project, "nx_app.kernels.components")
    assert route == "native-plugin:rextio-networkx"
    assert status == "accepted"


def test_generated_crate_uses_petgraph_helper(project: CertifiedProject) -> None:
    lib_rs = (project.project_root / ".rextio" / "generated" / "rust" / "src" / "lib.rs").read_text(
        encoding="utf-8"
    )
    assert "__rxtnx_connected_components_i64" in lib_rs
    assert "petgraph::unionfind::UnionFind" in lib_rs


def test_raw_spelling_is_not_natively_served(project: CertifiedProject) -> None:
    # The raw list(nx.connected_components(nx.from_edgelist(edges))) spelling
    # fails closed to the Python fallback; the kit refuses to certify it.
    route, status = _route_of(project, "nx_app.kernels.raw_spelling")
    assert route == "fallback-python"
    assert status in {"rejected", "not-candidate"}
    with pytest.raises(CertificationError, match="not natively served"):
        project.equivalence_checker("nx_app.kernels.raw_spelling")


@pytest.mark.parametrize("case", sorted(COVERED_EDGE_LISTS), ids=sorted(COVERED_EDGE_LISTS))
def test_native_matches_fallback_for_covered_cases(project: CertifiedProject, case: str) -> None:
    check = project.equivalence_checker(
        "nx_app.kernels.components",
        equals=_components_equal,
        args_equals=_args_unmutated,
    )
    edges = COVERED_EDGE_LISTS[case]
    result = check(edges)
    # The kit already compared both legs; assert type and value against NetworkX.
    assert isinstance(result, list)
    assert all(isinstance(component, set) for component in result)
    assert result == list(nx.connected_components(nx.from_edgelist(edges)))


def test_native_result_type_is_list_of_sets(project: CertifiedProject) -> None:
    check = project.equivalence_checker(
        "nx_app.kernels.components", equals=_components_equal, args_equals=_args_unmutated
    )
    result = check([(0, 1), (1, 2), (10, 11), (5, 5)])
    assert isinstance(result, list)
    assert result == [{0, 1, 2}, {10, 11}, {5}]
    assert all(type(component) is set for component in result)


def test_bool_labels_fail_closed_at_native_boundary(project: CertifiedProject) -> None:
    # A Python bool is an int subclass. If the native boundary extracted the edge
    # list by value it would silently coerce True/False to 1/0, so the native leg
    # would diverge from the NetworkX fallback in element TYPE (int vs bool) while
    # still comparing equal through set ==. The boundary refuses bool with a
    # TypeError instead: a deterministic, fail-closed type-contract violation, NOT
    # a silent coercion and NOT an analysis-time RXTP rejection (the call is
    # native-claimed; the rejection happens at the runtime boundary). The kit runs
    # both legs and reports the native leg's exception, proving it fired natively.
    check = project.equivalence_checker(
        "nx_app.kernels.components", equals=_components_equal, args_equals=_args_unmutated
    )
    for edges in ([(True, False)], [(True, 2), (2, 0)], [(0, 1), (1, True)]):
        with pytest.raises(CertificationError, match=r"native raised TypeError"):
            check(edges)
    # The fallback keeps bool identity (bool != int by type), so the divergence
    # the native boundary refuses to certify is real, not hypothetical.
    fallback = list(nx.connected_components(nx.from_edgelist([(True, False)])))
    assert fallback == [{False, True}]
    assert all(type(node) is bool for node in fallback[0])


def test_out_of_i64_labels_fail_closed_at_native_boundary(project: CertifiedProject) -> None:
    # A node label outside signed i64 has no native representation; PyO3 raises
    # OverflowError at the boundary. Deterministic, fail-closed type-contract
    # violation (the EdgeListI64 annotation promises signed i64), not an
    # analysis-time RXTP reject and not a silent truncation.
    check = project.equivalence_checker(
        "nx_app.kernels.components", equals=_components_equal, args_equals=_args_unmutated
    )
    for out_of_range in (2**63, -(2**63) - 1):
        with pytest.raises(CertificationError, match=r"native raised OverflowError"):
            check([(out_of_range, 0)])
    # The fallback handles arbitrary-precision ints, so the divergence is real.
    assert list(nx.connected_components(nx.from_edgelist([(2**63, 0)]))) == [{0, 2**63}]


@st.composite
def edge_lists(draw: st.DrawFn) -> list[tuple[int, int]]:
    label = st.integers(min_value=-64, max_value=64)
    return draw(st.lists(st.tuples(label, label), max_size=24))


@settings(max_examples=40, deadline=None)
@given(edges=edge_lists())
def test_hypothesis_native_matches_fallback(
    project: CertifiedProject, edges: list[tuple[int, int]]
) -> None:
    check = project.equivalence_checker(
        "nx_app.kernels.components", equals=_components_equal, args_equals=_args_unmutated
    )
    result = check(edges)
    assert result == list(nx.connected_components(nx.from_edgelist(edges)))
