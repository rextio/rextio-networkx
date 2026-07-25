"""Rust helper-text generators for the rextio-networkx lowering.

Pure string functions (no NetworkX/petgraph import): each returns Rust text that
core codegen splices into the generated crate, deduplicated by exact text. The
helpers return ``pyo3::PyResult<...>`` and use fully qualified paths and scoped
``use`` lines inside the ``fn`` body, so no module-level ``use`` lines are
required.
"""

from __future__ import annotations

from rextio_networkx.rust_snippets.components import (
    cc_call_name,
    cc_helpers,
    is_connected_call_name,
    is_connected_helpers,
    number_connected_components_call_name,
    number_connected_components_helpers,
    resident_cc_call_name,
    resident_cc_helpers,
)
from rextio_networkx.rust_snippets.traversal import (
    BFS_EDGES,
    HAS_PATH,
    NUMBER_OF_EDGES,
    NUMBER_OF_NODES,
    SHORTEST_PATH_LENGTH,
    SHORTEST_PATH_LENGTHS,
    DIJKSTRA_LENGTHS,
    GRAPH_FROM_EDGELIST,
    WEIGHTED_GRAPH_FROM_EDGELIST,
    traversal_helpers,
)

__all__ = [
    "BFS_EDGES",
    "HAS_PATH",
    "NUMBER_OF_EDGES",
    "NUMBER_OF_NODES",
    "SHORTEST_PATH_LENGTH",
    "SHORTEST_PATH_LENGTHS",
    "DIJKSTRA_LENGTHS",
    "GRAPH_FROM_EDGELIST",
    "WEIGHTED_GRAPH_FROM_EDGELIST",
    "cc_call_name",
    "cc_helpers",
    "is_connected_call_name",
    "is_connected_helpers",
    "number_connected_components_call_name",
    "number_connected_components_helpers",
    "resident_cc_call_name",
    "resident_cc_helpers",
    "traversal_helpers",
]
