# Product-route benchmarks

`bench_product_routes.py` measures the generated Rextio wrapper, not a
standalone Rust/PyO3 prototype. It builds a fixture against frozen core commit
`ac2b79d304f13abaaecaf7714f897574c3b6256f` (plugin API 1.3), verifies
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
