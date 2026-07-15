"""Real-Cargo proof for ordered resident BFS and Dijkstra product routes."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from copy import deepcopy
from pathlib import Path

import networkx as nx
import pytest

import rextio
from rextio.plugins.api import PLUGIN_API_VERSION
from rextio.plugins.testing import CertifiedProject, build_certification_project

CORE_ROOT = Path("/Volumes/Data/workspace/rextio/rextio-core-next").resolve()
CORE_SHA = "ac2b79d304f13abaaecaf7714f897574c3b6256f"

pytestmark = pytest.mark.skipif(
    shutil.which("cargo") is None,
    reason="real-cargo traversal proof requires cargo",
)

KERNELS = """
import rextio
from rextio_networkx import (
    BfsEdgesI64,
    ComponentList,
    DijkstraLengthsI64,
    EdgeListI64,
    GraphI64,
    NodeI64,
    WeightedEdgeListI64F64,
    bfs_edges,
    connected_components_from_edgelist,
    dijkstra_path_lengths,
    graph_from_edgelist,
    weighted_graph_from_edgelist,
)


def bfs_product(edges: EdgeListI64, source: NodeI64) -> BfsEdgesI64:
    return bfs_edges(graph_from_edgelist(edges), source)


def dijkstra_product(
    edges: WeightedEdgeListI64F64,
    source: NodeI64,
) -> DijkstraLengthsI64:
    return dijkstra_path_lengths(weighted_graph_from_edgelist(edges), source)


@rextio.native
def resident_escape(edges: EdgeListI64) -> GraphI64:
    return graph_from_edgelist(edges)


def materialized_consumer(edges: EdgeListI64) -> ComponentList:
    return connected_components_from_edgelist(edges)


@rextio.native
def resident_to_materialized(edges: EdgeListI64) -> ComponentList:
    graph = graph_from_edgelist(edges)
    return materialized_consumer(graph)
"""


def _core_sha() -> str:
    return subprocess.run(
        ["rtk", "git", "-C", str(CORE_ROOT), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


@pytest.fixture(scope="module")
def project(tmp_path_factory: pytest.TempPathFactory) -> CertifiedProject:
    assert _core_sha() == CORE_SHA
    assert PLUGIN_API_VERSION == "1.3"
    assert Path(rextio.__file__).resolve().is_relative_to(CORE_ROOT / "src")

    root = tmp_path_factory.mktemp("nx_traversal")
    (root / "rextio.toml").write_text(
        '[rust]\nbuild_tool = "cargo"\n\n[plugins]\nenabled = ["rextio-networkx"]\n',
        encoding="utf-8",
    )
    package = root / "src" / "nx_traversal_app"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "kernels.py").write_text(KERNELS, encoding="utf-8")
    built = build_certification_project(root)
    check_path = root / ".rextio" / "reports" / "check.json"
    provenance = {
        "core_sha": CORE_SHA,
        "plugin_api": PLUGIN_API_VERSION,
        "rextio_file": str(Path(rextio.__file__).resolve()),
        "check_json_sha256": hashlib.sha256(check_path.read_bytes()).hexdigest(),
    }
    (root / ".rextio" / "reports" / "wp2-provenance.json").write_text(
        json.dumps(provenance, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return built


def _functions(project: CertifiedProject) -> dict[str, dict[str, object]]:
    report = json.loads(
        (project.project_root / ".rextio" / "reports" / "check.json").read_text(encoding="utf-8")
    )
    return {
        function["qualname"]: function
        for module in report["modules"]
        for function in module["functions"]
    }


def test_routes_and_exact_rxt092_gates(project: CertifiedProject) -> None:
    functions = _functions(project)
    for name in ("bfs_product", "dijkstra_product"):
        function = functions[f"nx_traversal_app.kernels.{name}"]
        assert function["route"] == "native-plugin:rextio-networkx"
        assert function["native_status"] == "accepted"
    for name in ("resident_escape", "resident_to_materialized"):
        function = functions[f"nx_traversal_app.kernels.{name}"]
        assert function["route"] == "fallback-python"
        assert function["native_status"] == "rejected"
        assert function["rejection_codes"] == ["RXT092"]


def _function_body(source: str, rust_name: str) -> str:
    start = source.index(f"fn {rust_name}")
    next_function = source.find("\nfn ", start + 3)
    return source[start:] if next_function == -1 else source[start:next_function]


def test_generated_source_owns_petgraph_and_constructs_once(project: CertifiedProject) -> None:
    source = (project.project_root / ".rextio" / "generated" / "rust" / "src" / "lib.rs").read_text(
        encoding="utf-8"
    )
    assert "petgraph::graph::UnGraph<i64, ()>" in source
    assert "petgraph::graph::UnGraph<i64, f64>" in source
    bfs_body = _function_body(source, "nx_traversal_app__kernels__bfs_product")
    dijkstra_body = _function_body(source, "nx_traversal_app__kernels__dijkstra_product")
    assert bfs_body.count("__rxtnx_graph_from_edgelist_i64(&edges)") == 1
    assert dijkstra_body.count("__rxtnx_weighted_graph_from_edgelist_i64_f64(&edges)") == 1
    assert bfs_body.index("__rxtnx_parse_edgelist_i64(py, &edges)") < bfs_body.index(
        "__rxtnx_parse_source_i64(py, &source)"
    )
    assert dijkstra_body.index(
        "__rxtnx_parse_weighted_edgelist_i64_f64(py, &edges)"
    ) < dijkstra_body.index("__rxtnx_parse_source_i64(py, &source)")
    assert "__rxtnx_bfs_edges_i64(py, &" in bfs_body
    assert "__rxtnx_dijkstra_lengths_i64_f64(py, &" in dijkstra_body
    assert "wrap_pyfunction!(nx_traversal_app__kernels__resident_escape" not in source


def _bfs_equal(left: object, right: object) -> bool:
    return type(left) is list and type(right) is list and left == right


def _dijkstra_signature(result: object) -> list[tuple[int, type, str]]:
    assert type(result) is dict
    return [
        (key, type(value), value.hex() if type(value) is float else str(value))
        for key, value in result.items()
    ]


def _dijkstra_equal(left: object, right: object) -> bool:
    return _dijkstra_signature(left) == _dijkstra_signature(right)


BFS_CASES = [
    ([(0, 4), (0, 2), (0, 9), (0, 1)], 0),
    ([(0, 2), (0, 1), (2, 3), (1, 3)], 0),
    ([(4, 1), (2, 4), (1, 4), (4, 2), (2, 3)], 4),
    ([(7, 7), (7, 8), (8, 8), (8, 9)], 7),
    ([(0, 1), (10, 11), (11, 12)], 10),
    ([(-5, -2), (-2, 9), (100, 101)], -5),
    ([(2**63 - 1, -(2**63)), (0, 2**63 - 1)], 0),
]


@pytest.mark.parametrize(("edges", "source"), BFS_CASES)
def test_native_bfs_matches_fallback_and_exact_reference(
    project: CertifiedProject,
    edges: list[tuple[int, int]],
    source: int,
) -> None:
    before = deepcopy(edges)
    checker = project.equivalence_checker(
        "nx_traversal_app.kernels.bfs_product",
        equals=_bfs_equal,
        args_equals=lambda left, right: left == right,
    )
    actual = checker(edges, source)
    graph = nx.Graph()
    graph.add_edges_from(edges)
    assert actual == list(nx.bfs_edges(graph, source))
    assert all(type(edge) is tuple and all(type(node) is int for node in edge) for edge in actual)
    assert edges == before


DIJKSTRA_CASES = [
    ([(0, 1, 1.5), (1, 2, 2.25), (0, 2, 10.0)], 0),
    ([(0, 1, 9.0), (1, 0, 3.0), (0, 1, 5.0), (1, 2, 1.0)], 0),
    ([(0, 2, 1.0), (0, 1, 1.0), (2, 3, 1.0), (1, 4, 1.0)], 0),
    ([(0, 1, 10.0), (0, 2, 1.0), (2, 1, 1.0), (1, 3, 1.0)], 0),
    ([(0, 1, -0.0), (0, 2, 0.0), (1, 3, 0.0)], 0),
    ([(5, 5, 0.0), (5, 6, 2.0), (20, 21, 1.0)], 5),
    ([(0, 1, 1.0e308), (1, 2, 1.0e308)], 0),
    (
        [(0, 1, 1.0e308), (1, 3, 1.0e308), (0, 2, 1.7e308), (2, 3, 0.0)],
        0,
    ),
]


@pytest.mark.parametrize(("edges", "source"), DIJKSTRA_CASES)
def test_native_dijkstra_matches_fallback_order_types_and_hex(
    project: CertifiedProject,
    edges: list[tuple[int, int, float]],
    source: int,
) -> None:
    before = deepcopy(edges)
    checker = project.equivalence_checker(
        "nx_traversal_app.kernels.dijkstra_product",
        equals=_dijkstra_equal,
        args_equals=lambda left, right: left == right,
    )
    actual = checker(edges, source)
    graph = nx.Graph()
    graph.add_weighted_edges_from(edges)
    expected = nx.single_source_dijkstra_path_length(graph, source, weight="weight")
    assert _dijkstra_signature(actual) == _dijkstra_signature(expected)
    assert type(actual[source]) is int
    assert all(type(value) is float for key, value in actual.items() if key != source)
    assert edges == before


def _signature(error: BaseException) -> tuple[type[BaseException], str, tuple[object, ...]]:
    return type(error), str(error), error.args


@pytest.mark.parametrize(
    ("function", "args", "expected"),
    [
        (
            "bfs_product",
            ([(0, 1), (True, 2)], False),
            (TypeError, "rextio-networkx: edges[1][0] must be an exact int"),
        ),
        (
            "bfs_product",
            ([(0, 1)], 2**63),
            (OverflowError, "rextio-networkx: source is outside signed-i64 range"),
        ),
        (
            "dijkstra_product",
            ([(0, 1, 1.0), (1, 0, float("nan"))], False),
            (
                ValueError,
                "rextio-networkx: edges[1][2] must be a finite non-negative float",
            ),
        ),
        (
            "dijkstra_product",
            ([(0, 1, 1)], 0),
            (TypeError, "rextio-networkx: edges[0][2] must be an exact float"),
        ),
    ],
)
def test_native_and_fallback_match_exact_dynamic_errors(
    project: CertifiedProject,
    function: str,
    args: tuple[object, ...],
    expected: tuple[type[BaseException], str],
) -> None:
    checker = project.equivalence_checker(f"nx_traversal_app.kernels.{function}")
    with pytest.raises(expected[0]) as caught:
        checker(*args)
    assert _signature(caught.value) == (expected[0], expected[1], (expected[1],))


def test_native_and_fallback_match_exact_missing_source_errors(project: CertifiedProject) -> None:
    bfs = project.equivalence_checker("nx_traversal_app.kernels.bfs_product")
    with pytest.raises(nx.NetworkXError) as bfs_error:
        bfs([], -9)
    assert _signature(bfs_error.value) == (
        nx.NetworkXError,
        "The node -9 is not in the graph.",
        ("The node -9 is not in the graph.",),
    )

    dijkstra = project.equivalence_checker("nx_traversal_app.kernels.dijkstra_product")
    with pytest.raises(nx.NodeNotFound) as dijkstra_error:
        dijkstra([], -9)
    assert _signature(dijkstra_error.value) == (
        nx.NodeNotFound,
        "Node -9 not found in graph",
        ("Node -9 not found in graph",),
    )


def test_build_records_exact_core_and_petgraph_provenance(project: CertifiedProject) -> None:
    provenance = json.loads(
        (project.project_root / ".rextio" / "reports" / "wp2-provenance.json").read_text(
            encoding="utf-8"
        )
    )
    assert provenance["core_sha"] == CORE_SHA
    assert provenance["plugin_api"] == "1.3"
    assert Path(provenance["rextio_file"]).is_relative_to(CORE_ROOT / "src")
    build = json.loads(
        (project.project_root / ".rextio" / "reports" / "build.json").read_text(encoding="utf-8")
    )
    deps = build["plugin_crate_dependencies"]
    assert any(dep["name"] == "petgraph" and dep["version"] == "=0.6.5" for dep in deps)
