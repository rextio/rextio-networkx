"""Contract tests for plugin metadata, rules, types, and crate pins.

Assert the plugin registers cleanly under the core loader and that its
protocol-v2 surface matches the tooling contract: namespaced rule ids and
diagnostic codes, a verified native rule, the emitted rejection code, the
plugin type vocabulary, and the exact ``petgraph`` crate pin. A clean
registration surface is the WP-2 integration contract (traversal modules can be
added without restructuring the package).
"""

from __future__ import annotations

import subprocess
import sys

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
from rextio_networkx.plugin import PLUGIN_ID, RextioNetworkxPlugin, plugin


def _registry():
    return load_plugin_registry(PluginConfig(enabled=[PLUGIN_ID]), TargetSpec(language="rust"))


def test_entry_point_factory_returns_plugin() -> None:
    obj = plugin()
    assert isinstance(obj, RextioNetworkxPlugin)
    assert obj.plugin_id == PLUGIN_ID
    assert obj.api_version == "1.2"


def test_registry_loads_and_lowering_is_provided() -> None:
    reg = _registry()
    ids = {p.id for p in reg.active}
    assert PLUGIN_ID in ids
    active = next(p for p in reg.active if p.id == PLUGIN_ID)
    assert active.lowering_provided is True
    assert active.rules_provided is True
    assert active.api_version == "1.2"
    assert {b.plugin_id for b in reg.providers} == {PLUGIN_ID}


def test_covers_declares_networkx_and_adapter() -> None:
    coverage = plugin().covers()
    assert isinstance(coverage, CoverageDecl)
    assert "networkx" in coverage.packages
    assert "rextio_networkx" in coverage.packages
    assert "rextio_networkx.connected_components_from_edgelist" in coverage.symbols


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
        "rextio-networkx/edgelist-i64",
        "rextio-networkx/component-list",
    }
    spellings: set[str] = set()
    for plugin_type in types:
        assert isinstance(plugin_type, PluginType)
        assert plugin_type.key.startswith("rextio-networkx/")
        assert plugin_type.annotations
        spellings.update(plugin_type.annotations)
    assert spellings == {
        "rextio_networkx.EdgeListI64",
        "rextio_networkx.ComponentList",
    }


def test_crate_dependency_is_exact_petgraph_pin() -> None:
    deps = plugin().crate_dependencies()
    assert deps == (CrateDependency(name="petgraph", version="=0.6.5"),)


def test_registry_binds_types_and_crates() -> None:
    reg = _registry()
    assert {b.plugin_type.key for b in reg.types} == {
        "rextio-networkx/edgelist-i64",
        "rextio-networkx/component-list",
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
    )
    assert "guard-fired" in completed.stdout
