"""Rust helper-text for the connected-components edge-list lowering.

Pure string functions (no NetworkX/petgraph import in Python): each returns one
module-level Rust ``fn`` item that core codegen splices into the generated
crate, deduplicated by exact text. The main helper takes the interpreter token
and the raw Python edge list, extracts each node label to ``i64`` at the
boundary (rejecting a Python ``bool``, which is an ``int`` subclass and would
otherwise silently coerce ``True``/``False`` to ``1``/``0`` and diverge in
element type from the NetworkX fallback), builds an immutable local ``petgraph``
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
_LABEL_HELPER_NAME = "__rxtnx_node_label_i64"


def cc_call_name() -> str:
    """Return the Rust helper function name for the i64 edge-list route."""
    return _HELPER_NAME


def cc_helpers() -> tuple[str, ...]:
    """Return the petgraph helper ``fn`` texts: node-label extractor then main."""
    return (_node_label_helper(), _cc_helper())


def _node_label_helper() -> str:
    """Return the boundary node-label extractor ``fn`` text.

    Rejects a Python ``bool`` node label with ``TypeError`` (bool is an ``int``
    subclass, so PyO3 would silently coerce ``True``/``False`` to ``1``/``0``,
    and the native leg would then diverge from the NetworkX fallback in element
    *type* — ``int`` vs ``bool`` — while still comparing equal through set
    ``==``). A non-integer label raises ``TypeError`` and an out-of-i64 label
    raises ``OverflowError`` through the ``extract`` — both deterministic,
    fail-closed type-contract violations, never a silent coercion.
    """
    return f"""fn {_LABEL_HELPER_NAME}(label: &pyo3::Bound<'_, pyo3::types::PyAny>) -> pyo3::PyResult<i64> {{
    // A Python bool is an int subclass: extracting it as i64 would silently
    // coerce True/False to 1/0 and diverge in element type from the NetworkX
    // fallback (which keeps bool) while comparing equal through set ==. Refuse
    // it loudly. Non-int labels raise TypeError and out-of-i64 labels raise
    // OverflowError via extract — deterministic fail-closed type-contract
    // violations, never silent.
    if pyo3::types::PyAnyMethods::is_instance_of::<pyo3::types::PyBool>(label) {{
        return Err(pyo3::exceptions::PyTypeError::new_err(
            "rextio-networkx: bool is not a signed-i64 node label (True/False would \
coerce to 1/0 and diverge from the NetworkX fallback); relabel nodes as int",
        ));
    }}
    pyo3::types::PyAnyMethods::extract::<i64>(label)
}}"""


def _cc_helper() -> str:
    """Return the petgraph connected-components helper ``fn`` text."""
    return f"""fn {_HELPER_NAME}<'py>(
    py: pyo3::Python<'py>,
    edges: &pyo3::Bound<'py, pyo3::types::PyList>,
) -> pyo3::PyResult<pyo3::Bound<'py, pyo3::types::PyList>> {{
    use petgraph::graph::{{NodeIndex, UnGraph}};
    use petgraph::unionfind::UnionFind;
    use std::collections::HashMap;

    // Extract the edge list into owned (i64, i64) pairs, validating each node
    // label at the boundary via {_LABEL_HELPER_NAME}: a Python bool is rejected
    // (TypeError) rather than silently coerced, and an out-of-i64 label raises
    // OverflowError. Only after every label is a faithful i64 do we build the
    // graph, so the native leg never diverges silently from the fallback.
    let mut edge_pairs: Vec<(i64, i64)> =
        Vec::with_capacity(pyo3::types::PyListMethods::len(edges));
    for item in pyo3::types::PyListMethods::iter(edges) {{
        let u = {_LABEL_HELPER_NAME}(&pyo3::types::PyAnyMethods::get_item(&item, 0)?)?;
        let v = {_LABEL_HELPER_NAME}(&pyo3::types::PyAnyMethods::get_item(&item, 1)?)?;
        edge_pairs.push((u, v));
    }}

    // Build the immutable local petgraph representation, assigning node indices
    // in NetworkX from_edgelist insertion order (each edge inserts u then v).
    let mut graph: UnGraph<i64, ()> = UnGraph::new_undirected();
    let mut index_of: HashMap<i64, NodeIndex> = HashMap::new();
    let mut order: Vec<i64> = Vec::new();
    for (u, v) in edge_pairs.iter() {{
        for label in [*u, *v] {{
            if !index_of.contains_key(&label) {{
                let idx = graph.add_node(label);
                index_of.insert(label, idx);
                order.push(label);
            }}
        }}
    }}
    for (u, v) in edge_pairs.iter() {{
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
