"""Real-Cargo proof for ordered resident BFS and Dijkstra product routes."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
from copy import deepcopy
from pathlib import Path
from types import ModuleType

import networkx as nx
import pytest

import rextio
from rextio.build.cargo_builder import build_native_extension_with_cargo
from rextio.codegen.rust.cargo import render_cargo_config_toml, render_cargo_toml
from rextio.codegen.rust.generator import generate_rust_module
from rextio.ir.nodes import BlockIR, FunctionIR, ModuleIR, NameIR, ParamIR, ReturnIR
from rextio.ir.types import RxtPluginType
from rextio.plugins.api import PLUGIN_API_VERSION
from rextio.plugins.testing import CertifiedProject, EquivalenceChecker, build_certification_project
from rextio_networkx.diagnostics import EDGELIST_I64, NODE_I64, WEIGHTED_EDGELIST_I64_F64
from rextio_networkx.plugin_types import plugin_type

CORE_ROOT = Path("/Volumes/Data/workspace/rextio/rextio-core-next").resolve()
CORE_SHA = "2bd1d1da0cf59e97d1659606bcb1ec12491e032c"

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
        ["git", "-C", str(CORE_ROOT), "rev-parse", "HEAD"],
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
    assert source.count("fn __rxtnx_edgelist_i64_to_py") == 1
    assert source.count("fn __rxtnx_weighted_edgelist_i64_f64_to_py") == 1
    assert "wrap_pyfunction!(nx_traversal_app__kernels__resident_escape" not in source


def _signature_ir_type(key: str) -> RxtPluginType:
    declared = plugin_type(key)
    conversion = declared.conversion
    assert conversion is not None
    return RxtPluginType(
        key=declared.key,
        native_rust=declared.rust_type,
        param_rust=conversion.param_rust,
        param_expr=conversion.param_expr,
        return_rust=conversion.return_rust,
        return_expr=conversion.return_expr,
        uses=declared.uses,
        helpers=declared.helpers,
    )


def _signature_roundtrip(name: str, key: str, param: str) -> FunctionIR:
    value_type = _signature_ir_type(key)
    return FunctionIR(
        name=name,
        qualname=f"nx_signature.{name}",
        module_name="nx_signature",
        params=[ParamIR(name=param, type=value_type)],
        return_type=value_type,
        body=BlockIR(statements=[ReturnIR(NameIR(param))]),
        plugin_lowered=True,
    )


@pytest.fixture(scope="module")
def signature_only_module(tmp_path_factory: pytest.TempPathFactory) -> ModuleType:
    """Compile zero-claim IR so signature support alone must close every symbol."""
    rust_dir = tmp_path_factory.mktemp("nx_signature_rust")
    rust_src = rust_dir / "src"
    rust_src.mkdir()
    python_dir = tmp_path_factory.mktemp("nx_signature_python")
    functions = [
        _signature_roundtrip("node_roundtrip", NODE_I64, "source"),
        _signature_roundtrip("edgelist_roundtrip", EDGELIST_I64, "edges"),
        _signature_roundtrip(
            "weighted_edgelist_roundtrip",
            WEIGHTED_EDGELIST_I64_F64,
            "edges",
        ),
    ]
    types_by_key = {
        key: _signature_ir_type(key) for key in (NODE_I64, EDGELIST_I64, WEIGHTED_EDGELIST_I64_F64)
    }
    source = generate_rust_module(
        ModuleIR(functions=functions),
        plugin_types_by_key=types_by_key,
    )
    # There are deliberately zero PluginClaimIR nodes: the signature is the
    # sole support authority, while each body simply exercises the conversion
    # pair. This bypasses source-level mutable-alias rejection only inside the
    # codegen regression; the public analyzer's aliasing guard remains intact.
    assert "__rxtnx_edgelist_i64_to_py" in source
    assert "__rxtnx_weighted_edgelist_i64_f64_to_py" in source
    (rust_dir / "Cargo.toml").write_text(render_cargo_toml(), encoding="utf-8")
    cargo_config = rust_dir / ".cargo"
    cargo_config.mkdir()
    (cargo_config / "config.toml").write_text(render_cargo_config_toml(), encoding="utf-8")
    (rust_src / "lib.rs").write_text(source, encoding="utf-8")
    built = build_native_extension_with_cargo(rust_dir, python_dir)
    assert built.status == "built", built.message + "\n" + built.stderr
    assert built.installed_path is not None
    spec = importlib.util.spec_from_file_location("_rextio_native", built.installed_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("source", [-(2**63), -7, 0, 2**63 - 1])
def test_claimless_node_signature_roundtrip(signature_only_module: ModuleType, source: int) -> None:
    actual = signature_only_module.nx_signature__node_roundtrip(source)
    assert type(actual) is int
    assert actual == source


@pytest.mark.parametrize(
    "edges",
    [
        [],
        [(0, 1), (-5, 9), (2**63 - 1, -(2**63))],
        [(4, 1), (1, 4), (4, 4)],
    ],
)
def test_claimless_edgelist_signature_roundtrip(
    signature_only_module: ModuleType,
    edges: list[tuple[int, int]],
) -> None:
    actual = signature_only_module.nx_signature__edgelist_roundtrip(edges)
    assert type(actual) is list
    assert actual == edges
    assert all(type(edge) is tuple and len(edge) == 2 for edge in actual)
    assert all(type(node) is int for edge in actual for node in edge)


@pytest.mark.parametrize(
    "edges",
    [
        [],
        [(0, 1, -0.0), (-5, 9, 1.25), (2**63 - 1, -(2**63), 2.5)],
        [(4, 1, 3.0), (1, 4, 7.5), (4, 4, 0.0)],
    ],
)
def test_claimless_weighted_edgelist_signature_roundtrip(
    signature_only_module: ModuleType,
    edges: list[tuple[int, int, float]],
) -> None:
    actual = signature_only_module.nx_signature__weighted_edgelist_roundtrip(edges)
    assert type(actual) is list
    assert [(u, v, weight.hex()) for u, v, weight in actual] == [
        (u, v, weight.hex()) for u, v, weight in edges
    ]
    assert all(type(edge) is tuple and len(edge) == 3 for edge in actual)
    assert all(type(edge[0]) is int and type(edge[1]) is int for edge in actual)
    assert all(type(edge[2]) is float for edge in actual)


def _bfs_equal(left: object, right: object) -> bool:
    return type(left) is list and type(right) is list and left == right


def _dijkstra_signature(result: object) -> list[tuple[type, object, type, str]]:
    assert type(result) is dict
    return [
        (type(key), key, type(value), value.hex() if type(value) is float else str(value))
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


def _leg_error_signatures(
    checker: EquivalenceChecker,
    args: tuple[object, ...],
) -> tuple[
    tuple[type[BaseException], str, tuple[object, ...]],
    tuple[type[BaseException], str, tuple[object, ...]],
]:
    signatures = []
    for mode in ("native", "fallback"):
        (kind, value), _ = checker._run(mode, args)
        assert kind == "raised"
        assert isinstance(value, Exception)
        signatures.append(_signature(value))
    return signatures[0], signatures[1]


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
    expected_signature = (expected[0], expected[1], (expected[1],))
    native_signature, fallback_signature = _leg_error_signatures(checker, args)
    assert native_signature == expected_signature
    assert fallback_signature == expected_signature


def test_native_and_fallback_match_exact_missing_source_errors(project: CertifiedProject) -> None:
    bfs = project.equivalence_checker("nx_traversal_app.kernels.bfs_product")
    expected_bfs = (
        nx.NetworkXError,
        "The node -9 is not in the graph.",
        ("The node -9 is not in the graph.",),
    )
    native_bfs, fallback_bfs = _leg_error_signatures(bfs, ([], -9))
    assert native_bfs == expected_bfs
    assert fallback_bfs == expected_bfs

    dijkstra = project.equivalence_checker("nx_traversal_app.kernels.dijkstra_product")
    expected_dijkstra = (
        nx.NodeNotFound,
        "Node -9 not found in graph",
        ("Node -9 not found in graph",),
    )
    native_dijkstra, fallback_dijkstra = _leg_error_signatures(dijkstra, ([], -9))
    assert native_dijkstra == expected_dijkstra
    assert fallback_dijkstra == expected_dijkstra


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
