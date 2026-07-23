"""Shared fixtures and sample data for the rextio-networkx test suite.

``pyproject.toml`` puts ``src`` and the repo root on ``pythonpath``, so tests
import ``rextio_networkx`` directly. This module exposes the covered-semantics
sample edge lists once, so the unit tests and the real-Cargo certification test
exercise the same cases (empty, duplicates/self-loop, negative labels, multiple
components, insertion order).

By default, tests use the installed ``rextio`` dependency (``rextio>=0.1.3,<0.2``,
plugin API 1.3). Set ``REXTIO_CORE_ROOT`` to a local core checkout only when
developing against an unreleased core tree.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_CORE_ROOT_ENV = "REXTIO_CORE_ROOT"


def _maybe_prepend_core_src() -> Path | None:
    """Optionally put a local core ``src`` on ``sys.path`` before importing rextio."""
    raw = os.environ.get(_CORE_ROOT_ENV)
    if not raw:
        return None
    core_root = Path(raw).expanduser().resolve()
    core_src = core_root / "src"
    if not core_src.is_dir():
        raise RuntimeError(f"{_CORE_ROOT_ENV}={core_root} does not contain a src/ directory")
    sys.path.insert(0, str(core_src))
    return core_root


_optional_core_root = _maybe_prepend_core_src()

import rextio  # noqa: E402
from rextio.plugins.api import PLUGIN_API_VERSION  # noqa: E402
from rextio_networkx.host_compat import require_supported_plugin_api  # noqa: E402

require_supported_plugin_api(PLUGIN_API_VERSION, consumer="rextio-networkx")

if _optional_core_root is not None:
    rextio_file = Path(rextio.__file__).resolve()
    if not rextio_file.is_relative_to(_optional_core_root / "src"):
        raise RuntimeError(f"{_CORE_ROOT_ENV} is set but rextio imported from {rextio_file}")

# Each case names one covered semantic. Every case is an undirected simple-graph
# edge list of signed i64 node labels; expected components are compared against
# NetworkX (unit tests) and the native leg (certification).
COVERED_EDGE_LISTS: dict[str, list[tuple[int, int]]] = {
    "empty": [],
    "single_edge": [(0, 1)],
    "self_loop": [(5, 5)],
    "self_loop_then_edge": [(5, 5), (5, 6)],
    "duplicate_edges": [(0, 1), (0, 1), (1, 2)],
    "chain": [(0, 1), (1, 2), (2, 3)],
    "disconnected": [(0, 1), (1, 2), (10, 11)],
    "negative_labels": [(-3, -4), (-4, -5), (100, -3)],
    "insertion_order": [(7, 8), (9, 9), (8, 7), (1, 2), (2, 3), (3, 1)],
    "reverse_seen_order": [(4, 3), (3, 2), (0, 1)],
    # The full signed-i64 range is in-contract and must round-trip natively; the
    # out-of-range neighbours are fail-closed boundary rejections (see the e2e
    # boundary tests), not covered cases.
    "i64_bounds": [(2**63 - 1, -(2**63)), (0, 2**63 - 1)],
}


@pytest.fixture(params=sorted(COVERED_EDGE_LISTS), ids=sorted(COVERED_EDGE_LISTS))
def covered_case(request: pytest.FixtureRequest) -> list[tuple[int, int]]:
    """Yield each covered-semantics edge list in turn."""
    return COVERED_EDGE_LISTS[request.param]
