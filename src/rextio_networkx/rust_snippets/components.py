"""Rust helper-text for the connected-components edge-list lowering.

Pure string functions (no NetworkX/petgraph import in Python): each returns one
module-level Rust ``fn`` item that core codegen splices into the generated
crate, deduplicated by exact text. The helper takes the interpreter token and a
borrowed slice of ``(i64, i64)`` edges, builds an immutable local ``petgraph``
``UnGraph`` once, computes connected components with petgraph union-find, and
materializes the exact Python-visible ``list[set[int]]`` result.

Component list order reproduces NetworkX: nodes are assigned indices in
``from_edgelist`` insertion order (each edge inserts ``u`` then ``v``), and a
component is emitted the first time a node in that order is seen — matching
``for v in G`` iteration in ``networkx.connected_components``. Set element order
is not observable through Python set equality.
"""

from __future__ import annotations

_HELPER_NAME = "__rxtnx_connected_components_i64"


def cc_call_name() -> str:
    """Return the Rust helper function name for the i64 edge-list route."""
    return _HELPER_NAME


def cc_helper() -> str:
    """Return the petgraph connected-components helper ``fn`` text."""
    return f"""fn {_HELPER_NAME}<'py>(
    py: pyo3::Python<'py>,
    edges: &[(i64, i64)],
) -> pyo3::PyResult<pyo3::Bound<'py, pyo3::types::PyList>> {{
    use petgraph::graph::{{NodeIndex, UnGraph}};
    use petgraph::unionfind::UnionFind;
    use std::collections::HashMap;

    // Build the immutable local petgraph representation, assigning node indices
    // in NetworkX from_edgelist insertion order (each edge inserts u then v).
    let mut graph: UnGraph<i64, ()> = UnGraph::new_undirected();
    let mut index_of: HashMap<i64, NodeIndex> = HashMap::new();
    let mut order: Vec<i64> = Vec::new();
    for (u, v) in edges.iter() {{
        for label in [*u, *v] {{
            if !index_of.contains_key(&label) {{
                let idx = graph.add_node(label);
                index_of.insert(label, idx);
                order.push(label);
            }}
        }}
    }}
    for (u, v) in edges.iter() {{
        let a = index_of[u];
        let b = index_of[v];
        graph.add_edge(a, b, ());
    }}

    // Connected components via petgraph union-find over the immutable graph.
    let mut vertex_sets = UnionFind::new(graph.node_count());
    for edge in graph.raw_edges() {{
        vertex_sets.union(edge.source().index(), edge.target().index());
    }}

    // Emit components in NetworkX order: first appearance of each root in node
    // insertion order. Node index i corresponds to order[i].
    let mut position_of_root: HashMap<usize, usize> = HashMap::new();
    let mut components: Vec<Vec<i64>> = Vec::new();
    for (i, label) in order.iter().enumerate() {{
        let root = vertex_sets.find(i);
        let position = match position_of_root.get(&root) {{
            Some(existing) => *existing,
            None => {{
                let position = components.len();
                position_of_root.insert(root, position);
                components.push(Vec::new());
                position
            }}
        }};
        components[position].push(*label);
    }}

    // Materialize the covered Python-visible list[set[int]] result.
    let result = pyo3::types::PyList::empty(py);
    for component in components.iter() {{
        let node_set = pyo3::types::PySet::empty(py)?;
        for label in component.iter() {{
            pyo3::types::PySetMethods::add(&node_set, *label)?;
        }}
        pyo3::types::PyListMethods::append(&result, node_set)?;
    }}
    Ok(result)
}}"""
