# Rextio NetworkX product-route benchmark

Primary rows call the generated Rextio wrapper in two persistent processes; they are not standalone Rust/PyO3 measurements.

## Run summary

- Frozen core: `ac2b79d304f13abaaecaf7714f897574c3b6256f` / API `1.3`
- Product commit: `e40bd64ea43268e6d6722733f1091b40d88eb026`
- One-time build: 8.455 s
- First-call warm-up range: native 0.020–0.811 ms; fallback 0.023–137.332 ms
- Retained sample minimum: 20.083 ms; timer floor: 41 ns
- Route evidence: `check.json` SHA-256 `81c4f4bdb9c84e1ac8ddb9f55637da70cf6361c0afd87edcf60c4fe92eafe074`
- Observed loss cells: 0 (none)

| Algorithm | Family | Requested nodes | Raw/effective nodes | Raw/effective edges | Reach | Native ms | Fallback ms | Speedup | Ratio CI95 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| components | connected | 4 | 12/4 | 6/3 | 4 | 0.0017 | 0.0061 | 3.57x | [0.278, 0.286] |
| components | disconnected | 4 | 16/4 | 8/4 | 4 | 0.0022 | 0.0075 | 3.46x | [0.287, 0.289] |
| bfs | connected | 4 | 12/4 | 6/3 | 4 | 0.0016 | 0.0061 | 3.75x | [0.263, 0.271] |
| bfs | disconnected | 4 | 16/4 | 8/4 | 1 | 0.0018 | 0.0064 | 3.59x | [0.276, 0.281] |
| bfs | low-reach | 4 | 8/4 | 4/2 | 2 | 0.0012 | 0.0048 | 3.90x | [0.255, 0.263] |
| dijkstra | connected | 4 | 14/4 | 7/3 | 4 | 0.0018 | 0.0080 | 4.40x | [0.226, 0.229] |
| dijkstra | disconnected | 4 | 18/4 | 9/4 | 1 | 0.0021 | 0.0082 | 3.92x | [0.253, 0.258] |
| dijkstra | low-reach | 4 | 10/4 | 5/2 | 2 | 0.0015 | 0.0063 | 4.20x | [0.236, 0.241] |
| components | connected | 8 | 28/8 | 14/7 | 8 | 0.0034 | 0.0106 | 3.17x | [0.314, 0.317] |
| components | disconnected | 8 | 16/8 | 8/4 | 8 | 0.0026 | 0.0082 | 3.22x | [0.310, 0.317] |
| bfs | connected | 8 | 28/8 | 14/7 | 8 | 0.0031 | 0.0110 | 3.52x | [0.283, 0.291] |
| bfs | disconnected | 8 | 16/8 | 8/4 | 2 | 0.0021 | 0.0069 | 3.23x | [0.307, 0.311] |
| bfs | low-reach | 8 | 24/8 | 12/6 | 2 | 0.0027 | 0.0089 | 3.31x | [0.300, 0.305] |
| dijkstra | connected | 8 | 30/8 | 15/7 | 8 | 0.0035 | 0.0141 | 4.00x | [0.248, 0.251] |
| dijkstra | disconnected | 8 | 18/8 | 9/4 | 2 | 0.0024 | 0.0089 | 3.65x | [0.273, 0.277] |
| dijkstra | low-reach | 8 | 26/8 | 13/6 | 2 | 0.0030 | 0.0111 | 3.66x | [0.272, 0.276] |
| components | connected | 16 | 60/16 | 30/15 | 16 | 0.0064 | 0.0192 | 3.02x | [0.329, 0.341] |
| components | disconnected | 16 | 48/16 | 24/12 | 16 | 0.0055 | 0.0170 | 3.10x | [0.319, 0.328] |
| bfs | connected | 16 | 60/16 | 30/15 | 16 | 0.0061 | 0.0199 | 3.27x | [0.300, 0.309] |
| bfs | disconnected | 16 | 48/16 | 24/12 | 4 | 0.0050 | 0.0155 | 3.13x | [0.317, 0.323] |
| bfs | low-reach | 16 | 56/16 | 28/14 | 2 | 0.0056 | 0.0167 | 3.01x | [0.328, 0.336] |
| dijkstra | connected | 16 | 62/16 | 31/15 | 16 | 0.0069 | 0.0256 | 3.73x | [0.265, 0.270] |
| dijkstra | disconnected | 16 | 50/16 | 25/12 | 4 | 0.0055 | 0.0186 | 3.36x | [0.295, 0.303] |
| dijkstra | low-reach | 16 | 58/16 | 29/14 | 2 | 0.0060 | 0.0199 | 3.35x | [0.294, 0.302] |
| components | connected | 32 | 124/32 | 62/31 | 32 | 0.0123 | 0.0357 | 2.89x | [0.343, 0.347] |
| components | disconnected | 32 | 112/32 | 56/28 | 32 | 0.0115 | 0.0339 | 2.93x | [0.339, 0.347] |
| bfs | connected | 32 | 124/32 | 62/31 | 32 | 0.0119 | 0.0378 | 3.19x | [0.307, 0.317] |
| bfs | disconnected | 32 | 112/32 | 56/28 | 8 | 0.0106 | 0.0307 | 2.89x | [0.339, 0.349] |
| bfs | low-reach | 32 | 120/32 | 60/30 | 2 | 0.0110 | 0.0314 | 2.85x | [0.346, 0.363] |
| dijkstra | connected | 32 | 126/32 | 63/31 | 32 | 0.0130 | 0.0475 | 3.65x | [0.272, 0.275] |
| dijkstra | disconnected | 32 | 114/32 | 57/28 | 8 | 0.0113 | 0.0372 | 3.28x | [0.302, 0.309] |
| dijkstra | low-reach | 32 | 122/32 | 61/30 | 2 | 0.0120 | 0.0369 | 3.07x | [0.324, 0.329] |
| components | connected | 128 | 292/128 | 146/127 | 128 | 0.0320 | 0.0940 | 2.94x | [0.334, 0.349] |
| components | disconnected | 128 | 284/128 | 142/124 | 128 | 0.0323 | 0.0938 | 2.90x | [0.345, 0.350] |
| bfs | connected | 128 | 292/128 | 146/127 | 128 | 0.0310 | 0.1021 | 3.30x | [0.302, 0.314] |
| bfs | disconnected | 128 | 284/128 | 142/124 | 32 | 0.0291 | 0.0821 | 2.82x | [0.346, 0.356] |
| bfs | low-reach | 128 | 288/128 | 144/126 | 2 | 0.0286 | 0.0775 | 2.71x | [0.364, 0.381] |
| dijkstra | connected | 128 | 294/128 | 147/127 | 128 | 0.0348 | 0.1325 | 3.80x | [0.262, 0.273] |
| dijkstra | disconnected | 128 | 286/128 | 143/124 | 32 | 0.0323 | 0.1004 | 3.11x | [0.314, 0.324] |
| dijkstra | low-reach | 128 | 290/128 | 145/126 | 2 | 0.0316 | 0.0895 | 2.83x | [0.352, 0.357] |
| components | connected | 512 | 1056/512 | 528/511 | 512 | 0.1175 | 0.3457 | 2.94x | [0.328, 0.341] |
| components | disconnected | 512 | 1050/512 | 525/508 | 512 | 0.1196 | 0.3455 | 2.89x | [0.333, 0.349] |
| bfs | connected | 512 | 1056/512 | 528/511 | 512 | 0.1180 | 0.3838 | 3.25x | [0.305, 0.310] |
| bfs | disconnected | 512 | 1050/512 | 525/508 | 128 | 0.1074 | 0.3074 | 2.86x | [0.343, 0.351] |
| bfs | low-reach | 512 | 1054/512 | 527/510 | 2 | 0.1057 | 0.2862 | 2.71x | [0.363, 0.373] |
| dijkstra | connected | 512 | 1058/512 | 529/511 | 512 | 0.1294 | 0.4855 | 3.75x | [0.264, 0.267] |
| dijkstra | disconnected | 512 | 1052/512 | 526/508 | 128 | 0.1194 | 0.3649 | 3.05x | [0.324, 0.330] |
| dijkstra | low-reach | 512 | 1056/512 | 528/510 | 2 | 0.1155 | 0.3268 | 2.83x | [0.351, 0.357] |
| components | connected | 2048 | 4128/2048 | 2064/2047 | 2048 | 0.4635 | 1.3760 | 2.97x | [0.336, 0.340] |
| components | disconnected | 2048 | 4122/2048 | 2061/2044 | 2048 | 0.4632 | 1.3790 | 2.98x | [0.334, 0.339] |
| bfs | connected | 2048 | 4128/2048 | 2064/2047 | 2048 | 0.4797 | 1.5468 | 3.22x | [0.307, 0.345] |
| bfs | disconnected | 2048 | 4122/2048 | 2061/2044 | 512 | 0.4279 | 1.2387 | 2.90x | [0.341, 0.348] |
| bfs | low-reach | 2048 | 4126/2048 | 2063/2046 | 2 | 0.4194 | 1.1343 | 2.70x | [0.367, 0.375] |
| dijkstra | connected | 2048 | 4130/2048 | 2065/2047 | 2048 | 0.5127 | 1.9460 | 3.80x | [0.259, 0.266] |
| dijkstra | disconnected | 2048 | 4124/2048 | 2062/2044 | 512 | 0.4717 | 1.4538 | 3.08x | [0.321, 0.327] |
| dijkstra | low-reach | 2048 | 4128/2048 | 2064/2046 | 2 | 0.4602 | 1.3016 | 2.83x | [0.346, 0.357] |

## Sustained measured break-even

- `bfs/connected`: 4
- `bfs/disconnected`: 4
- `bfs/low-reach`: 4
- `components/connected`: 4
- `components/disconnected`: 4
- `dijkstra/connected`: 4
- `dijkstra/disconnected`: 4
- `dijkstra/low-reach`: 4

Sustained break-even is the first measured size whose paired-bootstrap 95% CI for log(native/fallback) is wholly below zero and remains so at every larger measured size in that family; `none` is not interpolated.

## Loss cells

- None at the measured sizes; this is a measured result, not a claim below the smallest size.

## Explicit non-claims

- Compilation is excluded from steady-state latency and reported separately.
- No standalone PyO3 or Rust diagnostic row is presented as product speedup.
- Results apply only to the exact signed-i64 / finite-f64 adapter contracts.
- A correctness digest mismatch invalidates the cell and suppresses speedup.
