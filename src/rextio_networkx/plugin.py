"""The rextio-networkx plugin object and entry-point factory.

Implements plugin API 1.3, including resident petgraph values that chain from
typed constructors into BFS/Dijkstra without a Python graph round trip.  The
module itself never imports NetworkX; fallback adapters do so lazily when
called.

Claim and lower logic live in :mod:`rextio_networkx.claim` and
:mod:`rextio_networkx.lower`; this module is a thin facade.

Import-time contract: this module (and therefore the package root) must load
without analyzer/config/plugin modules from core. Core types are imported
lazily inside the methods that only run under a full analyzer/plugin host.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rextio_networkx.__about__ import __version__

if TYPE_CHECKING:
    from rextio.config.schema import RextioConfig
    from rextio.plugins.api import (
        ClaimResult,
        ClaimSite,
        CoverageDecl,
        CrateDependency,
        LoweredExpr,
        LoweringContext,
        PluginType,
        RuleRecord,
    )
    from rextio.plugins.models import RextioPlugin

PLUGIN_ID = "rextio-networkx"

# Re-export for existing test and internal imports.
__all__ = ["PLUGIN_ID", "RextioNetworkxPlugin", "plugin"]


class RextioNetworkxPlugin:
    """Plugin API 1.3 provider for exact narrow NetworkX routes."""

    plugin_id = PLUGIN_ID
    api_version = "1.3"

    def to_rextio_plugin(self) -> RextioPlugin:
        """Return the v1 metadata Rextio core registers this plugin under."""
        from rextio.plugins.models import RextioPlugin

        from rextio_networkx.rules import COVERAGE

        return RextioPlugin(
            id=PLUGIN_ID,
            name=f"NetworkX to petgraph (rextio-networkx {__version__})",
            source_language="python",
            target_language="rust",
            packages=COVERAGE.packages,
        )

    def covers(self) -> CoverageDecl:
        """Return the packages, modules, and symbols this plugin covers."""
        from rextio_networkx.rules import COVERAGE

        return COVERAGE

    def describe(self, config: RextioConfig) -> tuple[RuleRecord, ...]:
        """Return the rule records for the resolved project configuration.

        The rule surface is currently config-independent; the parameter is part
        of the protocol so future rules can vary with (for example) import
        policies or target versions.
        """
        from rextio_networkx.rules import networkx_rule_records

        del config
        return networkx_rule_records()

    def type_vocabulary(self) -> tuple[PluginType, ...]:
        """Return the annotation vocabulary this plugin adds to the analyzer."""
        from rextio_networkx.plugin_types import plugin_types

        return plugin_types()

    def claim(self, site: ClaimSite, config: RextioConfig) -> ClaimResult:
        """Decide, at analysis time, whether this plugin lowers the site.

        Deterministic by contract: the decision is a pure function of
        ``(site.kind, site.target, site.operand_types, site.keywords)``. The
        exact component/traversal shapes are :class:`~rextio.plugins.api.Claimed`.
        Every recognized traversal miss is :class:`~rextio.plugins.api.Rejected`
        with RXTP-NETWORKX-020 guidance; unrelated targets are
        :class:`~rextio.plugins.api.NotCovered`.
        """
        from rextio_networkx.claim import claim as claim_site

        return claim_site(site, config)

    def lower(self, claimed: ClaimSite, ctx: LoweringContext) -> LoweredExpr:
        """Emit the Rust expression for a previously claimed site.

        Expressions construct or immutably borrow real resident petgraph values;
        support items travel in ``helpers`` and are deduplicated by exact text.
        """
        from rextio_networkx.lower import lower as lower_site

        return lower_site(claimed, ctx)

    def crate_dependencies(self) -> tuple[CrateDependency, ...]:
        """Return the pinned crates the generated helper depends on."""
        from rextio.plugins.api import CrateDependency

        return (CrateDependency(name="petgraph", version="=0.6.5"),)


def plugin() -> RextioNetworkxPlugin:
    """Entry-point factory for the ``rextio.plugins`` group."""
    return RextioNetworkxPlugin()
