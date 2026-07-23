"""Focused tests for benchmark result interpretation."""

from __future__ import annotations

import sys
from pathlib import Path

BENCHMARKS_ROOT = Path(__file__).resolve().parents[1] / "benchmarks"
sys.path.insert(0, str(BENCHMARKS_ROOT))

from bench_product_routes import (  # noqa: E402
    KERNELS,
    _break_even,
    _format_core_provenance_line,
)


def test_shortest_path_lengths_benchmark_smoke_is_non_timed_and_typed() -> None:
    assert "def shortest_path_lengths_product(" in KERNELS
    assert "ShortestPathLengthsI64" in KERNELS


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


def test_provenance_line_reports_installed_package_not_none_core_sha() -> None:
    """Normal installed-core path must not render ``Frozen core: None``."""
    line = _format_core_provenance_line(
        {
            "rextio_version": "0.1.3",
            "core_sha": None,
            "plugin_api": "1.3",
            "rextio_file": "/site-packages/rextio/__init__.py",
            "rextio_core_root": None,
        }
    )

    assert line == (
        "- Installed rextio: `0.1.3` at `/site-packages/rextio/__init__.py` / API `1.3`"
    )
    assert "None" not in line
    assert "Frozen core" not in line


def test_provenance_line_reports_frozen_core_sha_from_checkout_override() -> None:
    """REXTIO_CORE_ROOT checkout with git records frozen SHA and source path."""
    line = _format_core_provenance_line(
        {
            "rextio_version": "0.1.3",
            "core_sha": "2bd1d1da0cf59e97d1659606bcb1ec12491e032c",
            "plugin_api": "1.3",
            "rextio_file": "/checkout/src/rextio/__init__.py",
            "rextio_core_root": "/checkout",
        }
    )

    assert line == (
        "- Frozen core: `2bd1d1da0cf59e97d1659606bcb1ec12491e032c` from `/checkout` "
        "(source `/checkout/src/rextio/__init__.py`) / API `1.3`"
    )


def test_provenance_line_reports_checkout_without_git_sha() -> None:
    """Override without a ``.git`` directory still reports root and import path."""
    line = _format_core_provenance_line(
        {
            "rextio_version": "0.1.3",
            "core_sha": None,
            "plugin_api": "1.3",
            "rextio_file": "/checkout/src/rextio/__init__.py",
            "rextio_core_root": "/checkout",
        }
    )

    assert line == (
        "- Core checkout: `/checkout` "
        "(source `/checkout/src/rextio/__init__.py`, package `0.1.3`) / API `1.3`"
    )
    assert "None" not in line
