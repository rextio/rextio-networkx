# Rextio NetworkX product-route benchmark

Primary rows call the generated Rextio wrapper in two persistent processes; they are not standalone Rust/PyO3 measurements.

## Run summary

- Frozen core: `2bd1d1da0cf59e97d1659606bcb1ec12491e032c` / API `1.3`
- Product commit: `242d17828e96e3a2ff1914cd40324c8b7128d981`
- One-time build: 6.640 s
- First-call warm-up range: native 0.011–0.607 ms; fallback 0.027–120.733 ms
- Retained sample minimum: 19.271 ms; timer floor: 41 ns
- Route evidence: `check.json` SHA-256 `69bd6fd77dd26cf4cc2a40ec6536e126954bd0f8c39aa72be7d6e14906a3ea92`
- Observed loss cells: 0 (none)

| Algorithm | Family | Requested nodes | Raw/effective nodes | Raw/effective edges | Reach | Native ms | Fallback ms | Speedup | Ratio CI95 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| components | connected | 4 | 12/4 | 6/3 | 4 | 0.0017 | 0.0060 | 3.65x | [0.273, 0.277] |
| components | disconnected | 4 | 16/4 | 8/4 | 4 | 0.0021 | 0.0074 | 3.50x | [0.283, 0.289] |
| bfs | connected | 4 | 12/4 | 6/3 | 4 | 0.0016 | 0.0060 | 3.88x | [0.256, 0.259] |
| bfs | disconnected | 4 | 16/4 | 8/4 | 1 | 0.0018 | 0.0065 | 3.67x | [0.270, 0.276] |
| bfs | low-reach | 4 | 8/4 | 4/2 | 2 | 0.0012 | 0.0048 | 3.93x | [0.252, 0.256] |
| dijkstra | connected | 4 | 14/4 | 7/3 | 4 | 0.0018 | 0.0079 | 4.49x | [0.221, 0.231] |
| dijkstra | disconnected | 4 | 18/4 | 9/4 | 1 | 0.0020 | 0.0082 | 4.00x | [0.248, 0.252] |
| dijkstra | low-reach | 4 | 10/4 | 5/2 | 2 | 0.0014 | 0.0063 | 4.32x | [0.231, 0.235] |
| components | connected | 8 | 28/8 | 14/7 | 8 | 0.0033 | 0.0108 | 3.29x | [0.301, 0.310] |
| components | disconnected | 8 | 16/8 | 8/4 | 8 | 0.0025 | 0.0082 | 3.25x | [0.306, 0.309] |
| bfs | connected | 8 | 28/8 | 14/7 | 8 | 0.0031 | 0.0111 | 3.64x | [0.271, 0.275] |
| bfs | disconnected | 8 | 16/8 | 8/4 | 2 | 0.0021 | 0.0070 | 3.36x | [0.296, 0.299] |
| bfs | low-reach | 8 | 24/8 | 12/6 | 2 | 0.0026 | 0.0090 | 3.45x | [0.287, 0.293] |
| dijkstra | connected | 8 | 30/8 | 15/7 | 8 | 0.0034 | 0.0140 | 4.09x | [0.243, 0.246] |
| dijkstra | disconnected | 8 | 18/8 | 9/4 | 2 | 0.0024 | 0.0088 | 3.70x | [0.267, 0.273] |
| dijkstra | low-reach | 8 | 26/8 | 13/6 | 2 | 0.0030 | 0.0110 | 3.71x | [0.268, 0.273] |
| components | connected | 16 | 60/16 | 30/15 | 16 | 0.0062 | 0.0193 | 3.14x | [0.318, 0.323] |
| components | disconnected | 16 | 48/16 | 24/12 | 16 | 0.0054 | 0.0171 | 3.17x | [0.313, 0.317] |
| bfs | connected | 16 | 60/16 | 30/15 | 16 | 0.0060 | 0.0202 | 3.37x | [0.293, 0.298] |
| bfs | disconnected | 16 | 48/16 | 24/12 | 4 | 0.0048 | 0.0153 | 3.19x | [0.309, 0.316] |
| bfs | low-reach | 16 | 56/16 | 28/14 | 2 | 0.0054 | 0.0167 | 3.08x | [0.323, 0.330] |
| dijkstra | connected | 16 | 62/16 | 31/15 | 16 | 0.0066 | 0.0252 | 3.79x | [0.261, 0.267] |
| dijkstra | disconnected | 16 | 50/16 | 25/12 | 4 | 0.0053 | 0.0185 | 3.51x | [0.285, 0.289] |
| dijkstra | low-reach | 16 | 58/16 | 29/14 | 2 | 0.0059 | 0.0196 | 3.35x | [0.294, 0.299] |
| components | connected | 32 | 124/32 | 62/31 | 32 | 0.0117 | 0.0357 | 3.04x | [0.328, 0.337] |
| components | disconnected | 32 | 112/32 | 56/28 | 32 | 0.0114 | 0.0338 | 2.95x | [0.334, 0.342] |
| bfs | connected | 32 | 124/32 | 62/31 | 32 | 0.0115 | 0.0377 | 3.29x | [0.304, 0.309] |
| bfs | disconnected | 32 | 112/32 | 56/28 | 8 | 0.0103 | 0.0308 | 2.98x | [0.328, 0.339] |
| bfs | low-reach | 32 | 120/32 | 60/30 | 2 | 0.0108 | 0.0311 | 2.88x | [0.344, 0.348] |
| dijkstra | connected | 32 | 126/32 | 63/31 | 32 | 0.0127 | 0.0471 | 3.72x | [0.266, 0.271] |
| dijkstra | disconnected | 32 | 114/32 | 57/28 | 8 | 0.0110 | 0.0371 | 3.39x | [0.295, 0.301] |
| dijkstra | low-reach | 32 | 122/32 | 61/30 | 2 | 0.0118 | 0.0372 | 3.17x | [0.314, 0.318] |
| components | connected | 128 | 292/128 | 146/127 | 128 | 0.0316 | 0.0931 | 2.95x | [0.337, 0.344] |
| components | disconnected | 128 | 284/128 | 142/124 | 128 | 0.0320 | 0.0926 | 2.89x | [0.343, 0.350] |
| bfs | connected | 128 | 292/128 | 146/127 | 128 | 0.0311 | 0.1020 | 3.28x | [0.300, 0.306] |
| bfs | disconnected | 128 | 284/128 | 142/124 | 32 | 0.0289 | 0.0816 | 2.82x | [0.350, 0.359] |
| bfs | low-reach | 128 | 288/128 | 144/126 | 2 | 0.0282 | 0.0769 | 2.73x | [0.365, 0.374] |
| dijkstra | connected | 128 | 294/128 | 147/127 | 128 | 0.0345 | 0.1294 | 3.75x | [0.265, 0.269] |
| dijkstra | disconnected | 128 | 286/128 | 143/124 | 32 | 0.0319 | 0.0984 | 3.08x | [0.321, 0.327] |
| dijkstra | low-reach | 128 | 290/128 | 145/126 | 2 | 0.0313 | 0.0898 | 2.87x | [0.347, 0.352] |
| components | connected | 512 | 1056/512 | 528/511 | 512 | 0.1148 | 0.3443 | 3.00x | [0.330, 0.337] |
| components | disconnected | 512 | 1050/512 | 525/508 | 512 | 0.1176 | 0.3449 | 2.93x | [0.324, 0.361] |
| bfs | connected | 512 | 1056/512 | 528/511 | 512 | 0.1164 | 0.3864 | 3.32x | [0.298, 0.305] |
| bfs | disconnected | 512 | 1050/512 | 525/508 | 128 | 0.1071 | 0.3060 | 2.86x | [0.347, 0.356] |
| bfs | low-reach | 512 | 1054/512 | 527/510 | 2 | 0.1044 | 0.2829 | 2.71x | [0.362, 0.373] |
| dijkstra | connected | 512 | 1058/512 | 529/511 | 512 | 0.1288 | 0.4846 | 3.76x | [0.263, 0.267] |
| dijkstra | disconnected | 512 | 1052/512 | 526/508 | 128 | 0.1177 | 0.3671 | 3.12x | [0.319, 0.324] |
| dijkstra | low-reach | 512 | 1056/512 | 528/510 | 2 | 0.1152 | 0.3278 | 2.84x | [0.349, 0.353] |
| components | connected | 2048 | 4128/2048 | 2064/2047 | 2048 | 0.4599 | 1.3827 | 3.01x | [0.331, 0.337] |
| components | disconnected | 2048 | 4122/2048 | 2061/2044 | 2048 | 0.4649 | 1.3890 | 2.99x | [0.333, 0.339] |
| bfs | connected | 2048 | 4128/2048 | 2064/2047 | 2048 | 0.4687 | 1.5538 | 3.31x | [0.300, 0.304] |
| bfs | disconnected | 2048 | 4122/2048 | 2061/2044 | 512 | 0.4261 | 1.2420 | 2.92x | [0.339, 0.349] |
| bfs | low-reach | 2048 | 4126/2048 | 2063/2046 | 2 | 0.4199 | 1.1338 | 2.70x | [0.365, 0.372] |
| dijkstra | connected | 2048 | 4130/2048 | 2065/2047 | 2048 | 0.5105 | 1.9671 | 3.85x | [0.258, 0.261] |
| dijkstra | disconnected | 2048 | 4124/2048 | 2062/2044 | 512 | 0.4664 | 1.4701 | 3.15x | [0.316, 0.322] |
| dijkstra | low-reach | 2048 | 4128/2048 | 2064/2046 | 2 | 0.4562 | 1.3073 | 2.87x | [0.343, 0.351] |

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
