"""Feature-owned plugin type registry for the rextio-networkx surface.

Holds the ``PluginType`` / ``BoundaryConversion`` definitions for the two types
of the covered edge-list route:

* :data:`EDGELIST_I64` — the undirected signed-i64 edge list input
  (``rextio_networkx.EdgeListI64``), a Python ``list[tuple[int, int]]`` that
  PyO3 extracts by value into a ``Vec<(i64, i64)>``.
* :data:`COMPONENT_LIST` — the ``list[set[int]]`` output
  (``rextio_networkx.ComponentList``). The claimed helper builds the Python
  ``list[set[int]]`` object directly (it has the ``py`` token in scope), so its
  native representation is already a ``Bound<'py, PyList>`` and the boundary
  return conversion is the identity.

``plugin.py`` exposes this registry via ``type_vocabulary()`` → ``plugin_types()``.
"""

from __future__ import annotations

from rextio.plugins.api import BoundaryConversion, PluginType

from rextio_networkx.diagnostics import COMPONENT_LIST, EDGELIST_I64

# The edge list crosses the boundary as an owned ``Vec<(i64, i64)>`` — PyO3
# extracts a Python ``list[tuple[int, int]]`` by value, so ``param_expr`` is the
# identity. A signed integer node label outside the i64 range raises PyO3's
# ``OverflowError`` at the boundary in native mode (a runtime type-contract
# violation, exactly like passing a str to an int-typed native function); it is
# not representable at analysis time, so it stays outside the claimed surface.
_EDGELIST_CONVERSION = BoundaryConversion(
    param_rust="Vec<(i64, i64)>",
    param_expr="{param}",
    # Return side is unused on the covered surface (the adapter returns a
    # ComponentList) but must be a valid PyO3 return: Vec<(i64, i64)> lowers to
    # a Python list[tuple[int, int]] through IntoPyObject.
    return_rust="Vec<(i64, i64)>",
    return_expr="{value}",
)

# The claimed helper already returns the covered Python-visible object
# (``Bound<'py, PyList>`` of ``PySet`` components), so both the native
# representation and the boundary return type are that Bound and the conversion
# is the identity. The parameter side is unused on the covered surface.
_COMPONENT_LIST_CONVERSION = BoundaryConversion(
    param_rust="pyo3::Bound<'py, pyo3::types::PyList>",
    param_expr="{param}",
    return_rust="pyo3::Bound<'py, pyo3::types::PyList>",
    return_expr="{value}",
)

# Stable, ordered registry: edge-list input first, then the component-list output.
PLUGIN_TYPES: tuple[PluginType, ...] = (
    PluginType(
        key=EDGELIST_I64,
        annotations=("rextio_networkx.EdgeListI64",),
        rust_type="Vec<(i64, i64)>",
        conversion=_EDGELIST_CONVERSION,
    ),
    PluginType(
        key=COMPONENT_LIST,
        annotations=("rextio_networkx.ComponentList",),
        rust_type="pyo3::Bound<'py, pyo3::types::PyList>",
        conversion=_COMPONENT_LIST_CONVERSION,
    ),
)

_PLUGIN_TYPES_BY_KEY: dict[str, PluginType] = {t.key: t for t in PLUGIN_TYPES}


def plugin_types() -> tuple[PluginType, ...]:
    """Return the full plugin type vocabulary (stable public registry API)."""
    return PLUGIN_TYPES


def plugin_type(key: str) -> PluginType:
    """Return the ``PluginType`` for ``key``, or raise ``KeyError``."""
    return _PLUGIN_TYPES_BY_KEY[key]


def plugin_type_keys() -> frozenset[str]:
    """Return the set of type keys this registry owns."""
    return frozenset(_PLUGIN_TYPES_BY_KEY)


__all__ = [
    "PLUGIN_TYPES",
    "plugin_type",
    "plugin_type_keys",
    "plugin_types",
]
