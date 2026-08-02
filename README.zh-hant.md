# rextio-networkx

<p align="center">
  <img src="./assets/readme/rextio-icon.png" width="96" alt="Rextio 圖示">
</p>

<p align="center"><strong>在常駐 petgraph 圖上執行有邊界的 NetworkX 圖演算法。</strong></p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.ko.md">한국어</a> · <a href="README.zh-hans.md">简体中文</a> · 繁體中文 · <a href="README.ja.md">日本語</a>
</p>

`rextio-networkx` 將精確的 typed adapter 呼叫 lowering 為 Rust，同時保留 NetworkX 3.5 的順序、結果型別與已記錄例外。圖在受支援操作之間維持為原生 `petgraph::UnGraph` 值；只有最終 collection 或 scalar 回到 Python。

> **公開 Alpha 0.1.1**（2026-07-26 發布）。需要 Python 3.11+、`rextio>=0.1.3,<0.2`、外掛 API 1.3 與 `networkx==3.5`。原始 `networkx.*` 寫法和不支援的圖族保留 Python fallback。

## 測量證據

儲存庫中的 generated-wrapper benchmark 在 4–2048 個 requested node 的 **56 個 correctness-valid cell** 上涵蓋 connected components、BFS 與 Dijkstra。記錄的 fallback/native 中位加速為 **2.70×–4.49×**，該測量矩陣中沒有 loss cell。

結果包含 extraction、保序去重、圖建構、演算法、Python 結果實體化/銷毀與 wrapper 開銷。編譯和首次呼叫 warm-up 分開記錄。不宣稱 4 個節點以下、2048 個節點以上、記錄外圖族，或精確 signed-i64 / finite-f64 契約外的效能。0.1.1 新增路由（包含 single-source shortest-path lengths）有 correctness/route 證據，但沒有新的速度聲明。

## 運作方式

```text
typed edge list → resident petgraph graph → supported resident query → Python result
```

constructor 擁有原生無向圖和 insertion-order sidecar。consumer 借用常駐值，不需重建或跨越 Python。常駐圖不能回傳、不能跨 wrapper 呼叫持久化，也不能傳給實體化的 Python consumer。

## 快速開始

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

原生路由必須使用 typed `rextio_networkx` adapter。直接呼叫 `networkx.from_edgelist` 或 `networkx.connected_components` 仍走 fallback。

## 支援的 adapter

| 建立常駐圖 | 使用它 |
| --- | --- |
| `graph_from_edgelist(EdgeListI64)` | `bfs_edges`, `single_source_shortest_path_lengths`, `has_path`, `shortest_path_length` |
| `graph_from_edgelist(EdgeListI64)` | `connected_components`, `number_connected_components`, `is_connected`, `number_of_nodes`, `number_of_edges` |
| `weighted_graph_from_edgelist(WeightedEdgeListI64F64)` | `dijkstra_path_lengths` |

`connected_components_from_edgelist` 仍可作為直接 typed 路由使用。Adapter 只接受 signature 記錄的嚴格 positional、無 option 形式。

## 精確語意

- 輸入由左到右掃描。首次遇到節點與首次插入無向邊決定可觀察順序。重複/反向重複邊不移動；self-loop 在鄰接順序中出現一次。
- 重複 weighted edge 更新現有邊，最後一個權重生效，與 `nx.Graph` 一致。
- BFS 邊、shortest-path dictionary、connected-component list、計數、連通性與圖計數保留文件所述的精確 Python collection/scalar 型別與順序。
- `has_path` 和 `shortest_path_length` 先檢查缺少 source，再檢查缺少 target。斷開的最短路徑保留 NetworkX 3.5 `NetworkXNoPath` 行為。
- Dijkstra 要求有限非負輸入權重（接受 `-0.0`），保留 finalized key 順序。source distance 是精確 `int` `0`，到達的 non-source distance 是 `float`。
- null edge-induced graph 的節點、邊、component 數均為 0；`is_connected` 對它拋出 NetworkX 3.5 `NetworkXPointlessConcept`。

## 輸入邊界與 fallback

- Edge container 必須是精確 `list`；每條邊必須是精確 2-tuple，加權輸入則是精確 3-tuple。
- Node/source/target 必須是精確 Python `int`，不能是 `bool` 或 subclass，且必須適合 signed i64。
- Weight 必須是精確 Python `float`、有限且非負。輸入絕不修改，每次出現都在去重前驗證。
- 錯誤 arity、keyword/option、錯誤 annotation 或 resident type，以及未解析的必要外掛 annotation 都會 fail closed。
- Directed graph、multigraph、object/mixed label、depth/cutoff/weight/method option、原始 NetworkX API 與所有未列操作僅走 fallback。

## Benchmark 證據

參見[方法與限制](benchmarks/README.md)、[完整報告](benchmarks/results/report.md)和保留的[路由證據](benchmarks/results/check.json)。Paired round 交替順序；所有保留 sample 都越過 timing floor，且 correctness digest 相符後才報告加速。未來 loss 也會保留而不隱藏。

## 開發

```bash
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python 'rextio>=0.1.3,<0.2'
uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/python -m pytest
.venv/bin/ruff check src tests benchmarks
.venv/bin/mypy src
```

發布歷史見 [CHANGELOG.md](CHANGELOG.md)。

## 授權條款

MIT
