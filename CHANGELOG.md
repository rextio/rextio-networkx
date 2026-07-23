# Changelog

All notable changes to `rextio-networkx` are documented here following Keep a
Changelog and Semantic Versioning conventions.

## [0.1.1] - Unreleased

### Added

- Typed `single_source_shortest_path_lengths(GraphI64, NodeI64) ->
  ShortestPathLengthsI64` adapter. It lowers only the exact no-option typed
  spelling and uses the resident unweighted `petgraph::UnGraph` plus ordered
  adjacency sidecar to match `nx.single_source_shortest_path_length` source-
  first dictionary insertion and BFS discovery order.
- Typed `has_path(GraphI64, NodeI64, NodeI64) -> bool` adapter. It lowers only
  the exact no-option typed spelling, borrows the resident unweighted graph,
  and matches NetworkX 3.5 connected/disconnected and source-before-target
  missing-endpoint semantics.
- Focused fallback/claim/lowering and real-Cargo certification coverage for
  diamonds, duplicate and reversed edges, self-loops, disconnected graphs,
  non-contiguous signed-i64 labels, exact missing-source `NodeNotFound`, and
  input immutability.
- Native-vs-fallback real-Cargo coverage for `has_path`, including
  connected/disconnected, self-loop, duplicate, signed-i64-bound, and exact
  missing-source/missing-target `NodeNotFound` class/message/args cases.

### Changed

- Host checks now accept plugin API 1.3 and later 1.x minor versions while the
  provider itself remains API 1.3 and advertises no artifact capability.
- CI tests the released Rextio 0.1.3 and 0.1.5 hosts on `main` and `0.1.1`.

## [0.1.0] - 2026-07-17

First public alpha release of `rextio-networkx` on PyPI. The supported surface
remains deliberately narrow: only the typed adapter routes listed below are
claimed for native lowering. Raw NetworkX spellings stay fallback-only.

### Added

- Plugin API 1.3 vocabulary: raw materialized `NodeI64`, `EdgeListI64`,
  `WeightedEdgeListI64F64`, `BfsEdgesI64`, and `DijkstraLengthsI64`, plus
  distinct opaque resident `GraphI64` and `WeightedGraphI64F64` types.
- Generated constructor/consumer chains for exact NetworkX 3.5 BFS and
  single-source Dijkstra path lengths. Resident structures own real
  `petgraph::UnGraph` values and explicit stable node/edge/adjacency sidecars;
  consumers borrow resident operands and only final Python results materialize.
- Typed connected-components adapter `connected_components_from_edgelist` that
  shares the exact raw parser and ordered petgraph constructor.
- NetworkX insertion-order compatibility: first-node and first-adjacency order,
  duplicate/reversed-duplicate stability, self-loop-once neighbor order, and
  last-weighted-duplicate-wins graph mutation.
- Ordered Dijkstra heap behavior using distance plus monotonic discovery
  counter, exact finalized-key insertion, stale entry handling, signed zero,
  finite-input cumulative infinity, and infinite-to-finite decrease support.
  Source distance remains Python integer `0`; reached distances are floats.
- Strict native/fallback raw validation with stable exception class/message/args
  and precedence: exact list, exact tuple/arity, exact signed-i64 endpoints,
  exact finite non-negative float weight, exact source, then membership. Every
  occurrence is validated before deduplication.
- Static fail-closed `RXTP-NETWORKX-020` rejection for every recognized
  traversal arity/keyword/type/unresolved-annotation miss. Core-owned resident
  escape and materialized-consumer gates are proven as exact `RXT092`.
- Differential and real-Cargo tests for stars, diamonds, duplicates, self-loops,
  disconnected/low-reach graphs, negative/i64-bound nodes, ties, stale heaps,
  zero and `-0.0`, cumulative overflow, malformed containers/arity/types,
  subclasses, multi-invalid precedence, missing source, input immutability,
  route evidence, one constructor evaluation, and native/fallback execution.
- Honest generated-wrapper benchmark harness for components, BFS, and Dijkstra:
  persistent native/fallback processes, AB/BA paired rounds, common >=10 ms
  calibration, symmetric GC, raw samples, paired-bootstrap intervals,
  order/type-preserving correctness digests, route evidence, exact provenance,
  measured sustained break-even, and explicit non-claims.
- Recorded 56 correctness-valid product cells over 4–2048 nodes. Median
  fallback/native speedups were 2.70x–4.49x; all eight algorithm/family groups
  had sustained measured break-even at the smallest measured size (4), with no
  observed loss cells. This is not generalized below four nodes, outside the
  measured matrix, or beyond the exact covered input contracts.
- Plugin API 1.3 type-owned Rust support for signature-only accepted functions,
  including exact ordered serializers for `EdgeListI64` and
  `WeightedEdgeListI64F64` returns, resident-signature definitions, exact-text
  signature/claim deduplication, and unused-type non-emission regressions.
- Real-Cargo regressions for claimless `NodeI64`, unweighted edge-list, and
  weighted edge-list round trips, including signed-i64 bounds and observable
  `-0.0` preservation.

### Changed

- Public packaging targets released `rextio>=0.1.3,<0.2` (plugin API 1.3)
  instead of a private exact VCS pin to `rextio-core-next`.
- `CoverageDecl.symbols` lists only directly lowerable adapter symbols. Raw
  NetworkX spellings such as `networkx.from_edgelist` and
  `networkx.connected_components` are not advertised as lowerable; they remain
  fallback-only (RXTP-NETWORKX-019).
- Tests, E2E fixtures, and the benchmark harness use the installed `rextio`
  dependency by default. An optional `REXTIO_CORE_ROOT` environment variable
  may point at a local core checkout for development overrides.
- Authoritative benchmark artifacts remain the 56-cell run from product commit
  `242d17828e96e3a2ff1914cd40324c8b7128d981` against integrated core
  `2bd1d1da0cf59e97d1659606bcb1ec12491e032c` / API 1.3. All three product
  routes and order/type-sensitive digests passed; the one-time build was
  6.640 s, first-call warm-up was 0.011–0.607 ms native and 0.027–120.733 ms
  fallback, and every retained sample cleared 19.271 ms against a 41 ns timer
  floor.

### Removed

- `Private :: Do Not Upload` package classifier (this release is intended for
  public PyPI publication as an alpha).

### Security

- Bool/int-subclass coercion, out-of-i64 extraction, tuple indexing before arity
  validation, and invalid overwritten weighted duplicates now fail closed with
  stable documented Python exceptions in both execution modes.

## [Unreleased]

### Added

### Changed

### Security
