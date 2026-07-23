"""Coverage declaration for the rextio-networkx plugin surface."""

from __future__ import annotations

from rextio.plugins.api import CoverageDecl

# ``packages`` drives the ``plugin`` import policy and the RXT091 hint; the claim
# pass routes sites by covered package + operand-type ownership. ``networkx`` is
# the accelerated library; ``rextio_networkx`` is where the covered adapter
# symbol lives. ``symbols`` lists only directly lowerable adapter targets —
# raw NetworkX spellings (e.g. ``networkx.from_edgelist``) are not lowerable
# and stay fallback-only (RXTP-NETWORKX-019).
COVERAGE = CoverageDecl(
    packages=("networkx", "rextio_networkx"),
    modules=("networkx", "rextio_networkx"),
    symbols=(
        "rextio_networkx.connected_components_from_edgelist",
        "rextio_networkx.graph_from_edgelist",
        "rextio_networkx.bfs_edges",
        "rextio_networkx.single_source_shortest_path_lengths",
        "rextio_networkx.weighted_graph_from_edgelist",
        "rextio_networkx.dijkstra_path_lengths",
    ),
)
