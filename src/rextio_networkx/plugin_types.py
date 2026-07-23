"""Plugin API 1.3 type vocabulary for exact traversal chains."""

from __future__ import annotations

from rextio.plugins.api import BoundaryConversion, PluginType

from rextio_networkx.diagnostics import (
    BFS_EDGES_I64,
    COMPONENT_LIST,
    DIJKSTRA_LENGTHS_I64,
    EDGELIST_I64,
    GRAPH_I64,
    NODE_I64,
    SHORTEST_PATH_LENGTHS_I64,
    WEIGHTED_EDGELIST_I64_F64,
    WEIGHTED_GRAPH_I64_F64,
)
from rextio_networkx.rust_snippets.traversal import (
    edge_list_type_helpers,
    graph_type_helpers,
    node_type_helpers,
    weighted_edge_list_type_helpers,
    weighted_graph_type_helpers,
)


def _raw_conversion(*, parser: str, return_rust: str, return_expr: str) -> BoundaryConversion:
    return BoundaryConversion(
        param_rust="pyo3::Bound<'py, pyo3::types::PyAny>",
        param_expr=f"{parser}(py, &{{param}})?",
        return_rust=return_rust,
        return_expr=return_expr,
    )


_EDGE_CONVERSION = _raw_conversion(
    parser="__rxtnx_parse_edgelist_i64",
    return_rust="pyo3::Bound<'py, pyo3::types::PyList>",
    return_expr="__rxtnx_edgelist_i64_to_py(py, &{value})?",
)
_WEIGHTED_EDGE_CONVERSION = _raw_conversion(
    parser="__rxtnx_parse_weighted_edgelist_i64_f64",
    return_rust="pyo3::Bound<'py, pyo3::types::PyList>",
    return_expr="__rxtnx_weighted_edgelist_i64_f64_to_py(py, &{value})?",
)
_NODE_CONVERSION = _raw_conversion(
    parser="__rxtnx_parse_source_i64",
    return_rust="i64",
    return_expr="{value}",
)
_LIST_CONVERSION = BoundaryConversion(
    param_rust="pyo3::Bound<'py, pyo3::types::PyList>",
    param_expr="{param}",
    return_rust="pyo3::Bound<'py, pyo3::types::PyList>",
    return_expr="{value}",
)
_DICT_CONVERSION = BoundaryConversion(
    param_rust="pyo3::Bound<'py, pyo3::types::PyDict>",
    param_expr="{param}",
    return_rust="pyo3::Bound<'py, pyo3::types::PyDict>",
    return_expr="{value}",
)

PLUGIN_TYPES: tuple[PluginType, ...] = (
    PluginType(
        key=NODE_I64,
        annotations=("rextio_networkx.NodeI64",),
        rust_type="i64",
        conversion=_NODE_CONVERSION,
        helpers=node_type_helpers(),
    ),
    PluginType(
        key=EDGELIST_I64,
        annotations=("rextio_networkx.EdgeListI64",),
        rust_type="RxtNxEdgeListI64",
        conversion=_EDGE_CONVERSION,
        helpers=edge_list_type_helpers(),
    ),
    PluginType(
        key=WEIGHTED_EDGELIST_I64_F64,
        annotations=("rextio_networkx.WeightedEdgeListI64F64",),
        rust_type="RxtNxWeightedEdgeListI64F64",
        conversion=_WEIGHTED_EDGE_CONVERSION,
        helpers=weighted_edge_list_type_helpers(),
    ),
    PluginType(
        key=COMPONENT_LIST,
        annotations=("rextio_networkx.ComponentList",),
        rust_type="pyo3::Bound<'py, pyo3::types::PyList>",
        conversion=_LIST_CONVERSION,
    ),
    PluginType(
        key=BFS_EDGES_I64,
        annotations=("rextio_networkx.BfsEdgesI64",),
        rust_type="pyo3::Bound<'py, pyo3::types::PyList>",
        conversion=_LIST_CONVERSION,
    ),
    PluginType(
        key=DIJKSTRA_LENGTHS_I64,
        annotations=("rextio_networkx.DijkstraLengthsI64",),
        rust_type="pyo3::Bound<'py, pyo3::types::PyDict>",
        conversion=_DICT_CONVERSION,
    ),
    PluginType(
        key=SHORTEST_PATH_LENGTHS_I64,
        annotations=("rextio_networkx.ShortestPathLengthsI64",),
        rust_type="pyo3::Bound<'py, pyo3::types::PyDict>",
        conversion=_DICT_CONVERSION,
    ),
    PluginType(
        key=GRAPH_I64,
        annotations=("rextio_networkx.GraphI64",),
        rust_type="RxtNxGraphI64",
        conversion=None,
        helpers=graph_type_helpers(),
    ),
    PluginType(
        key=WEIGHTED_GRAPH_I64_F64,
        annotations=("rextio_networkx.WeightedGraphI64F64",),
        rust_type="RxtNxWeightedGraphI64F64",
        conversion=None,
        helpers=weighted_graph_type_helpers(),
    ),
)

_PLUGIN_TYPES_BY_KEY = {plugin_type.key: plugin_type for plugin_type in PLUGIN_TYPES}


def plugin_types() -> tuple[PluginType, ...]:
    """Return the stable full vocabulary."""
    return PLUGIN_TYPES


def plugin_type(key: str) -> PluginType:
    """Return one registered type by key."""
    return _PLUGIN_TYPES_BY_KEY[key]


def plugin_type_keys() -> frozenset[str]:
    """Return all owned type keys."""
    return frozenset(_PLUGIN_TYPES_BY_KEY)


__all__ = ["PLUGIN_TYPES", "plugin_type", "plugin_type_keys", "plugin_types"]
