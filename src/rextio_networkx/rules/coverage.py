"""Coverage declaration for the rextio-networkx plugin surface."""

from __future__ import annotations

from rextio.plugins.api import CoverageDecl

# ``packages`` drives the ``plugin`` import policy and the RXT091 hint; the claim
# pass routes sites by covered package + operand-type ownership. ``networkx`` is
# the accelerated library; ``rextio_networkx`` is where the covered adapter
# symbol lives. ``symbols`` is DESCRIPTIVE (it appears in the capability
# manifest): the explicit rextio_networkx adapters are claimed; raw NetworkX
# spellings are documented as uncovered (RXTP-NETWORKX-019) and stay fallback.
COVERAGE = CoverageDecl(
    packages=("networkx", "rextio_networkx"),
    modules=("networkx", "rextio_networkx"),
    symbols=(
        "rextio_networkx.connected_components_from_edgelist",
        "rextio_networkx.graph_from_edgelist",
        "rextio_networkx.bfs_edges",
        "rextio_networkx.weighted_graph_from_edgelist",
        "rextio_networkx.dijkstra_path_lengths",
        "networkx.from_edgelist",
        "networkx.connected_components",
    ),
)
