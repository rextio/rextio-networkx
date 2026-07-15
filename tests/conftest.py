"""Shared fixtures and sample data for the rextio-networkx test suite.

``pyproject.toml`` puts ``src`` and the repo root on ``pythonpath``, so tests
import ``rextio_networkx`` directly. This module exposes the covered-semantics
sample edge lists once, so the unit tests and the real-Cargo certification test
exercise the same cases (empty, duplicates/self-loop, negative labels, multiple
components, insertion order).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

CORE_ROOT = Path("/Volumes/Data/workspace/rextio/rextio-core-next").resolve()
CORE_SRC = CORE_ROOT / "src"
CORE_SHA = "2bd1d1da0cf59e97d1659606bcb1ec12491e032c"

# Collection must use the frozen source checkout, never a released/global core.
sys.path.insert(0, str(CORE_SRC))
import rextio  # noqa: E402
from rextio.plugins.api import PLUGIN_API_VERSION  # noqa: E402

_actual_sha = subprocess.run(
    ["git", "-C", str(CORE_ROOT), "rev-parse", "HEAD"],
    capture_output=True,
    text=True,
    check=True,
).stdout.strip()
if _actual_sha != CORE_SHA:
    raise RuntimeError(f"WP-2 requires core {CORE_SHA}, found {_actual_sha}")
if PLUGIN_API_VERSION != "1.3":
    raise RuntimeError(f"WP-2 requires plugin API 1.3, found {PLUGIN_API_VERSION}")
if not Path(rextio.__file__).resolve().is_relative_to(CORE_SRC):
    raise RuntimeError(f"WP-2 imported core outside frozen checkout: {rextio.__file__}")

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
