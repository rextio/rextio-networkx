# Changelog

All notable changes to `rextio-networkx` are documented here. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial private incubator cut (WP-1). Rextio plugin API 1.2 (`rextio.plugins.api`,
  protocol v2 describe/covers + claim/lower + type vocabulary + pinned crate
  injection); requires `rextio>=0.1.2,<0.2`.
- Public/fallback adapter `rextio_networkx.connected_components_from_edgelist(edges)
  -> list[set[int]]`, delegating to pinned NetworkX 3.5 and reproducing
  `list(networkx.connected_components(networkx.from_edgelist(edges)))` exactly.
  NetworkX 3.5 is a pinned runtime dependency, imported lazily so package import
  stays cheap.
- Annotation vocabulary `rextio_networkx.EdgeListI64` (`list[tuple[int, int]]`)
  and `rextio_networkx.ComponentList` (`list[set[int]]`) plus the matching
  plugin types with PyO3 boundary conversions.
- Native construction route: the covered adapter call with a typed `EdgeListI64`
  argument lowers to a native PyO3 helper that builds an immutable local
  `petgraph` `UnGraph` once and computes connected components in Rust via
  petgraph union-find, materializing the exact `list[set[int]]`. Certified
  value-equivalent against CPython NetworkX 3.5 (`RXTP-NETWORKX-001`,
  `verified=True`): undirected simple graphs, signed i64 node labels, edge
  insertion order, duplicate edges, self-loops, disconnected and empty edge
  lists, and NetworkX component-list order.
- Rule records and diagnostics in the `RXTP-NETWORKX-*` namespace: emitted
  `RXTP-NETWORKX-010` (unsupported argument type) plus declarative
  `RXTP-NETWORKX-011` (node representation / isolated nodes) and
  `RXTP-NETWORKX-019` (uncovered API, including the non-lowerable raw NetworkX
  spelling).
- Pinned crate dependency `petgraph = "=0.6.5"`.
- Real-Cargo dual-leg certification test proving native-route selection and
  native/fallback equivalence.

### Changed

- NetworkX 3.5 is now declared as a real pinned **runtime dependency** (it was
  previously only in the `test`/`dev` extras): the public/fallback adapter
  imports it at call time, so any install that uses the adapter needs it. It is
  still imported lazily. The extras no longer duplicate the pin.
- The native boundary now receives the raw Python edge list (a `Bound<PyList>`)
  and extracts each node label to `i64` in the injected helper, rejecting a
  Python `bool` label with `TypeError`. Previously the edge list was extracted
  by value into `Vec<(i64, i64)>`, which silently coerced `bool` labels
  (`True`/`False` → `1`/`0`) and diverged in element type from the NetworkX
  fallback. An out-of-i64 label still raises `OverflowError` at the boundary.
  `RXTP-NETWORKX-001`/`011` documentation now describes both as deterministic,
  fail-closed runtime type-contract violations rather than fallbacks.

### Tests

- Added real native/fallback boundary coverage: `bool` labels fail closed with
  `TypeError` and out-of-i64 labels with `OverflowError` at the native boundary,
  plus an in-contract `i64_bounds` covered case proving the full signed-i64
  range round-trips natively.
- The real-Cargo certification test imports its mandatory NetworkX/Hypothesis
  dependencies unconditionally (no `importorskip`, no `# noqa: E402`); Cargo
  remains the only environment gate.

### Notes

- No performance claims in this cut; WP-2 measures the integrated route.
- Directed graphs, graph options, weighted/attributed edges, and rank-2 matmul
  style extensions are out of scope for WP-1.
