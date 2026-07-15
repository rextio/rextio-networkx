# rextio-networkx

A **private incubator** Rextio plugin for exact, deliberately narrow NetworkX
3.5 routes on real `petgraph::UnGraph` resident values.

This branch requires unreleased Rextio plugin API **1.3** at exact integrated
core commit `2bd1d1da0cf59e97d1659606bcb1ec12491e032c`. Released
`rextio==0.1.2` implements API 1.2 and is not compatible. The package metadata
therefore pins the core-next Git commit rather than a released version range;
publication waits for a core release that actually denotes API 1.3.

## Product routes

The public proof shapes are:

```python
from rextio_networkx import (
    BfsEdgesI64,
    DijkstraLengthsI64,
    EdgeListI64,
    NodeI64,
    WeightedEdgeListI64F64,
    bfs_edges,
    dijkstra_path_lengths,
    graph_from_edgelist,
    weighted_graph_from_edgelist,
)


def bfs_product(edges: EdgeListI64, source: NodeI64) -> BfsEdgesI64:
    return bfs_edges(graph_from_edgelist(edges), source)


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
and an insertion-order sidecar; the consumer borrows it. Only the final
`list[tuple[int, int]]` or ordered Python `dict` crosses back to Python. A
resident value cannot be returned to Python or sent through a materialized
Python consumer (`RXT092`), and it cannot persist across wrapper calls.

The fallback legs execute these exact NetworkX 3.5 constructions:

```python
G = nx.Graph()
G.add_edges_from(edges)
list(nx.bfs_edges(G, source))

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
- Dijkstra uses `(distance, monotonic discovery counter, node)` heap semantics,
  inserts keys when finalized, ignores equal-distance rediscovery, skips stale
  entries, supports cumulative `+inf`, and can decrease a previously discovered
  infinite route to finite. It uses partial comparison, not `total_cmp`.
- Dijkstra's source value is the exact integer `0`; every reached non-source
  value is a Python `float`. Tests compare ordered `list(result.items())`,
  exact key/value types, and float `hex()` values.
- Missing BFS source raises `networkx.NetworkXError("The node X is not in the
  graph.")`. Missing Dijkstra source raises
  `networkx.NodeNotFound("Node X not found in graph")`.

The WP-1 typed `connected_components_from_edgelist` route remains available
and now shares the strict raw edge parser and ordered petgraph constructor.

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
- nodes/source: exact Python `int` (not `bool` or a subclass), signed-i64 range
- weight: exact Python `float` (not `int`, `bool`, or subclass), finite and
  non-negative; `-0.0` is accepted

Every occurrence is validated before deduplication, so an invalid overwritten
duplicate still raises. Malformed arity is checked before indexing. Input
objects are never mutated.

A recognized traversal target with wrong arity, keywords/options, a plain core
`int` instead of `NodeI64`, wrong resident type, or missing/unresolved required
plugin annotation is rejected statically as `RXTP-NETWORKX-020`. Directed and
multigraph inputs, object/mixed labels, target/depth/cutoff/weight options, and
raw NetworkX spellings are outside this surface and remain fallback-only.

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
are retained as **historical, stale evidence**. Their 56 correctness-valid
cells and 2.70x–4.40x measured medians came from product commit `e40bd64` and
the superseded core `ac2b79d…`; they predate both the current harness tip and
the API-1.3 type-support/serializer closure. They are not a speed claim for the
current branch. A new authoritative 56-cell run against `2bd1d1d…` remains a
serialized pre-release gate. The harness retains every future loss or `none`
finding rather than suppressing it, and never labels a standalone PyO3 row as
product speedup.

## Development

```bash
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -e ../rextio-core-next
uv pip install --python .venv/bin/python --no-deps -e .
uv pip install --python .venv/bin/python \
  'networkx==3.5' pytest hypothesis ruff mypy build twine check-wheel-contents

.venv/bin/python -m pytest
.venv/bin/ruff check src tests benchmarks
.venv/bin/ruff format --check src tests benchmarks
.venv/bin/mypy src
.venv/bin/python -m build
```

Test collection, real-Cargo fixtures, and benchmark startup verify the exact
core HEAD, API version, and `rextio.__file__` under the core-next source
checkout so a globally installed released core cannot satisfy the gates.
