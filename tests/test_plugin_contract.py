"""Contract tests for plugin metadata, rules, types, and crate pins.

Assert the plugin registers cleanly under the core loader and that its
protocol-v2 surface matches the tooling contract: namespaced rule ids and
diagnostic codes, a verified native rule, the emitted rejection code, the
plugin type vocabulary, and the exact ``petgraph`` crate pin. A clean
registration surface is the WP-2 integration contract (traversal modules can be
added without restructuring the package).
"""

from __future__ import annotations

import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from rextio.config.schema import PluginConfig
from rextio.plugins.api import (
    PLUGIN_DIAGNOSTIC_CODE_PATTERN,
    CoverageDecl,
    CrateDependency,
    PluginType,
    RuleRecord,
)
from rextio.plugins.loader import load_plugin_registry
from rextio.targets.models import TargetSpec

from rextio_networkx.claim.components import CC_RULE
from rextio_networkx.host_compat import supports_plugin_api
from rextio_networkx.plugin import PLUGIN_ID, RextioNetworkxPlugin, plugin


def _registry():
    return load_plugin_registry(PluginConfig(enabled=[PLUGIN_ID]), TargetSpec(language="rust"))


def test_entry_point_factory_returns_plugin() -> None:
    obj = plugin()
    assert isinstance(obj, RextioNetworkxPlugin)
    assert obj.plugin_id == PLUGIN_ID
    assert obj.api_version == "1.3"
    assert not hasattr(obj, "artifact_capabilities")


@pytest.mark.parametrize("version", ["1.3", "1.4", "1.99"])
def test_provider_accepts_same_major_hosts_from_api_13(version: str) -> None:
    assert supports_plugin_api(version)


@pytest.mark.parametrize("version", ["1.2", "2.0", "1.3.0", "dev", None])
def test_provider_rejects_incompatible_or_ambiguous_host_apis(version: object) -> None:
    assert not supports_plugin_api(version)


def test_registry_loads_and_lowering_is_provided() -> None:
    reg = _registry()
    ids = {p.id for p in reg.active}
    assert PLUGIN_ID in ids
    active = next(p for p in reg.active if p.id == PLUGIN_ID)
    assert active.lowering_provided is True
    assert active.rules_provided is True
    assert active.api_version == "1.3"
    assert {b.plugin_id for b in reg.providers} == {PLUGIN_ID}


def test_covers_declares_networkx_and_adapter() -> None:
    coverage = plugin().covers()
    assert isinstance(coverage, CoverageDecl)
    assert "networkx" in coverage.packages
    assert "rextio_networkx" in coverage.packages
    assert "rextio_networkx.connected_components_from_edgelist" in coverage.symbols
    assert "rextio_networkx.connected_components" in coverage.symbols
    assert "rextio_networkx.bfs_edges" in coverage.symbols
    assert "rextio_networkx.has_path" in coverage.symbols
    assert "rextio_networkx.shortest_path_length" in coverage.symbols
    assert "rextio_networkx.single_source_shortest_path_lengths" in coverage.symbols
    assert "rextio_networkx.dijkstra_path_lengths" in coverage.symbols


def test_coverage_symbols_are_only_lowerable_adapters() -> None:
    """Raw NetworkX spellings must not be advertised as directly lowerable."""
    coverage = plugin().covers()
    assert "networkx.from_edgelist" not in coverage.symbols
    assert "networkx.connected_components" not in coverage.symbols
    assert set(coverage.symbols) == {
        "rextio_networkx.connected_components_from_edgelist",
        "rextio_networkx.connected_components",
        "rextio_networkx.graph_from_edgelist",
        "rextio_networkx.bfs_edges",
        "rextio_networkx.has_path",
        "rextio_networkx.shortest_path_length",
        "rextio_networkx.single_source_shortest_path_lengths",
        "rextio_networkx.weighted_graph_from_edgelist",
        "rextio_networkx.dijkstra_path_lengths",
    }


def test_rule_records_are_namespaced_and_well_formed() -> None:
    records = plugin().describe(None)
    assert records, "expected at least one rule record"
    codes: set[str] = set()
    for record in records:
        assert isinstance(record, RuleRecord)
        assert record.id.startswith("rextio-networkx/")
        assert record.provider == "rextio-networkx"
        if record.diagnostic_code is not None:
            match = PLUGIN_DIAGNOSTIC_CODE_PATTERN.match(record.diagnostic_code)
            assert match is not None
            assert match.group(1) == "NETWORKX"
            assert record.diagnostic_code not in codes, "duplicate diagnostic code"
            codes.add(record.diagnostic_code)


def test_native_rule_is_verified_and_matches_claim() -> None:
    records = {r.id: r for r in plugin().describe(None)}
    native = records[CC_RULE]
    assert native.outcome == "native"
    assert native.verified is True
    assert native.scope.kind == "call"
    assert native.diagnostic_code == "RXTP-NETWORKX-001"


def test_rejection_code_is_declared_by_a_rule_record() -> None:
    codes = {r.diagnostic_code for r in plugin().describe(None)}
    assert "RXTP-NETWORKX-010" in codes


def test_type_vocabulary_keys_and_annotations() -> None:
    types = plugin().type_vocabulary()
    assert {t.key for t in types} == {
        "rextio-networkx/node-i64",
        "rextio-networkx/edgelist-i64",
        "rextio-networkx/weighted-edgelist-i64-f64",
        "rextio-networkx/component-list",
        "rextio-networkx/bfs-edges-i64",
        "rextio-networkx/dijkstra-lengths-i64",
        "rextio-networkx/shortest-path-lengths-i64",
        "rextio-networkx/graph-i64",
        "rextio-networkx/weighted-graph-i64-f64",
    }
    spellings: set[str] = set()
    for plugin_type in types:
        assert isinstance(plugin_type, PluginType)
        assert plugin_type.key.startswith("rextio-networkx/")
        assert plugin_type.annotations
        spellings.update(plugin_type.annotations)
    assert spellings == {
        "rextio_networkx.NodeI64",
        "rextio_networkx.EdgeListI64",
        "rextio_networkx.WeightedEdgeListI64F64",
        "rextio_networkx.ComponentList",
        "rextio_networkx.BfsEdgesI64",
        "rextio_networkx.DijkstraLengthsI64",
        "rextio_networkx.ShortestPathLengthsI64",
        "rextio_networkx.GraphI64",
        "rextio_networkx.WeightedGraphI64F64",
    }


def test_only_graph_types_are_resident_and_raw_inputs_receive_pyany() -> None:
    types = {plugin_type.key: plugin_type for plugin_type in plugin().type_vocabulary()}
    assert {key for key, value in types.items() if value.is_resident} == {
        "rextio-networkx/graph-i64",
        "rextio-networkx/weighted-graph-i64-f64",
    }
    for key in (
        "rextio-networkx/node-i64",
        "rextio-networkx/edgelist-i64",
        "rextio-networkx/weighted-edgelist-i64-f64",
    ):
        conversion = types[key].conversion
        assert conversion is not None
        assert conversion.param_rust == "pyo3::Bound<'py, pyo3::types::PyAny>"


def test_public_dependency_requires_released_api_13_core() -> None:
    pyproject = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text())
    dependencies = pyproject["project"]["dependencies"]
    core = next(item for item in dependencies if item.startswith("rextio"))
    assert core == "rextio>=0.1.3,<0.2"
    assert "git+" not in core
    assert "rextio-core-next" not in core


def test_private_do_not_upload_classifier_is_absent() -> None:
    """Public alpha is intended for PyPI; do not block upload with this classifier."""
    pyproject = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text())
    assert "Private :: Do Not Upload" not in pyproject["project"]["classifiers"]
    assert pyproject["project"]["name"] == "rextio-networkx"


def test_crate_dependency_is_exact_petgraph_pin() -> None:
    deps = plugin().crate_dependencies()
    assert deps == (CrateDependency(name="petgraph", version="=0.6.5"),)


def test_registry_binds_types_and_crates() -> None:
    reg = _registry()
    assert {b.plugin_type.key for b in reg.types} == {
        "rextio-networkx/node-i64",
        "rextio-networkx/edgelist-i64",
        "rextio-networkx/weighted-edgelist-i64-f64",
        "rextio-networkx/component-list",
        "rextio-networkx/bfs-edges-i64",
        "rextio-networkx/dijkstra-lengths-i64",
        "rextio-networkx/shortest-path-lengths-i64",
        "rextio-networkx/graph-i64",
        "rextio-networkx/weighted-graph-i64-f64",
    }
    assert [(b.dependency.name, b.dependency.version) for b in reg.crate_dependencies] == [
        ("petgraph", "=0.6.5")
    ]


def test_lower_guard_survives_optimized_interpreter() -> None:
    # The covered lower-time invariant uses an explicit ValueError, not assert,
    # so it stays active under `python -O` (PYTHONOPTIMIZE strips asserts). This
    # runs a real optimized subprocess and asserts the guard still fires.
    program = (
        "from rextio.plugins.api import ClaimSite, LoweringContext\n"
        "from rextio_networkx.claim.components import CC_RULE, CC_TARGET\n"
        "from rextio_networkx.diagnostics import COMPONENT_LIST, EDGELIST_I64\n"
        "from rextio_networkx.lower import lower\n"
        "site = ClaimSite(kind='call', target=CC_TARGET, operand_types=(EDGELIST_I64,),\n"
        "                 file_path='', line=0, column=0, rule_id=CC_RULE, result_type=COMPONENT_LIST)\n"
        "ctx = LoweringContext(operands=('a', 'b'), target_language='rust', fresh_name=lambda p: p)\n"
        "try:\n"
        "    lower(site, ctx)\n"
        "except ValueError:\n"
        "    print('guard-fired')\n"
        "else:\n"
        "    raise SystemExit('guard did not fire under -O')\n"
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


def test_lower_metadata_contract_survives_optimized_interpreter() -> None:
    """A forged result type must still fail closed when Python assertions vanish."""
    program = (
        "from rextio.plugins.api import ClaimSite, LoweringContext\n"
        "from rextio_networkx.claim.components import CC_RULE, CC_TARGET\n"
        "from rextio_networkx.diagnostics import EDGELIST_I64\n"
        "from rextio_networkx.lower import lower\n"
        "site = ClaimSite(kind='call', target=CC_TARGET, operand_types=(EDGELIST_I64,),\n"
        "                 file_path='', line=0, column=0, rule_id=CC_RULE,\n"
        "                 result_type='rextio-networkx/forged')\n"
        "ctx = LoweringContext(operands=('edges',), target_language='rust', fresh_name=lambda p: p)\n"
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
                [
                    str(Path(__file__).parents[1] / "src"),
                    os.environ.get("PYTHONPATH", ""),
                ]
            ),
        },
    )
    assert "guard-fired" in completed.stdout
