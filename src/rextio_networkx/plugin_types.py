"""Feature-owned plugin type registry for the rextio-networkx surface.

Holds the ``PluginType`` / ``BoundaryConversion`` definitions for the two types
of the covered edge-list route:

* :data:`EDGELIST_I64` — the undirected signed-i64 edge list input
  (``rextio_networkx.EdgeListI64``), a Python ``list[tuple[int, int]]``. It
  crosses the boundary as the raw ``Bound<'py, PyList>`` (not an auto-extracted
  ``Vec<(i64, i64)>``): the injected helper extracts each node label to ``i64``
  itself so it can reject a Python ``bool`` label at the boundary. bool is an
  ``int`` subclass, so a by-value ``Vec<(i64, i64)>`` extraction would silently
  coerce ``True``/``False`` to ``1``/``0`` and diverge in element type from the
  NetworkX fallback; an out-of-i64 label raises ``OverflowError`` there.
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

# The edge list crosses the boundary as the raw ``Bound<'py, PyList>``, so the
# injected helper controls how each node label is extracted (``param_expr`` is
# the identity). It rejects a Python ``bool`` label with ``TypeError`` — bool is
# an ``int`` subclass, so a by-value ``Vec<(i64, i64)>`` extraction would
# silently coerce ``True``/``False`` to ``1``/``0`` and diverge in element type
# from the NetworkX fallback — and a label outside the i64 range raises
# ``OverflowError``. Both are deterministic, fail-closed runtime type-contract
# violations (not analysis-time rejections and not per-call fallbacks).
_EDGELIST_CONVERSION = BoundaryConversion(
    param_rust="pyo3::Bound<'py, pyo3::types::PyList>",
    param_expr="{param}",
    # Return side is unused on the covered surface (the adapter returns a
    # ComponentList); it must be a valid PyO3 return, so mirror the input's
    # Bound<PyList> with the identity conversion.
    return_rust="pyo3::Bound<'py, pyo3::types::PyList>",
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
        rust_type="pyo3::Bound<'py, pyo3::types::PyList>",
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
