"""The rextio-networkx plugin object and entry-point factory.

Implements plugin API 1.2 (``rextio.plugins.api.RextioLoweringPlugin``): the
protocol-v2 describe/covers surface plus the lowering members — the annotation
vocabulary, the deterministic claim pass, expression lowering, and the pinned
``petgraph`` crate dependency. The plugin module itself never imports NetworkX;
the public/fallback adapter (:mod:`rextio_networkx`) imports it lazily on call.

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
    """Plugin API 1.2: describes AND lowers the covered edge-list route to Rust."""

    plugin_id = PLUGIN_ID
    api_version = "1.2"

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
        covered adapter call with a typed :data:`~rextio_networkx.EdgeListI64`
        argument is :class:`~rextio.plugins.api.Claimed`; the same call with a
        known-but-unsupported argument type is
        :class:`~rextio.plugins.api.Rejected` with RXTP-NETWORKX-010 guidance;
        everything else (unresolved operands, wrong arity, keywords, other
        targets) is :class:`~rextio.plugins.api.NotCovered`.
        """
        from rextio_networkx.claim import claim as claim_site

        return claim_site(site, config)

    def lower(self, claimed: ClaimSite, ctx: LoweringContext) -> LoweredExpr:
        """Emit the Rust expression for a previously claimed site.

        The emitted expression calls one deterministic ``petgraph`` helper and
        ends with ``?``; the helper ``fn`` travels in ``helpers`` and is
        deduplicated by exact text in core codegen.
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
