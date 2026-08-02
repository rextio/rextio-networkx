# rextio-networkx

<p align="center">
  <img src="./assets/readme/rextio-icon.png" width="96" alt="Rextio icon">
</p>

<p align="center"><strong>Bounded NetworkX graph algorithms on resident petgraph graphs.</strong></p>

<p align="center">
  English · <a href="https://github.com/rextio/rextio-networkx/blob/main/README.ko.md">한국어</a> · <a href="https://github.com/rextio/rextio-networkx/blob/main/README.zh-hans.md">简体中文</a> · <a href="https://github.com/rextio/rextio-networkx/blob/main/README.zh-hant.md">繁體中文</a> · <a href="https://github.com/rextio/rextio-networkx/blob/main/README.ja.md">日本語</a>
</p>

`rextio-networkx` lowers exact typed adapter calls to Rust while preserving NetworkX 3.5 ordering, result types, and documented exceptions. Graphs stay as native `petgraph::UnGraph` values between supported operations; only final collections or scalars return to Python.

> **Public Alpha 0.1.1** (released 2026-07-26). Requires Python 3.11+, `rextio>=0.1.3,<0.2`, plugin API 1.3, and `networkx==3.5`. Raw `networkx.*` spellings and unsupported graph families remain Python fallback.

## Measured proof

The checked-in generated-wrapper benchmark covers connected components, BFS, and Dijkstra across **56 correctness-valid cells** with 4–2048 requested nodes. Recorded median fallback/native speedups were **2.70×–4.49×**, with no loss cells in that measured matrix.

These results include extraction, ordered deduplication, graph construction, the algorithm, Python result materialization, destruction, and wrapper overhead. Compilation and first-call warm-up are separate. They do not claim performance below 4 nodes, beyond 2048 nodes, outside the recorded graph families, or beyond the exact signed-i64 / finite-f64 contracts. Routes added in 0.1.1, including single-source shortest-path lengths, have correctness/route evidence but no new speed claim.

## How it works

```text
typed edge list → resident petgraph graph → supported resident query → Python result
```

The constructor owns a native undirected graph plus insertion-order sidecars. Consumers borrow that resident value without rebuilding or crossing Python. A resident graph cannot be returned, persisted between wrapper calls, or passed to a materialized Python consumer.

## Quick start

```bash
python -m pip install "rextio-networkx==0.1.1"
```

```toml
# rextio.toml
[rust]
build_tool = "cargo"

[plugins]
enabled = ["rextio-networkx"]
```

```python
from rextio_networkx import (
    ComponentList,
    EdgeListI64,
    connected_components,
    graph_from_edgelist,
)

def components(edges: EdgeListI64) -> ComponentList:
    graph = graph_from_edgelist(edges)
    return connected_components(graph)
```

```bash
rextio build .
```

Use the typed `rextio_networkx` adapters for a native route. Calling `networkx.from_edgelist` or `networkx.connected_components` directly remains fallback.

## Supported adapters

| Build a resident graph | Consume it |
| --- | --- |
| `graph_from_edgelist(EdgeListI64)` | `bfs_edges`, `single_source_shortest_path_lengths`, `has_path`, `shortest_path_length` |
| `graph_from_edgelist(EdgeListI64)` | `connected_components`, `number_connected_components`, `is_connected`, `number_of_nodes`, `number_of_edges` |
| `weighted_graph_from_edgelist(WeightedEdgeListI64F64)` | `dijkstra_path_lengths` |

`connected_components_from_edgelist` remains available as a direct typed route. Adapters accept the exact positional, no-option forms documented by their signatures.

## Exact semantics

- Input is scanned left-to-right. First node encounter and first undirected edge insertion define observable order. Duplicate/reversed edges do not move; self-loops appear once in neighbor order.
- Weighted duplicate edges update the existing edge and the last weight wins, matching `nx.Graph`.
- BFS edges, shortest-path dictionaries, connected-component lists, counts, connectivity, and graph counts preserve their exact documented Python collection/scalar types and order.
- `has_path` and `shortest_path_length` check a missing source before a missing target. Disconnected shortest paths preserve NetworkX 3.5 `NetworkXNoPath` behavior.
- Dijkstra requires finite non-negative input weights (`-0.0` is accepted), preserves ordered finalized keys, and returns source distance as exact `int` `0`; reached non-source distances are `float`.
- The null edge-induced graph has zero nodes, edges, and components. `is_connected` raises NetworkX 3.5 `NetworkXPointlessConcept` for it.

## Input boundary and fallback

- Edge containers must be exact `list`; each edge must be an exact 2-tuple, or exact 3-tuple for weighted input.
- Nodes, sources, and targets must be exact Python `int` values—not `bool` or subclasses—and fit signed i64.
- Weights must be exact Python `float`, finite, and non-negative. Inputs are never mutated, and every occurrence is validated before deduplication.
- Wrong arity, keywords/options, wrong annotations or resident type, and unresolved required plugin annotations fail closed.
- Directed graphs, multigraphs, object/mixed labels, depth/cutoff/weight/method options, raw NetworkX APIs, and any unlisted operation remain fallback-only.

## Benchmark evidence

See the [method and qualifications](benchmarks/README.md), the [full report](benchmarks/results/report.md), and the retained [route evidence](benchmarks/results/check.json). Paired rounds alternate order, every retained sample clears the timing floor, and correctness digests must match before a speedup is reported. Future losses are retained rather than suppressed.

## Development

```bash
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python 'rextio>=0.1.3,<0.2'
uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/python -m pytest
.venv/bin/ruff check src tests benchmarks
.venv/bin/mypy src
```

See [CHANGELOG.md](CHANGELOG.md) for release history.

## License

MIT
