"""rextio-networkx: a private incubator Rextio plugin for NetworkX.

Implements Rextio plugin API 1.2 (``rextio.plugins.api``): the plugin
self-describes its rules AND lowers one covered construction route — a typed
undirected integer edge list converted once to an immutable local ``petgraph``
graph, with connected components computed in Rust — to a native PyO3 extension,
with a pinned ``petgraph`` crate injection and the annotation vocabulary
(:data:`EdgeListI64` / :data:`ComponentList`). The lowering is certified
against CPython NetworkX 3.5 with the core plugin certification kit
(``rextio.plugins.testing``).

The minimum reliable public surface is the explicit adapter
:func:`connected_components_from_edgelist`, whose ordinary Python
implementation delegates to pinned NetworkX 3.5. NetworkX 3.5 is therefore a
real (pinned) runtime dependency of this package. It is imported *lazily* — on
the adapter call, not at package import — so ``import rextio_networkx`` still
pulls in neither NetworkX nor the Rextio analyzer: the annotation aliases are
plain typing aliases and the plugin facade defers every core import. That keeps
package import cheap while guaranteeing the fallback leg's NetworkX is present.
"""

from __future__ import annotations

from rextio_networkx.__about__ import __version__
from rextio_networkx.plugin import RextioNetworkxPlugin, plugin

# --- User annotation vocabulary -------------------------------------------
# Pure typing aliases: no NetworkX, no Rextio, no runtime cost. They spell the
# covered native surface so the analyzer resolves parameter/return types to the
# plugin's registered plugin-type keys (see ``rextio_networkx.plugin_types``).
#
# ``EdgeListI64`` is an undirected simple-graph edge list of signed 64-bit
# integer node labels; ``ComponentList`` is the exact ``list[set[int]]`` result
# of ``list(networkx.connected_components(...))``.
EdgeListI64 = list[tuple[int, int]]
ComponentList = list[set[int]]


def connected_components_from_edgelist(edges: EdgeListI64) -> ComponentList:
    """Return the connected components of the graph built from ``edges``.

    This is the explicit public/fallback adapter and the single covered native
    construction route. Its ordinary Python implementation delegates to pinned
    NetworkX 3.5, reproducing exactly::

        list(networkx.connected_components(networkx.from_edgelist(edges)))

    ``edges`` is an undirected simple-graph edge list of signed integer node
    labels: ``[(u0, v0), (u1, v1), ...]``. Insertion order, duplicate edges,
    self-loops, and disconnected or empty edge lists are all covered. Component
    list order follows NetworkX (each component ordered by the first insertion
    of one of its nodes); set element order is not observable through equality.

    Edge-only input intentionally cannot represent an isolated node that never
    appears in an edge — pass such nodes through NetworkX directly.

    When Rextio compiles a function that calls this adapter with a typed
    :data:`EdgeListI64` argument, the call lowers to a native ``petgraph``
    route instead; both legs return an identical ``list[set[int]]`` for
    in-contract signed-i64 labels. A Python ``bool`` label or an integer outside
    the signed i64 range is rejected at the native boundary (``TypeError`` /
    ``OverflowError``) rather than silently coerced.

    NetworkX 3.5 is a pinned runtime dependency, imported lazily on call so
    importing ``rextio_networkx`` stays cheap; the call raises
    :class:`ModuleNotFoundError` only if NetworkX has been removed.
    """
    import networkx as nx

    return list(nx.connected_components(nx.from_edgelist(edges)))


__all__ = [
    "ComponentList",
    "EdgeListI64",
    "RextioNetworkxPlugin",
    "__version__",
    "connected_components_from_edgelist",
    "plugin",
]
