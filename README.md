# rextio-networkx

A **private incubator** [Rextio](https://github.com/rextio/rextio) plugin that
lowers one covered NetworkX construction route to native Rust: a typed
undirected integer edge list converted once to an immutable local
[`petgraph`](https://crates.io/crates/petgraph) graph, with connected
components computed in Rust and materialized as the exact `list[set[int]]`
NetworkX returns.

It implements Rextio **plugin API 1.2** (`rextio.plugins.api`, protocol v2:
describe/covers + claim/lower + type vocabulary + pinned crate injection) and
requires `rextio>=0.1.2,<0.2`. This is a WP-1 foundation cut — it makes no
performance claims (WP-2 measures the integrated route).

## Public / fallback adapter

The minimum reliable surface is the explicit adapter, whose ordinary Python
implementation delegates to pinned NetworkX 3.5:

```python
from rextio_networkx import connected_components_from_edgelist

edges = [(0, 1), (1, 2), (10, 11)]
connected_components_from_edgelist(edges)
# [{0, 1, 2}, {10, 11}]
```

It reproduces `list(networkx.connected_components(networkx.from_edgelist(edges)))`
exactly. NetworkX is imported lazily, so `import rextio_networkx` never requires
it (install the `test` extra to run the adapter and the certification project).

## Native route

When Rextio compiles a function that calls the adapter with a typed edge-list
argument, the call lowers to the native `petgraph` route. Annotate the argument
and return with the plugin's vocabulary so the types resolve statically:

```python
from rextio_networkx import (
    ComponentList,
    EdgeListI64,
    connected_components_from_edgelist,
)


def components(edges: EdgeListI64) -> ComponentList:
    return connected_components_from_edgelist(edges)
```

- `EdgeListI64` is `list[tuple[int, int]]` — an undirected simple-graph edge
  list of signed 64-bit integer node labels.
- `ComponentList` is `list[set[int]]` — the connected-components result.

Both the native and fallback legs return an identical `list[set[int]]`.

## Covered semantics

Certified value-equivalent against CPython NetworkX 3.5 (rule record
`RXTP-NETWORKX-001`, `verified=True`):

- undirected simple graphs; signed i64 node labels
- edge insertion order; duplicate edges; self-loops
- disconnected and empty edge lists
- component list order matches NetworkX (each component ordered by the first
  insertion of one of its nodes); set element order is not observable through
  equality

Values are bit-exact (integer sets), so certification is value-equivalence, not
within-tolerance.

## Boundaries (fail-closed)

- **Isolated nodes** that appear in no edge cannot be represented by edge-only
  input — both legs omit them identically (`RXTP-NETWORKX-011`).
- **Non-i64 / bool / object node labels** have no native representation and stay
  on the fallback; an out-of-i64 label raises PyO3 `OverflowError` at the
  boundary in native mode (a runtime type-contract violation, not a per-call
  fallback).
- **The raw NetworkX spelling** `list(nx.connected_components(nx.from_edgelist(edges)))`,
  directed graphs, graph options, and weighted/attributed edges are not lowered
  (`RXTP-NETWORKX-019`) — they stay on the Python fallback. The raw spelling is
  not lowerable under core plugin API 1.2: nested calls are opaque atomic leaves
  offered as independent sites, and the intermediate `networkx.Graph` and the
  lazy `connected_components` generator have no boundary representation, while
  `list(...)` is a core builtin that does not consume a plugin generator type.
  Use the explicit adapter instead.
- A covered adapter call with a resolved-but-unsupported argument type is
  rejected with `RXTP-NETWORKX-010` so its guidance is delivered.

All plugin diagnostics live in the `RXTP-NETWORKX-*` namespace.

## Crate dependency

The generated helper depends on one pinned crate, injected and reported through
the core plugin crate-dependency contract:

- `petgraph = "=0.6.5"`

## Development

```bash
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python "rextio>=0.1.2,<0.2"
uv pip install --python .venv/bin/python --no-deps -e .
uv pip install --python .venv/bin/python "networkx==3.5" pytest hypothesis ruff mypy
.venv/bin/python -m pytest
```

The real-Cargo certification test (`tests/e2e/test_components_real_cargo.py`)
is skipped unless `cargo` is on `PATH`; it builds the fixture project once,
proves the native `petgraph` route was selected, and compares the native and
fallback legs (empty, duplicates/self-loop, negative labels, multiple
components).
