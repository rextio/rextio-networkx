# rextio-networkx

<p align="center">
  <img src="./assets/readme/rextio-icon.png" width="96" alt="Rextio 아이콘">
</p>

<p align="center"><strong>상주 petgraph graph에서 실행되는 한정된 NetworkX graph algorithm.</strong></p>

<p align="center">
  <a href="README.md">English</a> · 한국어 · <a href="README.zh-hans.md">简体中文</a> · <a href="README.zh-hant.md">繁體中文</a> · <a href="README.ja.md">日本語</a>
</p>

`rextio-networkx`는 NetworkX 3.5의 순서, 결과 타입, 문서화된 예외를 보존하면서 정확한 typed adapter 호출을 Rust로 lowering합니다. 지원 연산 사이에서 graph는 네이티브 `petgraph::UnGraph` 값으로 유지되고 최종 collection이나 scalar만 Python으로 돌아옵니다.

> **공개 Alpha 0.1.1** (2026-07-26 릴리스). Python 3.11+, `rextio>=0.1.3,<0.2`, 플러그인 API 1.3, `networkx==3.5`가 필요합니다. raw `networkx.*` 표기와 미지원 graph family는 Python fallback입니다.

## 측정된 근거

저장된 generated-wrapper benchmark는 requested node 4–2048의 **56개 correctness-valid cell**에서 connected components, BFS, Dijkstra를 다룹니다. 기록된 fallback/native 중앙 speedup은 **2.70×–4.49×**였고 이 측정 행렬에는 loss cell이 없었습니다.

결과에는 extraction, 순서 보존 deduplication, graph 구성, algorithm, Python 결과 materialization/destruction, wrapper overhead가 포함됩니다. 컴파일과 첫 호출 warm-up은 별도입니다. 4개 미만 또는 2048개 초과 node, 기록되지 않은 graph family, 정확한 signed-i64 / finite-f64 계약 밖의 성능은 주장하지 않습니다. single-source shortest-path lengths를 포함해 0.1.1에 추가된 route에는 correctness/route 근거만 있고 새 속도 주장은 없습니다.

## 동작 방식

```text
typed edge list → resident petgraph graph → supported resident query → Python result
```

constructor는 네이티브 무방향 graph와 insertion-order sidecar를 소유합니다. consumer는 재구성이나 Python 왕복 없이 상주 값을 borrow합니다. 상주 graph는 반환하거나 wrapper 호출 사이에 보존하거나 materialized Python consumer로 전달할 수 없습니다.

## 빠른 시작

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

네이티브 route에는 typed `rextio_networkx` adapter를 사용하세요. `networkx.from_edgelist`나 `networkx.connected_components` 직접 호출은 fallback입니다.

## 지원 adapter

| 상주 graph 구성 | consumer |
| --- | --- |
| `graph_from_edgelist(EdgeListI64)` | `bfs_edges`, `single_source_shortest_path_lengths`, `has_path`, `shortest_path_length` |
| `graph_from_edgelist(EdgeListI64)` | `connected_components`, `number_connected_components`, `is_connected`, `number_of_nodes`, `number_of_edges` |
| `weighted_graph_from_edgelist(WeightedEdgeListI64F64)` | `dijkstra_path_lengths` |

`connected_components_from_edgelist`도 직접 typed route로 유지됩니다. Adapter는 signature에 문서화된 정확한 positional/no-option 형식만 받습니다.

## 정확한 semantics

- 입력은 왼쪽에서 오른쪽으로 스캔합니다. 첫 node 만남과 첫 undirected edge 삽입이 관찰 가능한 순서를 정합니다. duplicate/reversed edge는 이동하지 않고 self-loop는 neighbor 순서에 한 번 나타납니다.
- 중복 weighted edge는 기존 edge를 갱신하며 마지막 weight가 `nx.Graph`와 같이 적용됩니다.
- BFS edge, shortest-path dict, connected-component list, count, connectivity, graph count는 문서화된 정확한 Python collection/scalar 타입과 순서를 보존합니다.
- `has_path`와 `shortest_path_length`는 missing target보다 missing source를 먼저 검사합니다. 연결되지 않은 shortest path는 NetworkX 3.5 `NetworkXNoPath` 동작을 보존합니다.
- Dijkstra 입력 weight는 finite non-negative여야 하며 (`-0.0` 허용), finalized key 순서를 보존합니다. source distance는 정확한 `int` `0`, 도달한 non-source distance는 `float`입니다.
- null edge-induced graph의 node/edge/component 수는 0입니다. `is_connected`는 NetworkX 3.5 `NetworkXPointlessConcept`를 발생시킵니다.

## 입력 경계와 fallback

- Edge container는 정확한 `list`, 각 edge는 정확한 2-tuple, weighted 입력은 정확한 3-tuple이어야 합니다.
- Node/source/target은 `bool`이나 subclass가 아닌 정확한 Python `int`이며 signed i64 범위여야 합니다.
- Weight는 정확한 Python `float`, finite, non-negative여야 합니다. 입력은 변경되지 않고 모든 occurrence가 deduplication 전에 검증됩니다.
- 잘못된 arity, keyword/option, annotation/resident type, 해결되지 않은 필수 플러그인 annotation은 fail closed합니다.
- Directed graph, multigraph, object/mixed label, depth/cutoff/weight/method option, raw NetworkX API, 목록 밖의 연산은 fallback-only입니다.

## Benchmark 근거

[방법과 한계](benchmarks/README.md), [전체 보고서](benchmarks/results/report.md), 보존된 [route 근거](benchmarks/results/check.json)를 참고하세요. Paired round는 순서를 번갈아 사용하고 모든 sample은 timing floor를 넘으며 correctness digest가 일치해야 speedup이 보고됩니다. 향후 loss도 숨기지 않고 보존합니다.

## 개발

```bash
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python 'rextio>=0.1.3,<0.2'
uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/python -m pytest
.venv/bin/ruff check src tests benchmarks
.venv/bin/mypy src
```

릴리스 이력은 [CHANGELOG.md](CHANGELOG.md)를 참고하세요.

## 라이선스

MIT
