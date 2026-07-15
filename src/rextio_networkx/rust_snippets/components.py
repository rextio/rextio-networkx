"""Rust helper for the retained WP-1 connected-components route."""

from __future__ import annotations

from rextio_networkx.rust_snippets.traversal import traversal_support

_HELPER_NAME = "__rxtnx_connected_components_i64"


def cc_call_name() -> str:
    """Return the connected-components helper name."""
    return _HELPER_NAME


def cc_helpers() -> tuple[str, ...]:
    """Return shared parsing/graph support plus the components helper."""
    return (traversal_support(), _cc_helper())


def _cc_helper() -> str:
    return f"""fn {_HELPER_NAME}<'py>(
    py: pyo3::Python<'py>,
    edges: &RxtNxEdgeListI64,
) -> pyo3::PyResult<pyo3::Bound<'py, pyo3::types::PyList>> {{
    use petgraph::unionfind::UnionFind;
    use pyo3::types::{{PyListMethods, PySetMethods}};
    use std::collections::HashMap;

    let graph = __rxtnx_graph_from_edgelist_i64(edges);
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


__all__ = ["cc_call_name", "cc_helpers"]
