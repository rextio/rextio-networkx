"""Rust helper for the retained WP-1 connected-components route."""

from __future__ import annotations

from rextio_networkx.rust_snippets.traversal import (
    graph_constructor_helpers,
    graph_type_helpers,
    networkx_exception_helper,
)

_HELPER_NAME = "__rxtnx_connected_components_i64"
_RESIDENT_HELPER_NAME = "__rxtnx_connected_components_graph_i64"
_COMPONENT_COUNT_HELPER_NAME = "__rxtnx_component_count_i64"
_NUMBER_CONNECTED_COMPONENTS_HELPER_NAME = "__rxtnx_number_connected_components_i64"
_IS_CONNECTED_HELPER_NAME = "__rxtnx_is_connected_i64"


def cc_call_name() -> str:
    """Return the connected-components helper name."""
    return _HELPER_NAME


def cc_helpers() -> tuple[str, ...]:
    """Return shared parsing/graph support plus the components helper."""
    return (*graph_constructor_helpers(), _resident_cc_helper(), _cc_helper())


def resident_cc_call_name() -> str:
    """Return the resident connected-components helper name."""
    return _RESIDENT_HELPER_NAME


def resident_cc_helpers() -> tuple[str, ...]:
    """Return graph support plus the resident component materializer."""
    return (*graph_type_helpers(), _resident_cc_helper())


def number_connected_components_call_name() -> str:
    """Return the resident component-count helper name."""
    return _NUMBER_CONNECTED_COMPONENTS_HELPER_NAME


def number_connected_components_helpers() -> tuple[str, ...]:
    """Return support for exact scalar component-counting."""
    return (*graph_type_helpers(), _component_count_helper(), _number_components_helper())


def is_connected_call_name() -> str:
    """Return the resident connectivity-predicate helper name."""
    return _IS_CONNECTED_HELPER_NAME


def is_connected_helpers() -> tuple[str, ...]:
    """Return support for exact scalar connectivity, including its null error."""
    return (
        *graph_type_helpers(),
        _component_count_helper(),
        networkx_exception_helper(),
        _is_connected_helper(),
    )


def _cc_helper() -> str:
    return f"""fn {_HELPER_NAME}<'py>(
    py: pyo3::Python<'py>,
    edges: &RxtNxEdgeListI64,
) -> pyo3::PyResult<pyo3::Bound<'py, pyo3::types::PyList>> {{
    let graph = __rxtnx_graph_from_edgelist_i64(edges);
    {_RESIDENT_HELPER_NAME}(py, &graph)
}}"""


def _resident_cc_helper() -> str:
    return f"""fn {_RESIDENT_HELPER_NAME}<'py>(
    py: pyo3::Python<'py>,
    graph: &RxtNxGraphI64,
) -> pyo3::PyResult<pyo3::Bound<'py, pyo3::types::PyList>> {{
    use petgraph::unionfind::UnionFind;
    use pyo3::types::{{PyListMethods, PySetMethods}};
    use std::collections::HashMap;

    let mut vertex_sets = UnionFind::new(graph.graph.node_count());
    for edge in graph.graph.raw_edges() {{
        vertex_sets.union(edge.source().index(), edge.target().index());
    }}
    let mut position_of_root: HashMap<usize, usize> = HashMap::new();
    let mut components: Vec<Vec<i64>> = Vec::new();
    for node in &graph.node_order {{
        let root = vertex_sets.find(node.index());
        let position = match position_of_root.get(&root) {{
            Some(existing) => *existing,
            None => {{
                let position = components.len();
                position_of_root.insert(root, position);
                components.push(Vec::new());
                position
            }}
        }};
        components[position].push(graph.graph[*node]);
    }}
    let result = pyo3::types::PyList::empty(py);
    for component in &components {{
        let node_set = pyo3::types::PySet::empty(py)?;
        for &label in component {{
            node_set.add(label)?;
        }}
        result.append(node_set)?;
    }}
    Ok(result)
}}"""


def _component_count_helper() -> str:
    return f"""fn {_COMPONENT_COUNT_HELPER_NAME}(graph: &RxtNxGraphI64) -> usize {{
    use petgraph::unionfind::UnionFind;
    use std::collections::HashSet;

    let mut vertex_sets = UnionFind::new(graph.graph.node_count());
    for edge in graph.graph.raw_edges() {{
        vertex_sets.union(edge.source().index(), edge.target().index());
    }}
    let mut roots = HashSet::with_capacity(graph.graph.node_count());
    for node in &graph.node_order {{
        roots.insert(vertex_sets.find(node.index()));
    }}
    roots.len()
}}"""


def _number_components_helper() -> str:
    return f"""fn {_NUMBER_CONNECTED_COMPONENTS_HELPER_NAME}(
    graph: &RxtNxGraphI64,
) -> pyo3::PyResult<i64> {{
    i64::try_from({_COMPONENT_COUNT_HELPER_NAME}(graph)).map_err(|_| {{
        pyo3::exceptions::PyOverflowError::new_err(
            "rextio-networkx: connected-component count is outside signed-i64 range",
        )
    }})
}}"""


def _is_connected_helper() -> str:
    return f"""fn {_IS_CONNECTED_HELPER_NAME}(
    py: pyo3::Python<'_>,
    graph: &RxtNxGraphI64,
) -> pyo3::PyResult<bool> {{
    if graph.graph.node_count() == 0 {{
        return Err(__rxtnx_networkx_exception(
            py,
            "NetworkXPointlessConcept",
            "Connectivity is undefined for the null graph.".to_owned(),
        )?);
    }}
    Ok({_COMPONENT_COUNT_HELPER_NAME}(graph) == 1)
}}"""


__all__ = [
    "cc_call_name",
    "cc_helpers",
    "is_connected_call_name",
    "is_connected_helpers",
    "number_connected_components_call_name",
    "number_connected_components_helpers",
    "resident_cc_call_name",
    "resident_cc_helpers",
]
