"""Focused tests for benchmark result interpretation."""

from __future__ import annotations

import sys
from pathlib import Path

BENCHMARKS_ROOT = Path(__file__).resolve().parents[1] / "benchmarks"
sys.path.insert(0, str(BENCHMARKS_ROOT))

from bench_product_routes import _break_even  # noqa: E402


def _cell(requested_nodes: int, *, valid: bool) -> dict[str, object]:
    cell: dict[str, object] = {
        "algorithm": "bfs",
        "family": "sparse",
        "requested_nodes": requested_nodes,
        "valid": valid,
    }
    if valid:
        cell["paired_ci"] = {"log_ratio_ci95": [-0.5, -0.1]}
    return cell


def test_break_even_does_not_skip_an_invalid_larger_cell() -> None:
    cells = [_cell(4, valid=True), _cell(8, valid=False), _cell(16, valid=True)]

    assert _break_even(cells) == {"bfs/sparse": 16}


def test_break_even_is_none_when_largest_cell_is_invalid() -> None:
    cells = [_cell(4, valid=True), _cell(8, valid=True), _cell(16, valid=False)]

    assert _break_even(cells) == {"bfs/sparse": "none"}


def test_break_even_allows_a_complete_valid_suffix_after_an_invalid_cell() -> None:
    cells = [_cell(4, valid=False), _cell(8, valid=True), _cell(16, valid=True)]

    assert _break_even(cells) == {"bfs/sparse": 8}
