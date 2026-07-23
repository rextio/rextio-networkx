"""Plugin type keys and fail-closed claim diagnostics."""

from __future__ import annotations

from rextio.analyzer.diagnostics import Diagnostic
from rextio.plugins.api import ClaimResult, ClaimSite, NotCovered, Rejected

EDGELIST_I64 = "rextio-networkx/edgelist-i64"
WEIGHTED_EDGELIST_I64_F64 = "rextio-networkx/weighted-edgelist-i64-f64"
NODE_I64 = "rextio-networkx/node-i64"
COMPONENT_LIST = "rextio-networkx/component-list"
BFS_EDGES_I64 = "rextio-networkx/bfs-edges-i64"
DIJKSTRA_LENGTHS_I64 = "rextio-networkx/dijkstra-lengths-i64"
SHORTEST_PATH_LENGTHS_I64 = "rextio-networkx/shortest-path-lengths-i64"
GRAPH_I64 = "rextio-networkx/graph-i64"
WEIGHTED_GRAPH_I64_F64 = "rextio-networkx/weighted-graph-i64-f64"

TYPE_KEYS: frozenset[str] = frozenset(
    {
        EDGELIST_I64,
        WEIGHTED_EDGELIST_I64_F64,
        NODE_I64,
        COMPONENT_LIST,
        BFS_EDGES_I64,
        DIJKSTRA_LENGTHS_I64,
        SHORTEST_PATH_LENGTHS_I64,
        GRAPH_I64,
        WEIGHTED_GRAPH_I64_F64,
    }
)


def is_edgelist_type(type_key: str | None) -> bool:
    """Whether ``type_key`` is the unweighted edge-list type."""
    return type_key == EDGELIST_I64


def reject_site(site: ClaimSite, *, expected: str) -> Rejected:
    """Reject a recognized traversal target with stable plugin guidance."""
    operands = ", ".join("unresolved" if item is None else item for item in site.operand_types)
    keyword_names = ", ".join(keyword.name for keyword in site.keywords) or "none"
    return Rejected(
        diagnostic=Diagnostic(
            code="RXTP-NETWORKX-020",
            severity="error",
            message=(
                f"rextio-networkx cannot lower recognized traversal target {site.target!r}: "
                f"operand types ({operands}), keywords ({keyword_names}); expected {expected}"
            ),
            file_path=site.file_path,
            line=site.line,
            column=site.column,
            suggestion=(
                "Use the exact rextio_networkx annotation vocabulary and positional call "
                "shape shown in the traversal documentation; keep unsupported NetworkX "
                "options on the Python fallback."
            ),
        )
    )


def not_covered_or_rejected(site: ClaimSite) -> ClaimResult:
    """Preserve the WP-1 component route's legacy unresolved behavior."""
    if any(operand is None for operand in site.operand_types):
        return NotCovered()
    return Rejected(
        diagnostic=Diagnostic(
            code="RXTP-NETWORKX-010",
            severity="error",
            message=(
                f"rextio-networkx cannot lower {site.target!r}: expected one "
                "rextio_networkx.EdgeListI64 argument"
            ),
            file_path=site.file_path,
            line=site.line,
            column=site.column,
            suggestion="Annotate the single edge-list argument as rextio_networkx.EdgeListI64.",
        )
    )
