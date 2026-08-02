# rextio-networkx

<p align="center">
  <img src="./assets/readme/rextio-icon.png" width="96" alt="Rextio 图标">
</p>

<p align="center"><strong>在常驻 petgraph 图上运行有边界的 NetworkX 图算法。</strong></p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.ko.md">한국어</a> · 简体中文 · <a href="README.zh-hant.md">繁體中文</a> · <a href="README.ja.md">日本語</a>
</p>

`rextio-networkx` 将精确的类型化 adapter 调用降级为 Rust，同时保留 NetworkX 3.5 的顺序、结果类型和已记录异常。图在受支持操作之间保持为原生 `petgraph::UnGraph` 值；只有最终 collection 或 scalar 返回 Python。

> **公开 Alpha 0.1.1**（2026-07-26 发布）。需要 Python 3.11+、`rextio>=0.1.3,<0.2`、插件 API 1.3 和 `networkx==3.5`。原始 `networkx.*` 写法和不支持的图族保留 Python fallback。

## 测量证据

仓库中的 generated-wrapper benchmark 在 4–2048 个 requested node 的 **56 个 correctness-valid cell** 上覆盖 connected components、BFS 和 Dijkstra。记录的 fallback/native 中位加速为 **2.70×–4.49×**，该测量矩阵中没有 loss cell。

结果包括 extraction、保序去重、图构建、算法、Python 结果物化/销毁和 wrapper 开销。编译与首次调用 warm-up 分开记录。不声称 4 个节点以下、2048 个节点以上、记录外图族，或精确 signed-i64 / finite-f64 契约外的性能。0.1.1 新增路由（包括 single-source shortest-path lengths）有 correctness/route 证据，但没有新的速度声明。

## 工作原理

```text
typed edge list → resident petgraph graph → supported resident query → Python result
```

constructor 拥有原生无向图和 insertion-order sidecar。consumer 借用常驻值，无需重建或跨越 Python。常驻图不能返回、不能跨 wrapper 调用持久化，也不能传给物化的 Python consumer。

## 快速开始

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

原生路由必须使用类型化 `rextio_networkx` adapter。直接调用 `networkx.from_edgelist` 或 `networkx.connected_components` 仍走 fallback。

## 支持的 adapter

| 构建常驻图 | 消费它 |
| --- | --- |
| `graph_from_edgelist(EdgeListI64)` | `bfs_edges`, `single_source_shortest_path_lengths`, `has_path`, `shortest_path_length` |
| `graph_from_edgelist(EdgeListI64)` | `connected_components`, `number_connected_components`, `is_connected`, `number_of_nodes`, `number_of_edges` |
| `weighted_graph_from_edgelist(WeightedEdgeListI64F64)` | `dijkstra_path_lengths` |

`connected_components_from_edgelist` 仍可作为直接类型化路由使用。Adapter 只接受签名记录的严格位置参数、无选项形式。

## 精确语义

- 输入从左到右扫描。首次遇到节点和首次插入无向边决定可观察顺序。重复/反向重复边不移动；self-loop 在邻接顺序中出现一次。
- 重复 weighted edge 更新已有边，最后一个权重生效，与 `nx.Graph` 一致。
- BFS 边、shortest-path 字典、connected-component 列表、计数、连通性和图计数保留文档所述的精确 Python collection/scalar 类型与顺序。
- `has_path` 和 `shortest_path_length` 先检查缺失 source，再检查缺失 target。断开的最短路径保留 NetworkX 3.5 `NetworkXNoPath` 行为。
- Dijkstra 要求有限非负输入权重（接受 `-0.0`），保留 finalized key 顺序。source distance 是精确 `int` `0`，到达的 non-source distance 是 `float`。
- null edge-induced graph 的节点、边、component 数均为 0；`is_connected` 对它抛出 NetworkX 3.5 `NetworkXPointlessConcept`。

## 输入边界与 fallback

- Edge container 必须是精确 `list`；每条边必须是精确 2-tuple，加权输入则是精确 3-tuple。
- Node/source/target 必须是精确 Python `int`，不能是 `bool` 或子类，并且必须适合 signed i64。
- Weight 必须是精确 Python `float`、有限且非负。输入绝不修改，每次出现都在去重前验证。
- 错误 arity、keyword/option、错误 annotation 或 resident type，以及未解析的必要插件 annotation 都会 fail closed。
- Directed graph、multigraph、object/mixed label、depth/cutoff/weight/method option、原始 NetworkX API 及所有未列操作仅走 fallback。

## Benchmark 证据

参见[方法与限定](benchmarks/README.md)、[完整报告](benchmarks/results/report.md)和保留的[路由证据](benchmarks/results/check.json)。Paired round 交替顺序；所有保留 sample 都越过 timing floor，且 correctness digest 匹配后才报告加速。未来 loss 也会保留而不会隐藏。

## 开发

```bash
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python 'rextio>=0.1.3,<0.2'
uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/python -m pytest
.venv/bin/ruff check src tests benchmarks
.venv/bin/mypy src
```

发布历史见 [CHANGELOG.md](CHANGELOG.md)。

## 许可证

MIT
