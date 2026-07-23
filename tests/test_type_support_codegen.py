"""Cargo-free source regressions for NetworkX plugin API 1.3 type support."""

from __future__ import annotations

from rextio.codegen.rust.generator import generate_rust_module
from rextio.ir.nodes import (
    BlockIR,
    CallIR,
    FunctionIR,
    LiteralIR,
    ModuleIR,
    NameIR,
    ParamIR,
    PluginClaimIR,
    ReturnIR,
)
from rextio.ir.types import RxtInt, RxtPluginType

from rextio_networkx.claim.components import CC_RULE, CC_TARGET
from rextio_networkx.diagnostics import (
    COMPONENT_LIST,
    EDGELIST_I64,
    GRAPH_I64,
    NODE_I64,
    WEIGHTED_EDGELIST_I64_F64,
)
from rextio_networkx.plugin import PLUGIN_ID, plugin
from rextio_networkx.plugin_types import plugin_type, plugin_types
from rextio_networkx.rust_snippets.traversal import (
    edge_list_serializer_helper,
    edge_list_struct_helper,
    graph_struct_helper,
    weighted_edge_list_serializer_helper,
    weighted_edge_list_struct_helper,
)


def _ir_type(key: str) -> RxtPluginType:
    declared = plugin_type(key)
    conversion = declared.conversion
    if conversion is None:
        return RxtPluginType(
            key=declared.key,
            native_rust=declared.rust_type,
            resident=True,
            uses=declared.uses,
            helpers=declared.helpers,
        )
    return RxtPluginType(
        key=declared.key,
        native_rust=declared.rust_type,
        param_rust=conversion.param_rust,
        param_expr=conversion.param_expr,
        return_rust=conversion.return_rust,
        return_expr=conversion.return_expr,
        uses=declared.uses,
        helpers=declared.helpers,
    )


IR_TYPES = {declared.key: _ir_type(declared.key) for declared in plugin_types()}


def _function(
    name: str,
    params: list[ParamIR],
    return_type: RxtInt | RxtPluginType,
    body: BlockIR,
) -> FunctionIR:
    return FunctionIR(
        name=name,
        qualname=f"nx_support.{name}",
        module_name="nx_support",
        params=params,
        return_type=return_type,
        body=body,
        plugin_lowered=True,
    )


def _source(*functions: FunctionIR, with_provider: bool = False) -> str:
    return generate_rust_module(
        ModuleIR(functions=list(functions)),
        plugin_providers={PLUGIN_ID: plugin()} if with_provider else {},
        plugin_types_by_key=IR_TYPES,
    )


def test_parameter_only_edgelist_emits_parser_struct_and_serializer_once() -> None:
    probe = _function(
        "parameter_only",
        [ParamIR(name="edges", type=IR_TYPES[EDGELIST_I64])],
        RxtInt(),
        BlockIR(statements=[ReturnIR(LiteralIR(1))]),
    )
    source = _source(probe)
    assert "let edges = __rxtnx_parse_edgelist_i64(py, &edges)?;" in source
    assert source.count(edge_list_struct_helper()) == 1
    assert source.count(edge_list_serializer_helper()) == 1
    assert "RxtNxWeightedEdgeListI64F64" not in source


def test_return_only_weighted_edgelist_emits_owned_support_once() -> None:
    factory = _function(
        "return_only",
        [],
        IR_TYPES[WEIGHTED_EDGELIST_I64_F64],
        BlockIR(statements=[]),
    )
    source = _source(factory)
    assert "-> PyResult<pyo3::Bound<'py, pyo3::types::PyList>>" in source
    assert source.count(weighted_edge_list_struct_helper()) == 1
    assert source.count(weighted_edge_list_serializer_helper()) == 1
    assert "RxtNxEdgeListI64" not in source


def test_resident_signature_emits_only_its_named_graph_definition() -> None:
    consume = _function(
        "consume_graph",
        [ParamIR(name="graph", type=IR_TYPES[GRAPH_I64])],
        RxtInt(),
        BlockIR(statements=[ReturnIR(LiteralIR(5))]),
    )
    source = _source(consume)
    assert "graph: &RxtNxGraphI64" in source
    assert source.count(graph_struct_helper()) == 1
    assert "__rxtnx_parse_edgelist_i64" not in source
    assert "wrap_pyfunction!(nx_support__consume_graph" not in source


def test_signature_and_claim_support_deduplicate_by_exact_text() -> None:
    claim = PluginClaimIR(
        plugin_id=PLUGIN_ID,
        rule_id=CC_RULE,
        kind="call",
        target=CC_TARGET,
        operand_types=(EDGELIST_I64,),
        result_type=COMPONENT_LIST,
    )
    components = _function(
        "components",
        [ParamIR(name="edges", type=IR_TYPES[EDGELIST_I64])],
        IR_TYPES[COMPONENT_LIST],
        BlockIR(
            statements=[
                ReturnIR(
                    CallIR(
                        function=CC_TARGET,
                        args=[NameIR("edges")],
                        claim=claim,
                    )
                )
            ]
        ),
    )
    source = _source(components, with_provider=True)
    # EdgeList support arrives both from the signature and the claim's helper
    # set. Core's API-1.3 exact-text collector must emit every item once.
    for helper in plugin_type(EDGELIST_I64).helpers:
        assert source.count(helper) == 1
    assert source.count("fn __rxtnx_connected_components_i64") == 1


def test_registered_but_unused_networkx_types_emit_no_support() -> None:
    ordinary = FunctionIR(
        name="ordinary",
        qualname="nx_support.ordinary",
        module_name="nx_support",
        params=[],
        return_type=RxtInt(),
        body=BlockIR(statements=[ReturnIR(LiteralIR(7))]),
    )
    source = _source(ordinary)
    for symbol in (
        "RxtNxEdgeListI64",
        "RxtNxWeightedEdgeListI64F64",
        "RxtNxGraphI64",
        "__rxtnx_parse_source_i64",
        "__rxtnx_edgelist_i64_to_py",
        "__rxtnx_weighted_edgelist_i64_f64_to_py",
    ):
        assert symbol not in source


def test_node_signature_owns_exact_parser_without_graph_support() -> None:
    probe = _function(
        "node_probe",
        [ParamIR(name="source", type=IR_TYPES[NODE_I64])],
        RxtInt(),
        BlockIR(statements=[ReturnIR(LiteralIR(1))]),
    )
    source = _source(probe)
    assert "let source = __rxtnx_parse_source_i64(py, &source, \"source\")?;" in source
    assert source.count("fn __rxtnx_parse_exact_i64(") == 1
    assert source.count("fn __rxtnx_parse_source_i64(") == 1
    assert "RxtNxGraphI64" not in source
