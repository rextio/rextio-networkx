"""Rust helper-text generators for the rextio-networkx lowering.

Pure string functions (no NetworkX/petgraph import): each returns Rust text that
core codegen splices into the generated crate, deduplicated by exact text. The
helpers return ``pyo3::PyResult<...>`` and use fully qualified paths and scoped
``use`` lines inside the ``fn`` body, so no module-level ``use`` lines are
required.
"""

from __future__ import annotations

from rextio_networkx.rust_snippets.components import cc_call_name, cc_helpers
from rextio_networkx.rust_snippets.traversal import (
    BFS_EDGES,
    DIJKSTRA_LENGTHS,
    GRAPH_FROM_EDGELIST,
    WEIGHTED_GRAPH_FROM_EDGELIST,
    traversal_helpers,
)

__all__ = [
    "BFS_EDGES",
    "DIJKSTRA_LENGTHS",
    "GRAPH_FROM_EDGELIST",
    "WEIGHTED_GRAPH_FROM_EDGELIST",
    "cc_call_name",
    "cc_helpers",
    "traversal_helpers",
]
