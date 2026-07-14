"""Coverage declaration for the rextio-networkx plugin surface."""

from __future__ import annotations

from rextio.plugins.api import CoverageDecl

# ``packages`` drives the ``plugin`` import policy and the RXT091 hint; the claim
# pass routes sites by covered package + operand-type ownership. ``networkx`` is
# the accelerated library; ``rextio_networkx`` is where the covered adapter
# symbol lives. ``symbols`` is DESCRIPTIVE (it appears in the capability
# manifest): only ``rextio_networkx.connected_components_from_edgelist`` is
# actually claimed; the raw ``networkx.from_edgelist`` / ``connected_components``
# spelling is documented as an uncovered API (RXTP-NETWORKX-019) that stays on
# the Python fallback.
COVERAGE = CoverageDecl(
    packages=("networkx", "rextio_networkx"),
    modules=("networkx", "rextio_networkx"),
    symbols=(
        "rextio_networkx.connected_components_from_edgelist",
        "networkx.from_edgelist",
        "networkx.connected_components",
    ),
)
