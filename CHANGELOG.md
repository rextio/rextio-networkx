# Changelog

All notable changes to `rextio-networkx` are documented here following Keep a
Changelog and Semantic Versioning conventions.

## [Unreleased]

### Added

- Private-incubator plugin API 1.3 vocabulary: raw materialized `NodeI64`,
  `EdgeListI64`, `WeightedEdgeListI64F64`, `BfsEdgesI64`, and
  `DijkstraLengthsI64`, plus distinct opaque resident `GraphI64` and
  `WeightedGraphI64F64` types.
- Generated constructor/consumer chains for exact NetworkX 3.5 BFS and
  single-source Dijkstra path lengths. Resident structures own real
  `petgraph::UnGraph` values and explicit stable node/edge/adjacency sidecars;
  consumers borrow resident operands and only final Python results materialize.
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
  fallback/native speedups were 2.70x–4.40x; every family had sustained measured
  break-even at the smallest measured size (4), with no observed loss cells
  (explicitly not generalized below four nodes or beyond the recorded inputs).

### Changed

- The provider now advertises plugin API 1.3. Package metadata pins exact
  core-next commit `ac2b79d304f13abaaecaf7714f897574c3b6256f`; it cannot select
  released API-1.2 core `rextio==0.1.2`. Public packaging waits for an API-1.3
  core release.
- The retained connected-components route shares the new exact raw parser and
  resident-compatible ordered petgraph constructor.
- Test collection, E2E setup, and benchmark startup verify core HEAD, plugin API
  and `rextio.__file__` under the frozen source checkout.

### Security

- Bool/int-subclass coercion, out-of-i64 extraction, tuple indexing before arity
  validation, and invalid overwritten weighted duplicates now fail closed with
  stable documented Python exceptions in both execution modes.
