# rextio-networkx

<p align="center">
  <img src="./assets/readme/rextio-icon.png" width="96" alt="Rextio アイコン">
</p>

<p align="center"><strong>常駐 petgraph グラフ上で動く、範囲を限定した NetworkX グラフアルゴリズム。</strong></p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.ko.md">한국어</a> · <a href="README.zh-hans.md">简体中文</a> · <a href="README.zh-hant.md">繁體中文</a> · 日本語
</p>

`rextio-networkx` は、NetworkX 3.5 の順序、結果型、文書化された例外を保ちながら、厳密な typed adapter 呼び出しを Rust に lowering します。サポート操作間ではグラフをネイティブ `petgraph::UnGraph` 値として保持し、最終 collection または scalar だけを Python に返します。

> **Public Alpha 0.1.1**（2026-07-26 リリース）。Python 3.11+、`rextio>=0.1.3,<0.2`、プラグイン API 1.3、`networkx==3.5` が必要です。raw `networkx.*` 表記と未対応グラフ族は Python fallback です。

## 測定済みの根拠

保存済み generated-wrapper benchmark は、requested node 4–2048 の **56 個の correctness-valid cell** で connected components、BFS、Dijkstra を対象にします。記録された fallback/native の中央値 speedup は **2.70×–4.49×** で、この測定行列に loss cell はありませんでした。

結果には extraction、順序維持 deduplication、グラフ構築、アルゴリズム、Python 結果の materialization/destruction、wrapper overhead が含まれます。コンパイルと初回呼び出し warm-up は別です。4 node 未満、2048 node 超、記録外グラフ族、厳密な signed-i64 / finite-f64 契約外の性能は主張しません。single-source shortest-path lengths を含む 0.1.1 追加 route には correctness/route 根拠がありますが、新しい速度主張はありません。

## 仕組み

```text
typed edge list → resident petgraph graph → supported resident query → Python result
```

constructor はネイティブ無向グラフと insertion-order sidecar を所有します。consumer は再構築や Python 往復なしに常駐値を borrow します。常駐グラフは返却、wrapper 呼び出し間の永続化、materialized Python consumer への受け渡しができません。

## クイックスタート

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

ネイティブ route には typed `rextio_networkx` adapter を使ってください。`networkx.from_edgelist` や `networkx.connected_components` の直接呼び出しは fallback です。

## サポート adapter

| 常駐グラフを構築 | consumer |
| --- | --- |
| `graph_from_edgelist(EdgeListI64)` | `bfs_edges`, `single_source_shortest_path_lengths`, `has_path`, `shortest_path_length` |
| `graph_from_edgelist(EdgeListI64)` | `connected_components`, `number_connected_components`, `is_connected`, `number_of_nodes`, `number_of_edges` |
| `weighted_graph_from_edgelist(WeightedEdgeListI64F64)` | `dijkstra_path_lengths` |

`connected_components_from_edgelist` も直接 typed route として利用できます。Adapter は signature に記載された厳密な positional・option なし形式だけを受け付けます。

## 正確な semantics

- 入力は左から右へ走査します。最初の node 出現と最初の undirected edge 挿入が観測可能な順序を決めます。duplicate/reversed edge は移動せず、self-loop は neighbor 順序に 1 回現れます。
- 重複 weighted edge は既存 edge を更新し、`nx.Graph` と同様に最後の weight が有効です。
- BFS edge、shortest-path dict、connected-component list、count、connectivity、graph count は、文書化された厳密な Python collection/scalar 型と順序を保持します。
- `has_path` と `shortest_path_length` は missing target より missing source を先に検査します。非接続 shortest path は NetworkX 3.5 `NetworkXNoPath` 動作を保持します。
- Dijkstra の入力 weight は finite non-negative でなければならず（`-0.0` は許可）、finalized key 順序を保持します。source distance は厳密な `int` `0`、到達した non-source distance は `float` です。
- null edge-induced graph の node/edge/component 数は 0 です。`is_connected` は NetworkX 3.5 `NetworkXPointlessConcept` を送出します。

## 入力境界と fallback

- Edge container は厳密な `list`、各 edge は厳密な 2-tuple、weighted 入力は厳密な 3-tuple でなければなりません。
- Node/source/target は `bool` や subclass ではない厳密な Python `int` で、signed i64 範囲内でなければなりません。
- Weight は厳密な Python `float`、finite、non-negative でなければなりません。入力は変更されず、すべての occurrence が deduplication 前に検証されます。
- 不正 arity、keyword/option、annotation/resident type、未解決の必須プラグイン annotation は fail closed します。
- Directed graph、multigraph、object/mixed label、depth/cutoff/weight/method option、raw NetworkX API、未掲載の操作は fallback-only です。

## Benchmark 根拠

[方法と制限](benchmarks/README.md)、[完全なレポート](benchmarks/results/report.md)、保存済み[route 根拠](benchmarks/results/check.json)を参照してください。Paired round は順序を交互にし、全 sample が timing floor を超え、correctness digest が一致した場合だけ speedup を報告します。将来の loss も隠さず保持します。

## 開発

```bash
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python 'rextio>=0.1.3,<0.2'
uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/python -m pytest
.venv/bin/ruff check src tests benchmarks
.venv/bin/mypy src
```

リリース履歴は [CHANGELOG.md](CHANGELOG.md) を参照してください。

## ライセンス

MIT
