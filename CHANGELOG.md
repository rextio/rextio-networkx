# Changelog

All notable changes to `rextio-networkx` are documented here following Keep a
Changelog and Semantic Versioning conventions.

## [Unreleased]

### Added

- `Private :: Do Not Upload` package classifier so accidental PyPI publication is
  blocked while this repository remains a private pre-release incubator.
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
  fallback/native speedups were 2.70x–4.49x; all eight algorithm/family groups
  had sustained measured break-even at the smallest measured size (4), with no
  observed loss cells. This is not generalized below four nodes, outside the
  measured matrix, or beyond the exact covered input contracts.
- Plugin API 1.3 type-owned Rust support for signature-only accepted functions,
  including exact ordered serializers for `EdgeListI64` and
  `WeightedEdgeListI64F64` returns, resident-signature definitions, exact-text
  signature/claim deduplication, and unused-type non-emission regressions.
- Real-Cargo regressions (collected for the serialized verification phase) for
  claimless `NodeI64`, unweighted edge-list, and weighted edge-list round trips,
  including signed-i64 bounds and observable `-0.0` preservation.

### Changed

- The provider now advertises plugin API 1.3. Package metadata pins exact
  integrated core-next commit `2bd1d1da0cf59e97d1659606bcb1ec12491e032c`;
  it cannot select
  released API-1.2 core `rextio==0.1.2`. Public packaging waits for an API-1.3
  core release.
- The retained connected-components route shares the new exact raw parser and
  resident-compatible ordered petgraph constructor.
- Test collection, E2E setup, and benchmark startup verify core HEAD, plugin API
  and `rextio.__file__` under the frozen source checkout.
- Replace the stale benchmark artifacts with an authoritative 56-cell run from
  product commit `242d17828e96e3a2ff1914cd40324c8b7128d981` against integrated
  core `2bd1d1da0cf59e97d1659606bcb1ec12491e032c` / API 1.3. All three product
  routes and order/type-sensitive digests passed; the one-time build was
  6.640 s, first-call warm-up was 0.011–0.607 ms native and 0.027–120.733 ms
  fallback, and every retained sample cleared 19.271 ms against a 41 ns timer
  floor.

### Security

- Bool/int-subclass coercion, out-of-i64 extraction, tuple indexing before arity
  validation, and invalid overwritten weighted duplicates now fail closed with
  stable documented Python exceptions in both execution modes.
