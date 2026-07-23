"""Generated Rust support for exact ordered NetworkX traversal routes."""

from __future__ import annotations

GRAPH_FROM_EDGELIST = "__rxtnx_graph_from_edgelist_i64"
WEIGHTED_GRAPH_FROM_EDGELIST = "__rxtnx_weighted_graph_from_edgelist_i64_f64"
BFS_EDGES = "__rxtnx_bfs_edges_i64"
SHORTEST_PATH_LENGTHS = "__rxtnx_single_source_shortest_path_lengths_i64"
HAS_PATH = "__rxtnx_has_path_i64"
DIJKSTRA_LENGTHS = "__rxtnx_dijkstra_lengths_i64_f64"


def edge_list_struct_helper() -> str:
    """Define the native unweighted boundary representation."""
    return r"""struct RxtNxEdgeListI64 {
    edges: Vec<(i64, i64)>,
}"""


def weighted_edge_list_struct_helper() -> str:
    """Define the native weighted boundary representation."""
    return r"""struct RxtNxWeightedEdgeListI64F64 {
    edges: Vec<(i64, i64, f64)>,
}"""


def graph_struct_helper() -> str:
    """Define the unweighted resident graph and insertion-order sidecars."""
    return r"""struct RxtNxGraphI64 {
    graph: petgraph::graph::UnGraph<i64, ()>,
    node_order: Vec<petgraph::graph::NodeIndex>,
    adjacency_order: Vec<Vec<petgraph::graph::NodeIndex>>,
    index_of: std::collections::HashMap<i64, petgraph::graph::NodeIndex>,
}"""


def weighted_graph_struct_helper() -> str:
    """Define the weighted resident graph and insertion-order sidecars."""
    return r"""struct RxtNxWeightedGraphI64F64 {
    graph: petgraph::graph::UnGraph<i64, f64>,
    node_order: Vec<petgraph::graph::NodeIndex>,
    adjacency_order:
        Vec<Vec<(petgraph::graph::NodeIndex, petgraph::graph::EdgeIndex)>>,
    index_of: std::collections::HashMap<i64, petgraph::graph::NodeIndex>,
}"""


def exact_i64_helper() -> str:
    """Define strict exact-int extraction shared by node-bearing boundaries."""
    return r"""fn __rxtnx_parse_exact_i64(
    value: &pyo3::Bound<'_, pyo3::types::PyAny>,
    location: &str,
) -> pyo3::PyResult<i64> {
    use pyo3::types::PyAnyMethods;
    if !value.is_exact_instance_of::<pyo3::types::PyInt>() {
        return Err(pyo3::exceptions::PyTypeError::new_err(format!(
            "rextio-networkx: {} must be an exact int",
            location,
        )));
    }
    value.extract::<i64>().map_err(|_| {
        pyo3::exceptions::PyOverflowError::new_err(format!(
            "rextio-networkx: {} is outside signed-i64 range",
            location,
        ))
    })
}"""


def source_parser_helper() -> str:
    """Define the strict NodeI64 parameter conversion."""
    return r"""fn __rxtnx_parse_source_i64(
    _py: pyo3::Python<'_>,
    value: &pyo3::Bound<'_, pyo3::types::PyAny>,
) -> pyo3::PyResult<i64> {
    __rxtnx_parse_exact_i64(value, "source")
}"""


def edge_list_parser_helper() -> str:
    """Define the strict ordered EdgeListI64 parameter conversion."""
    return r"""fn __rxtnx_parse_edgelist_i64(
    _py: pyo3::Python<'_>,
    edges: &pyo3::Bound<'_, pyo3::types::PyAny>,
) -> pyo3::PyResult<RxtNxEdgeListI64> {
    use pyo3::types::{PyAnyMethods, PyListMethods, PyTupleMethods};
    if !edges.is_exact_instance_of::<pyo3::types::PyList>() {
        return Err(pyo3::exceptions::PyTypeError::new_err(
            "rextio-networkx: edges must be an exact list",
        ));
    }
    let list = edges.cast::<pyo3::types::PyList>().map_err(|_| {
        pyo3::exceptions::PyTypeError::new_err(
            "rextio-networkx: edges must be an exact list",
        )
    })?;
    let mut parsed = Vec::with_capacity(list.len());
    for (index, item) in list.iter().enumerate() {
        if !item.is_exact_instance_of::<pyo3::types::PyTuple>() {
            return Err(pyo3::exceptions::PyTypeError::new_err(format!(
                "rextio-networkx: edges[{}] must be an exact tuple",
                index,
            )));
        }
        let edge = item.cast::<pyo3::types::PyTuple>().map_err(|_| {
            pyo3::exceptions::PyTypeError::new_err(format!(
                "rextio-networkx: edges[{}] must be an exact tuple",
                index,
            ))
        })?;
        if edge.len() != 2 {
            return Err(pyo3::exceptions::PyTypeError::new_err(format!(
                "rextio-networkx: edges[{}] must contain exactly 2 items",
                index,
            )));
        }
        let u = __rxtnx_parse_exact_i64(
            &edge.get_item(0)?,
            &format!("edges[{}][0]", index),
        )?;
        let v = __rxtnx_parse_exact_i64(
            &edge.get_item(1)?,
            &format!("edges[{}][1]", index),
        )?;
        parsed.push((u, v));
    }
    Ok(RxtNxEdgeListI64 { edges: parsed })
}"""


def weighted_edge_list_parser_helper() -> str:
    """Define the strict ordered WeightedEdgeListI64F64 conversion."""
    return r"""fn __rxtnx_parse_weighted_edgelist_i64_f64(
    _py: pyo3::Python<'_>,
    edges: &pyo3::Bound<'_, pyo3::types::PyAny>,
) -> pyo3::PyResult<RxtNxWeightedEdgeListI64F64> {
    use pyo3::types::{PyAnyMethods, PyListMethods, PyTupleMethods};
    if !edges.is_exact_instance_of::<pyo3::types::PyList>() {
        return Err(pyo3::exceptions::PyTypeError::new_err(
            "rextio-networkx: edges must be an exact list",
        ));
    }
    let list = edges.cast::<pyo3::types::PyList>().map_err(|_| {
        pyo3::exceptions::PyTypeError::new_err(
            "rextio-networkx: edges must be an exact list",
        )
    })?;
    let mut parsed = Vec::with_capacity(list.len());
    for (index, item) in list.iter().enumerate() {
        if !item.is_exact_instance_of::<pyo3::types::PyTuple>() {
            return Err(pyo3::exceptions::PyTypeError::new_err(format!(
                "rextio-networkx: edges[{}] must be an exact tuple",
                index,
            )));
        }
        let edge = item.cast::<pyo3::types::PyTuple>().map_err(|_| {
            pyo3::exceptions::PyTypeError::new_err(format!(
                "rextio-networkx: edges[{}] must be an exact tuple",
                index,
            ))
        })?;
        if edge.len() != 3 {
            return Err(pyo3::exceptions::PyTypeError::new_err(format!(
                "rextio-networkx: edges[{}] must contain exactly 3 items",
                index,
            )));
        }
        let u = __rxtnx_parse_exact_i64(
            &edge.get_item(0)?,
            &format!("edges[{}][0]", index),
        )?;
        let v = __rxtnx_parse_exact_i64(
            &edge.get_item(1)?,
            &format!("edges[{}][1]", index),
        )?;
        let weight_obj = edge.get_item(2)?;
        if !weight_obj.is_exact_instance_of::<pyo3::types::PyFloat>() {
            return Err(pyo3::exceptions::PyTypeError::new_err(format!(
                "rextio-networkx: edges[{}][2] must be an exact float",
                index,
            )));
        }
        let weight = weight_obj.extract::<f64>().map_err(|_| {
            pyo3::exceptions::PyTypeError::new_err(format!(
                "rextio-networkx: edges[{}][2] must be an exact float",
                index,
            ))
        })?;
        if !weight.is_finite() || weight < 0.0 {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "rextio-networkx: edges[{}][2] must be a finite non-negative float",
                index,
            )));
        }
        parsed.push((u, v, weight));
    }
    Ok(RxtNxWeightedEdgeListI64F64 { edges: parsed })
}"""


def edge_list_serializer_helper() -> str:
    """Define the exact ordered EdgeListI64 return conversion."""
    return r"""fn __rxtnx_edgelist_i64_to_py<'py>(
    py: pyo3::Python<'py>,
    edges: &RxtNxEdgeListI64,
) -> pyo3::PyResult<pyo3::Bound<'py, pyo3::types::PyList>> {
    use pyo3::types::{PyListMethods, PyTupleMethods};
    use pyo3::IntoPyObject;

    let result = pyo3::types::PyList::empty(py);
    for &(u, v) in &edges.edges {
        let edge = (u, v).into_pyobject(py)?;
        if edge.len() != 2 {
            return Err(pyo3::exceptions::PyRuntimeError::new_err(
                "rextio-networkx: internal unweighted edge serializer arity mismatch",
            ));
        }
        result.append(edge)?;
    }
    if result.len() != edges.edges.len() {
        return Err(pyo3::exceptions::PyRuntimeError::new_err(
            "rextio-networkx: internal unweighted edge serializer length mismatch",
        ));
    }
    Ok(result)
}"""


def weighted_edge_list_serializer_helper() -> str:
    """Define the exact ordered WeightedEdgeListI64F64 return conversion."""
    return r"""fn __rxtnx_weighted_edgelist_i64_f64_to_py<'py>(
    py: pyo3::Python<'py>,
    edges: &RxtNxWeightedEdgeListI64F64,
) -> pyo3::PyResult<pyo3::Bound<'py, pyo3::types::PyList>> {
    use pyo3::types::{PyListMethods, PyTupleMethods};
    use pyo3::IntoPyObject;

    let result = pyo3::types::PyList::empty(py);
    for &(u, v, weight) in &edges.edges {
        let edge = (u, v, weight).into_pyobject(py)?;
        if edge.len() != 3 {
            return Err(pyo3::exceptions::PyRuntimeError::new_err(
                "rextio-networkx: internal weighted edge serializer arity mismatch",
            ));
        }
        result.append(edge)?;
    }
    if result.len() != edges.edges.len() {
        return Err(pyo3::exceptions::PyRuntimeError::new_err(
            "rextio-networkx: internal weighted edge serializer length mismatch",
        ));
    }
    Ok(result)
}"""


def graph_constructor_helper() -> str:
    """Define ordered construction of the unweighted resident graph."""
    return r"""fn __rxtnx_graph_from_edgelist_i64(edges: &RxtNxEdgeListI64) -> RxtNxGraphI64 {
    use petgraph::graph::{NodeIndex, UnGraph};
    use std::collections::{HashMap, HashSet};

    let mut graph: UnGraph<i64, ()> = UnGraph::new_undirected();
    let mut node_order: Vec<NodeIndex> = Vec::new();
    let mut adjacency_order: Vec<Vec<NodeIndex>> = Vec::new();
    let mut index_of: HashMap<i64, NodeIndex> = HashMap::new();
    let mut edge_keys: HashSet<(usize, usize)> = HashSet::new();

    for &(u, v) in &edges.edges {
        for label in [u, v] {
            if !index_of.contains_key(&label) {
                let node = graph.add_node(label);
                index_of.insert(label, node);
                node_order.push(node);
                adjacency_order.push(Vec::new());
            }
        }
        let a = index_of[&u];
        let b = index_of[&v];
        let key = if a.index() <= b.index() {
            (a.index(), b.index())
        } else {
            (b.index(), a.index())
        };
        if edge_keys.insert(key) {
            graph.add_edge(a, b, ());
            adjacency_order[a.index()].push(b);
            if a != b {
                adjacency_order[b.index()].push(a);
            }
        }
    }
    RxtNxGraphI64 { graph, node_order, adjacency_order, index_of }
}"""


def weighted_graph_constructor_helper() -> str:
    """Define ordered construction of the weighted resident graph."""
    return r"""fn __rxtnx_weighted_graph_from_edgelist_i64_f64(
    edges: &RxtNxWeightedEdgeListI64F64,
) -> RxtNxWeightedGraphI64F64 {
    use petgraph::graph::{EdgeIndex, NodeIndex, UnGraph};
    use std::collections::HashMap;

    let mut graph: UnGraph<i64, f64> = UnGraph::new_undirected();
    let mut node_order: Vec<NodeIndex> = Vec::new();
    let mut adjacency_order: Vec<Vec<(NodeIndex, EdgeIndex)>> = Vec::new();
    let mut index_of: HashMap<i64, NodeIndex> = HashMap::new();
    let mut edge_of: HashMap<(usize, usize), EdgeIndex> = HashMap::new();

    for &(u, v, weight) in &edges.edges {
        for label in [u, v] {
            if !index_of.contains_key(&label) {
                let node = graph.add_node(label);
                index_of.insert(label, node);
                node_order.push(node);
                adjacency_order.push(Vec::new());
            }
        }
        let a = index_of[&u];
        let b = index_of[&v];
        let key = if a.index() <= b.index() {
            (a.index(), b.index())
        } else {
            (b.index(), a.index())
        };
        if let Some(&edge) = edge_of.get(&key) {
            if let Some(stored) = graph.edge_weight_mut(edge) {
                *stored = weight;
            }
        } else {
            let edge = graph.add_edge(a, b, weight);
            edge_of.insert(key, edge);
            adjacency_order[a.index()].push((b, edge));
            if a != b {
                adjacency_order[b.index()].push((a, edge));
            }
        }
    }
    RxtNxWeightedGraphI64F64 {
        graph,
        node_order,
        adjacency_order,
        index_of,
    }
}"""


def networkx_exception_helper() -> str:
    """Define exact construction of NetworkX-owned exception classes."""
    return r"""fn __rxtnx_networkx_exception(
    py: pyo3::Python<'_>,
    class_name: &str,
    message: String,
) -> pyo3::PyResult<pyo3::PyErr> {
    use pyo3::types::{PyAnyMethods, PyModule};
    let networkx = PyModule::import(py, "networkx")?;
    let exception = networkx.getattr(class_name)?.call1((message,))?;
    Ok(pyo3::PyErr::from_value(exception))
}"""


def bfs_helper() -> str:
    """Define exact insertion-ordered BFS materialization."""
    return r"""fn __rxtnx_bfs_edges_i64<'py>(
    py: pyo3::Python<'py>,
    graph: &RxtNxGraphI64,
    source: i64,
) -> pyo3::PyResult<pyo3::Bound<'py, pyo3::types::PyList>> {
    use pyo3::types::PyListMethods;
    use std::collections::VecDeque;

    let Some(&source_node) = graph.index_of.get(&source) else {
        return Err(__rxtnx_networkx_exception(
            py,
            "NetworkXError",
            format!("The node {} is not in the graph.", source),
        )?);
    };
    let result = pyo3::types::PyList::empty(py);
    let mut seen = vec![false; graph.graph.node_count()];
    let mut queue = VecDeque::new();
    seen[source_node.index()] = true;
    queue.push_back(source_node);
    while let Some(parent) = queue.pop_front() {
        for &child in &graph.adjacency_order[parent.index()] {
            if !seen[child.index()] {
                seen[child.index()] = true;
                queue.push_back(child);
                let edge = pyo3::types::PyTuple::new(
                    py,
                    [graph.graph[parent], graph.graph[child]],
                )?;
                result.append(edge)?;
            }
        }
    }
    Ok(result)
}"""


def shortest_path_lengths_helper() -> str:
    """Define source-first, discovery-ordered unweighted shortest-path lengths."""
    return r"""fn __rxtnx_single_source_shortest_path_lengths_i64<'py>(
    py: pyo3::Python<'py>,
    graph: &RxtNxGraphI64,
    source: i64,
) -> pyo3::PyResult<pyo3::Bound<'py, pyo3::types::PyDict>> {
    use pyo3::types::PyDictMethods;
    use std::collections::VecDeque;

    let Some(&source_node) = graph.index_of.get(&source) else {
        return Err(__rxtnx_networkx_exception(
            py,
            "NodeNotFound",
            format!("Source {} is not in G", source),
        )?);
    };
    let result = pyo3::types::PyDict::new(py);
    let mut distances: Vec<Option<i64>> = vec![None; graph.graph.node_count()];
    let mut queue = VecDeque::new();
    distances[source_node.index()] = Some(0);
    result.set_item(graph.graph[source_node], 0_i64)?;
    queue.push_back(source_node);

    while let Some(parent) = queue.pop_front() {
        let parent_distance = distances[parent.index()].ok_or_else(|| {
            pyo3::exceptions::PyRuntimeError::new_err(
                "rextio-networkx: internal BFS distance is missing",
            )
        })?;
        let child_distance = parent_distance.checked_add(1).ok_or_else(|| {
            pyo3::exceptions::PyOverflowError::new_err(
                "rextio-networkx: shortest-path distance is outside signed-i64 range",
            )
        })?;
        for &child in &graph.adjacency_order[parent.index()] {
            if distances[child.index()].is_none() {
                distances[child.index()] = Some(child_distance);
                result.set_item(graph.graph[child], child_distance)?;
                queue.push_back(child);
            }
        }
    }
    Ok(result)
}"""


def has_path_helper() -> str:
    """Define exact unweighted NetworkX 3.5 ``has_path`` semantics."""
    return r"""fn __rxtnx_has_path_i64(
    py: pyo3::Python<'_>,
    graph: &RxtNxGraphI64,
    source: i64,
    target: i64,
) -> pyo3::PyResult<bool> {
    use std::collections::VecDeque;

    let Some(&source_node) = graph.index_of.get(&source) else {
        return Err(__rxtnx_networkx_exception(
            py,
            "NodeNotFound",
            format!("Source {} is not in G", source),
        )?);
    };
    let Some(&target_node) = graph.index_of.get(&target) else {
        return Err(__rxtnx_networkx_exception(
            py,
            "NodeNotFound",
            format!("Target {} is not in G", target),
        )?);
    };
    if source_node == target_node {
        return Ok(true);
    }

    let mut visited = vec![false; graph.graph.node_count()];
    let mut queue = VecDeque::new();
    visited[source_node.index()] = true;
    queue.push_back(source_node);

    while let Some(parent) = queue.pop_front() {
        for &child in &graph.adjacency_order[parent.index()] {
            if child == target_node {
                return Ok(true);
            }
            if !visited[child.index()] {
                visited[child.index()] = true;
                queue.push_back(child);
            }
        }
    }
    Ok(false)
}"""


def dijkstra_helper() -> str:
    """Define counter-ordered Dijkstra and exact Python result materialization."""
    return r"""#[derive(Clone, Copy)]
struct RxtNxDijkstraEntry {
    distance: f64,
    counter: u64,
    node: petgraph::graph::NodeIndex,
}

impl PartialEq for RxtNxDijkstraEntry {
    fn eq(&self, other: &Self) -> bool {
        self.distance == other.distance
            && self.counter == other.counter
            && self.node == other.node
    }
}

impl Eq for RxtNxDijkstraEntry {}

impl PartialOrd for RxtNxDijkstraEntry {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for RxtNxDijkstraEntry {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        use std::cmp::Ordering;
        match other.distance.partial_cmp(&self.distance).unwrap_or(Ordering::Equal) {
            Ordering::Equal => other
                .counter
                .cmp(&self.counter)
                .then_with(|| other.node.index().cmp(&self.node.index())),
            ordering => ordering,
        }
    }
}

fn __rxtnx_dijkstra_lengths_i64_f64<'py>(
    py: pyo3::Python<'py>,
    graph: &RxtNxWeightedGraphI64F64,
    source: i64,
) -> pyo3::PyResult<pyo3::Bound<'py, pyo3::types::PyDict>> {
    use pyo3::types::PyDictMethods;
    use std::collections::BinaryHeap;

    let Some(&source_node) = graph.index_of.get(&source) else {
        return Err(__rxtnx_networkx_exception(
            py,
            "NodeNotFound",
            format!("Node {} not found in graph", source),
        )?);
    };
    let result = pyo3::types::PyDict::new(py);
    let mut seen: Vec<Option<f64>> = vec![None; graph.graph.node_count()];
    let mut finalized = vec![false; graph.graph.node_count()];
    let mut heap = BinaryHeap::new();
    let mut counter = 0_u64;
    seen[source_node.index()] = Some(0.0);
    heap.push(RxtNxDijkstraEntry { distance: 0.0, counter, node: source_node });

    while let Some(entry) = heap.pop() {
        let node = entry.node;
        if finalized[node.index()] {
            continue;
        }
        finalized[node.index()] = true;
        let label = graph.graph[node];
        if node == source_node {
            result.set_item(label, 0_i64)?;
        } else {
            result.set_item(label, entry.distance)?;
        }
        for &(neighbor, edge) in &graph.adjacency_order[node.index()] {
            if finalized[neighbor.index()] {
                continue;
            }
            let weight = *graph.graph.edge_weight(edge).ok_or_else(|| {
                pyo3::exceptions::PyRuntimeError::new_err(
                    "rextio-networkx: internal weighted edge index is invalid",
                )
            })?;
            let candidate = entry.distance + weight;
            let improves = match seen[neighbor.index()] {
                None => true,
                Some(previous) => candidate < previous,
            };
            if improves {
                seen[neighbor.index()] = Some(candidate);
                counter += 1;
                heap.push(RxtNxDijkstraEntry {
                    distance: candidate,
                    counter,
                    node: neighbor,
                });
            }
        }
    }
    Ok(result)
}"""


def node_type_helpers() -> tuple[str, ...]:
    """Return only the support owned by the NodeI64 boundary type."""
    return (exact_i64_helper(), source_parser_helper())


def edge_list_type_helpers() -> tuple[str, ...]:
    """Return only the support owned by the EdgeListI64 boundary type."""
    return (
        edge_list_struct_helper(),
        exact_i64_helper(),
        edge_list_parser_helper(),
        edge_list_serializer_helper(),
    )


def weighted_edge_list_type_helpers() -> tuple[str, ...]:
    """Return support owned by the WeightedEdgeListI64F64 boundary type."""
    return (
        weighted_edge_list_struct_helper(),
        exact_i64_helper(),
        weighted_edge_list_parser_helper(),
        weighted_edge_list_serializer_helper(),
    )


def graph_type_helpers() -> tuple[str, ...]:
    """Return only the support owned by the GraphI64 resident type."""
    return (graph_struct_helper(),)


def weighted_graph_type_helpers() -> tuple[str, ...]:
    """Return only support owned by the WeightedGraphI64F64 resident type."""
    return (weighted_graph_struct_helper(),)


def graph_constructor_helpers() -> tuple[str, ...]:
    """Return exact support needed by an unweighted constructor claim."""
    return (*edge_list_type_helpers(), *graph_type_helpers(), graph_constructor_helper())


def weighted_graph_constructor_helpers() -> tuple[str, ...]:
    """Return exact support needed by a weighted constructor claim."""
    return (
        *weighted_edge_list_type_helpers(),
        *weighted_graph_type_helpers(),
        weighted_graph_constructor_helper(),
    )


def bfs_helpers() -> tuple[str, ...]:
    """Return exact support needed by a BFS consumer claim."""
    return (
        *node_type_helpers(),
        *graph_type_helpers(),
        networkx_exception_helper(),
        bfs_helper(),
    )


def shortest_path_lengths_helpers() -> tuple[str, ...]:
    """Return exact support needed by the unweighted distance consumer claim."""
    return (
        *node_type_helpers(),
        *graph_type_helpers(),
        networkx_exception_helper(),
        shortest_path_lengths_helper(),
    )


def has_path_helpers() -> tuple[str, ...]:
    """Return exact support needed by the resident boolean consumer claim."""
    return (
        *node_type_helpers(),
        *graph_type_helpers(),
        networkx_exception_helper(),
        has_path_helper(),
    )


def dijkstra_helpers() -> tuple[str, ...]:
    """Return exact support needed by a Dijkstra consumer claim."""
    return (
        *node_type_helpers(),
        *weighted_graph_type_helpers(),
        networkx_exception_helper(),
        dijkstra_helper(),
    )


def traversal_helpers() -> tuple[str, ...]:
    """Return the deterministic full support union without duplicate text."""
    return (
        edge_list_struct_helper(),
        weighted_edge_list_struct_helper(),
        graph_struct_helper(),
        weighted_graph_struct_helper(),
        exact_i64_helper(),
        source_parser_helper(),
        edge_list_parser_helper(),
        weighted_edge_list_parser_helper(),
        edge_list_serializer_helper(),
        weighted_edge_list_serializer_helper(),
        graph_constructor_helper(),
        weighted_graph_constructor_helper(),
        networkx_exception_helper(),
        bfs_helper(),
        shortest_path_lengths_helper(),
        has_path_helper(),
        dijkstra_helper(),
    )


def traversal_support() -> str:
    """Return the full support as readable joined text for source inspection."""
    return "\n\n".join(traversal_helpers())


__all__ = [
    "BFS_EDGES",
    "SHORTEST_PATH_LENGTHS",
    "HAS_PATH",
    "DIJKSTRA_LENGTHS",
    "GRAPH_FROM_EDGELIST",
    "WEIGHTED_GRAPH_FROM_EDGELIST",
    "bfs_helpers",
    "dijkstra_helpers",
    "edge_list_type_helpers",
    "graph_constructor_helpers",
    "graph_type_helpers",
    "has_path_helpers",
    "node_type_helpers",
    "shortest_path_lengths_helpers",
    "traversal_helpers",
    "traversal_support",
    "weighted_edge_list_type_helpers",
    "weighted_graph_constructor_helpers",
    "weighted_graph_type_helpers",
]
