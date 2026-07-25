# rextio-networkx

A **public alpha** Rextio plugin for exact, deliberately narrow NetworkX 3.5
routes on real `petgraph::UnGraph` resident values.

Version **0.1.1** was released on **2026-07-26**. It expands the resident
shortest-path, component, connectivity, and graph-count query surface without
claiming raw NetworkX spellings or unsupported graph families.

Requires **Rextio** `>=0.1.3,<0.2` (plugin API **1.3**). Install from PyPI as
`rextio-networkx`. Repository: [rextio/rextio-networkx](https://github.com/rextio/rextio-networkx).

This is an honest alpha: only the typed adapter routes below are claimed for
native lowering. Everything outside that surface remains Python fallback.

## Product routes

The public proof shapes are:

```python
from rextio_networkx import (
    BfsEdgesI64,
    ComponentList,
    DijkstraLengthsI64,
    EdgeListI64,
    NodeI64,
    ShortestPathLengthsI64,
    WeightedEdgeListI64F64,
    bfs_edges,
    connected_components,
    dijkstra_path_lengths,
    graph_from_edgelist,
    has_path,
    is_connected,
    number_connected_components,
    number_of_edges,
    number_of_nodes,
    shortest_path_length,
    single_source_shortest_path_lengths,
    weighted_graph_from_edgelist,
)


def bfs_product(edges: EdgeListI64, source: NodeI64) -> BfsEdgesI64:
    return bfs_edges(graph_from_edgelist(edges), source)


def shortest_path_lengths_product(
    edges: EdgeListI64,
    source: NodeI64,
) -> ShortestPathLengthsI64:
    return single_source_shortest_path_lengths(graph_from_edgelist(edges), source)


def has_path_product(edges: EdgeListI64, source: NodeI64, target: NodeI64) -> bool:
    return has_path(graph_from_edgelist(edges), source, target)


def shortest_path_length_product(
    edges: EdgeListI64,
    source: NodeI64,
    target: NodeI64,
) -> int:
    return shortest_path_length(graph_from_edgelist(edges), source, target)


def components_product(edges: EdgeListI64) -> ComponentList:
    return connected_components(graph_from_edgelist(edges))


def component_count_product(edges: EdgeListI64) -> int:
    return number_connected_components(graph_from_edgelist(edges))


def is_connected_product(edges: EdgeListI64) -> bool:
    return is_connected(graph_from_edgelist(edges))


def node_count_product(edges: EdgeListI64) -> int:
    return number_of_nodes(graph_from_edgelist(edges))


def edge_count_product(edges: EdgeListI64) -> int:
    return number_of_edges(graph_from_edgelist(edges))


def dijkstra_product(
    edges: WeightedEdgeListI64F64,
    source: NodeI64,
) -> DijkstraLengthsI64:
    return dijkstra_path_lengths(
        weighted_graph_from_edgelist(edges),
        source,
    )
```

The constructor result is an opaque plugin-owned resident graph
(`PluginType(conversion=None)`). Native code owns a real `petgraph::UnGraph`
and an insertion-order sidecar; the consumer borrows it. Only a final
materialized list/dict/set collection or scalar crosses back to Python. A
resident value cannot be returned to Python or sent through a materialized
Python consumer (`RXT092`), and it cannot persist across wrapper calls.

The fallback legs execute these exact NetworkX 3.5 constructions:

```python
G = nx.Graph()
G.add_edges_from(edges)
list(nx.bfs_edges(G, source))
nx.single_source_shortest_path_length(G, source)
nx.has_path(G, source, target)
nx.shortest_path_length(G, source, target)
list(nx.connected_components(G))
nx.number_connected_components(G)
nx.is_connected(G)
G.number_of_nodes()
G.number_of_edges()

G = nx.Graph()
G.add_weighted_edges_from(edges)
nx.single_source_dijkstra_path_length(G, source, weight="weight")
```

### Exact order and value semantics

- Input is scanned left-to-right. First endpoint encounter fixes node order.
- First undirected edge insertion fixes each adjacency position. Duplicate and
  reversed-duplicate edges do not move it; a self-loop appears once in neighbor
  order.
- A weighted duplicate updates the existing petgraph edge; the last weight
  wins exactly as in `nx.Graph`.
- BFS uses the preserved neighbor order and returns the exact ordered concrete
  `list[tuple[int, int]]`.
- `single_source_shortest_path_lengths` uses the same ordered BFS and returns
  the exact source-first `dict[int, int]` discovery order of
  `nx.single_source_shortest_path_length`; its source is always integer `0`.
- `has_path` borrows the same resident unweighted graph, returns an exact Python
  `bool`, and performs ordered BFS with early success. It accepts only typed
  `GraphI64, NodeI64, NodeI64` positional arguments; source membership is
  checked before target membership, matching NetworkX 3.5's exact
  `NodeNotFound` class, message, and `args`.
- `shortest_path_length` uses the same source-before-target membership
  precedence and returns an exact Python `int`, including `0` when source and
  target are equal. A disconnected pair raises the exact NetworkX 3.5
  `NetworkXNoPath("No path between X and Y.")`.
- `connected_components` borrows the resident graph and materializes the same
  ordered `list[set[int]]` as `list(nx.connected_components(G))`; component
  order follows first node insertion and each set retains exact integer values.
- `number_connected_components` borrows the same resident graph and returns
  the exact Python `int` from `nx.number_connected_components(G)`, including
  `0` for the null edge-induced graph.
- `is_connected` borrows the same resident graph and returns an exact Python
  `bool`. The null edge-induced graph raises the exact NetworkX 3.5
  `NetworkXPointlessConcept("Connectivity is undefined for the null graph.")`.
- `number_of_nodes` and `number_of_edges` borrow the resident graph and return
  exact Python integers. Duplicate and reversed duplicate edges count once, a
  self-loop counts once, and the empty edge-induced graph reports zero nodes
  and zero edges.
- Dijkstra uses `(distance, monotonic discovery counter, node)` heap semantics,
  inserts keys when finalized, ignores equal-distance rediscovery, skips stale
  entries, supports cumulative `+inf`, and can decrease a previously discovered
  infinite route to finite. It uses partial comparison, not `total_cmp`.
- Dijkstra's source value is the exact integer `0`; every reached non-source
  value is a Python `float`. Tests compare ordered `list(result.items())`,
  exact key/value types, and float `hex()` values.
- Missing BFS source raises `networkx.NetworkXError("The node X is not in the
  graph.")`. Missing shortest-path-lengths source raises
  `networkx.NodeNotFound("Source X is not in G")`; missing Dijkstra source
  raises `networkx.NodeNotFound("Node X not found in graph")`.
  `has_path` raises `networkx.NodeNotFound("Source X is not in G")` for a
  missing source before it considers the target, and
  `networkx.NodeNotFound("Target X is not in G")` for a missing target.
  `shortest_path_length` preserves that precedence and those messages.

The typed `connected_components_from_edgelist` route remains available. It
shares the strict raw edge parser, ordered petgraph constructor, and component
materializer with the resident `connected_components(GraphI64)` route.

API 1.3 type-level support is explicit and granular. `NodeI64`, both edge-list
types, and both resident graph types own the exact Rust helpers referenced by
their signatures or boundary conversions through `PluginType.helpers`.
Claimless accepted functions therefore compile when a plugin type appears only
in a parameter or return. Edge-list returns materialize exact ordered built-in
lists of exact 2- or 3-tuples; signed i64 values and observable float bits
(including `-0.0`) round-trip without normalization. Unused registered types
emit no support, and helper text shared by a signature and claim is emitted
once.

## Fail-closed boundary

The validation precedence is edge-list container, each edge and exact arity,
endpoints, weight, source, then source membership. Native and fallback modes
match exception class, `str(e)`, and one-string `e.args`.

- edge container: exact `list` only
- unweighted occurrence: exact 2-`tuple`
- weighted occurrence: exact 3-`tuple`
- nodes/source/target: exact Python `int` (not `bool` or a subclass), signed-i64 range
- weight: exact Python `float` (not `int`, `bool`, or subclass), finite and
  non-negative; `-0.0` is accepted

Every occurrence is validated before deduplication, so an invalid overwritten
duplicate still raises. Malformed arity is checked before indexing. Input
objects are never mutated.

A recognized traversal target with wrong arity, keywords/options, a plain core
`int` instead of `NodeI64`, wrong resident type, or missing/unresolved required
plugin annotation is rejected statically as `RXTP-NETWORKX-020`. Directed and
multigraph inputs, object/mixed labels, depth/cutoff/weight/method options, and
raw NetworkX spellings are outside this surface and remain fallback-only.

Raw NetworkX APIs such as `networkx.from_edgelist` and
`networkx.connected_components` are **not** lowerable symbols. Use the typed
`rextio_networkx` adapters when you need a native route.

## Benchmark evidence

[`benchmarks/bench_product_routes.py`](benchmarks/bench_product_routes.py)
builds a real generated wrapper and compares two persistent mode processes. It
includes extraction, ordered deduplication, graph construction, algorithm,
exact result materialization, destruction, and wrapper overhead; one-time build
and warm-up are separate. Paired rounds alternate AB/BA, use a common iteration
count with every sample at least 10 ms, control GC symmetrically, and preserve
raw samples plus correctness/route/provenance digests.

The tracked [`benchmarks/results/report.md`](benchmarks/results/report.md) and
[`benchmarks/results/raw_samples.json`](benchmarks/results/raw_samples.json)
are the current authoritative full-run evidence for product commit
`242d17828e96e3a2ff1914cd40324c8b7128d981` against core
`2bd1d1da0cf59e97d1659606bcb1ec12491e032c` / API 1.3. `check.json` accepted
all three generated native routes (connected components, BFS, and Dijkstra),
and all 56 cells preserved their order/type-sensitive native/fallback
correctness digests. The one-time build took 6.640 s; first-call warm-up ranged
from 0.011–0.607 ms native and 0.027–120.733 ms fallback. Every retained sample
was at least 19.271 ms against a 41 ns timer floor.

Across the measured 4–2048 requested-node matrix, median fallback/native
speedups were **2.70x–4.49x**, with no measured loss cells. All eight
algorithm/family groups have a sustained measured break-even at requested
nodes = 4: their paired-bootstrap 95% intervals remain favorable at every
larger measured size. This does **not** claim a break-even below 4 nodes or
generalize beyond the exact signed-i64 / finite-f64 contracts and recorded
inputs. The harness retains every future loss or `none` finding rather than
suppressing it, and never labels a standalone PyO3 row as product speedup.

## Development

```bash
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python 'rextio>=0.1.3,<0.2'
uv pip install --python .venv/bin/python -e ".[dev]"

.venv/bin/python -m pytest
.venv/bin/ruff check src tests benchmarks
.venv/bin/ruff format --check src tests benchmarks
.venv/bin/mypy src
.venv/bin/python -m build
.venv/bin/twine check dist/*
.venv/bin/check-wheel-contents dist/*.whl
```

By default, tests and benchmarks import the **installed** `rextio` package.
To point them at a local core checkout instead (optional development override):

```bash
export REXTIO_CORE_ROOT=/path/to/rextio   # directory that contains src/rextio
uv pip install --python .venv/bin/python --no-deps -e "$REXTIO_CORE_ROOT"
.venv/bin/python -m pytest
```

Collection and real-Cargo fixtures require plugin API 1.3 from that installed
(or overridden) core. Historical benchmark provenance files may still record
the original machine-local core path from the measured run; the harness no
longer hardcodes it.
