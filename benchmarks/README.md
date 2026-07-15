# Product-route benchmarks

`bench_product_routes.py` measures the generated Rextio wrapper, not a
standalone Rust/PyO3 prototype. It builds a fixture against frozen core commit
`2bd1d1da0cf59e97d1659606bcb1ec12491e032c` (plugin API 1.3), verifies
`check.json` route `native-plugin:rextio-networkx`, then starts two persistent
wrapper processes:

- `REXTIO_NATIVE_MODE=native`
- `REXTIO_NATIVE_MODE=fallback`

Both receive identical exact-list/tuple inputs. Timed calls include wrapper
overhead, raw boundary extraction, order-preserving deduplication, graph
construction, algorithm execution, Python result materialization, and result
destruction. One-time compilation and first-call warm-up are excluded from
steady state and recorded separately.

Paired rounds alternate AB/BA order. One common iteration count is calibrated
until every retained native and fallback sample is at least 10 ms. GC is
collected before and disabled symmetrically during each sample. Raw samples,
schedule, seed, correctness digest, timer floor, route digest, and exact
toolchain/package provenance are retained in `results/raw_samples.json`; the
original route evidence is `results/check.json`.

```bash
.venv/bin/python benchmarks/bench_product_routes.py --smoke
.venv/bin/python benchmarks/bench_product_routes.py
```

The full default matrix measures 4, 8, 16, 32, 128, 512, and 2048 requested
nodes across connected, disconnected, and low-reach families (56 cells total).

Break-even is never interpolated. It is the first measured size whose paired
bootstrap 95% interval for `log(native/fallback)` is wholly below zero and
remains below zero at every larger measured size in the same algorithm/family;
otherwise the report says `none`.

No direct-PyO3 diagnostic row is presented as product performance. A
native/fallback order/type-preserving digest mismatch invalidates the cell and
suppresses its speedup.

## Current authoritative result

The checked-in `results/{check.json,raw_samples.json,report.md}` comes from the
successful full 56-cell run at product commit
`242d17828e96e3a2ff1914cd40324c8b7128d981`, frozen core
`2bd1d1da0cf59e97d1659606bcb1ec12491e032c`, and plugin API 1.3. Route evidence
accepted connected components, BFS, and Dijkstra as
`native-plugin:rextio-networkx`; all 56 order/type-sensitive correctness
digests matched between native and fallback. The copied `check.json` SHA-256 is
`69bd6fd77dd26cf4cc2a40ec6536e126954bd0f8c39aa72be7d6e14906a3ea92`.

The one-time build took 6.640 s and is excluded from steady-state latency.
First-call warm-up ranged from 0.011–0.607 ms native and 0.027–120.733 ms
fallback. The minimum retained paired sample was 19.271 ms against a 41 ns
timer floor. Median fallback/native speedups span **2.70x–4.49x**, with zero
measured loss cells. Each of the eight algorithm/family groups has a sustained
measured break-even at requested nodes = 4 because its paired-bootstrap 95%
interval remains favorable through every larger measured size.

Four nodes is the smallest measured input. These results make no performance
or break-even claim below 4 nodes, outside the measured 4–2048 matrix, or
beyond the exact signed-i64 / finite-f64 adapter contracts and recorded graph
families.
