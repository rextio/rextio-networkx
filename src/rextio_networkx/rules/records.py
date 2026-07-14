"""The rule records rextio-networkx describes to Rextio core.

L2 rule records per the Rextio tooling contract: each states a pattern, the
constraint that decides it, the RXTP-NETWORKX diagnostic code it fires as, and
remediation guidance. The set covers the single implemented native route — a
typed undirected signed-i64 edge list converted once to an immutable local
``petgraph`` graph, with connected components computed in Rust and materialized
as the exact ``list[set[int]]`` NetworkX returns — plus the explicit exclusions
around it.

All records are ``experimental`` (plugin API 1.2, requires ``rextio>=0.1.2``).
The record with outcome ``native`` carries ``verified=True``: its lowering is
certified bit-exactly (integer node sets/lists) via the core plugin
certification kit (``rextio.plugins.testing``) against CPython NetworkX 3.5.

Only RXTP-NETWORKX-010 is actively emitted, via ``Rejected``. RXTP-NETWORKX-011
(node representation) and RXTP-NETWORKX-019 (uncovered API) are
declarative-only: they document why code stays on the fallback but are never
emitted by ``claim()`` — sites outside the covered surface return
``NotCovered`` and core reports its own diagnostic.
"""

from __future__ import annotations

from rextio.plugins.api import RuleRecord, RuleScope

_RULES: tuple[RuleRecord, ...] = (
    RuleRecord(
        id="rextio-networkx/connected-components-edgelist",
        provider="rextio-networkx",
        scope=RuleScope(
            kind="call",
            pattern=(
                "rextio_networkx.connected_components_from_edgelist(edges) with a single "
                "positional rextio_networkx.EdgeListI64 argument and no keywords "
                "(undirected simple graph of signed i64 node labels)"
            ),
        ),
        constraint=(
            "The covered adapter call with exactly one positional argument typed "
            "rextio_networkx.EdgeListI64 (a list[tuple[int, int]] of signed 64-bit "
            "integer node labels) and no keywords lowers to a native PyO3 helper: "
            "the edge list is converted once to an immutable local petgraph "
            "UnGraph (nodes assigned indices in NetworkX from_edgelist insertion "
            "order — each edge inserts u then v), connected components are computed "
            "in Rust via petgraph union-find, and the exact Python-visible "
            "list[set[int]] is materialized. Semantics match "
            "list(networkx.connected_components(networkx.from_edgelist(edges))) for "
            "undirected simple graphs, signed i64 node labels, edge insertion order, "
            "duplicate edges, self-loops, and disconnected or empty edge lists. "
            "Component list order matches NetworkX (each component ordered by the "
            "first insertion of one of its nodes); set element order is not "
            "observable through equality and is not claimed as observable. Values "
            "are bit-exact (integer sets), so verified means value-equivalent, not "
            "within-tolerance. Divergences: edge-only input intentionally cannot "
            "represent an isolated node that appears in no edge (both legs omit it "
            "identically, since the fallback also builds from the edge list); a node "
            "label outside the i64 range raises PyO3 OverflowError at the boundary "
            "in native mode (a runtime type-contract violation, not a per-call "
            "fallback). Directed graphs, graph options, weighted/attributed edges, "
            "and the raw NetworkX spelling are not this rule (see RXTP-NETWORKX-019)."
        ),
        outcome="native",
        diagnostic_code="RXTP-NETWORKX-001",
        guidance=(
            "Call rextio_networkx.connected_components_from_edgelist(edges) with a "
            "single argument annotated rextio_networkx.EdgeListI64 "
            "(list[tuple[int, int]]) and annotate the return "
            "rextio_networkx.ComponentList (list[set[int]]) so the types resolve "
            "statically. Keep node labels within the signed i64 range."
        ),
        stability="experimental",
        verified=True,
    ),
    RuleRecord(
        id="rextio-networkx/unsupported-argument-type",
        provider="rextio-networkx",
        scope=RuleScope(
            kind="call",
            pattern=(
                "a rextio_networkx.connected_components_from_edgelist call whose single "
                "resolved argument type is known but is not rextio_networkx.EdgeListI64"
            ),
        ),
        constraint=(
            "A covered adapter call whose argument type is resolved but is not the "
            "rextio_networkx.EdgeListI64 edge-list type is rejected here so the "
            "plugin's guidance is delivered and the function falls back. Unresolved "
            "arguments, wrong arity, and calls carrying keywords are NotCovered "
            "instead, so core's own diagnostic fires."
        ),
        outcome="fallback",
        diagnostic_code="RXTP-NETWORKX-010",
        guidance=(
            "Pass the edges as a single rextio_networkx.EdgeListI64 value "
            "(list[tuple[int, int]] of signed i64 node labels) at the boundary of "
            "the hot path, or keep the function on the Python fallback."
        ),
        stability="experimental",
    ),
    RuleRecord(
        id="rextio-networkx/unsupported-node-representation",
        provider="rextio-networkx",
        scope=RuleScope(
            kind="type",
            pattern=(
                "node labels that are not signed i64 integers (object/str/float/bool "
                "or out-of-i64-range labels), or isolated nodes not present in any edge"
            ),
        ),
        constraint=(
            "The covered surface represents nodes only as signed 64-bit integers and "
            "only through the edge list. Non-integer, bool, object, or out-of-i64 "
            "node labels have no faithful native representation; and edge-only input "
            "cannot express an isolated node that appears in no edge. Such graphs "
            "stay on the Python fallback (or must be constructed through NetworkX "
            "directly). Declarative-only: never emitted by claim()."
        ),
        outcome="fallback",
        diagnostic_code="RXTP-NETWORKX-011",
        guidance=(
            "Relabel nodes to signed i64 integers and express every node through an "
            "edge (add a self-loop for an otherwise-isolated node) to use the native "
            "route, or keep the graph on the Python fallback."
        ),
        stability="experimental",
    ),
    RuleRecord(
        id="rextio-networkx/unsupported-api",
        provider="rextio-networkx",
        scope=RuleScope(
            kind="call",
            pattern=(
                "any NetworkX API outside the covered adapter route — the raw "
                "list(networkx.connected_components(networkx.from_edgelist(edges))) "
                "spelling, directed graphs, graph options, weighted/attributed edges, "
                "other algorithms"
            ),
        ),
        constraint=(
            "APIs outside the covered adapter route have no certified native lowering "
            "and keep the surrounding candidate on the Python fallback — Rextio never "
            "guesses. The raw NetworkX spelling in particular is not lowerable under "
            "core plugin API 1.2: nested calls are opaque atomic leaves offered as "
            "independent sites, and the intermediate networkx.Graph and the lazy "
            "connected_components generator have no boundary representation, while "
            "list(...) is a core builtin that does not consume a plugin generator "
            "type. Use the explicit rextio_networkx.connected_components_from_edgelist "
            "adapter (RXTP-NETWORKX-001) instead. Declarative-only: never emitted by "
            "claim()."
        ),
        outcome="fallback",
        diagnostic_code="RXTP-NETWORKX-019",
        guidance=(
            "Route the hot path through rextio_networkx.connected_components_from_edgelist "
            "with a typed EdgeListI64 argument; keep other NetworkX usage (directed "
            "graphs, graph options, attributed edges, the raw from_edgelist / "
            "connected_components spelling) on the Python fallback."
        ),
        stability="experimental",
    ),
)


def networkx_rule_records() -> tuple[RuleRecord, ...]:
    """Return the plugin's rule records, ordered by rule id."""
    return _ORDERED


_ORDERED: tuple[RuleRecord, ...] = tuple(sorted(_RULES, key=lambda record: record.id))
