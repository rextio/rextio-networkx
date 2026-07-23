"""Benchmark only generated Rextio wrapper routes against forced fallback.

The parent builds one fixture and drives two persistent mode processes.  Every
timed cell calls the same generated Python wrapper surface; only
``REXTIO_NATIVE_MODE`` differs.  Compilation and warm-up are reported outside
steady-state samples.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import importlib
import json
import math
import os
import platform
import random
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from cases import BenchmarkCase, benchmark_cases

_CORE_ROOT_ENV = "REXTIO_CORE_ROOT"
REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_SRC = REPO_ROOT / "src"
FIXTURE_MODULE = "nx_bench_app.kernels"

KERNELS = """
from rextio_networkx import (
    BfsEdgesI64,
    ComponentList,
    DijkstraLengthsI64,
    EdgeListI64,
    NodeI64,
    WeightedEdgeListI64F64,
    bfs_edges,
    connected_components_from_edgelist,
    dijkstra_path_lengths,
    graph_from_edgelist,
    weighted_graph_from_edgelist,
)


def components_product(edges: EdgeListI64) -> ComponentList:
    return connected_components_from_edgelist(edges)


def bfs_product(edges: EdgeListI64, source: NodeI64) -> BfsEdgesI64:
    return bfs_edges(graph_from_edgelist(edges), source)


def dijkstra_product(
    edges: WeightedEdgeListI64F64,
    source: NodeI64,
) -> DijkstraLengthsI64:
    return dijkstra_path_lengths(weighted_graph_from_edgelist(edges), source)
"""


def _run_text(command: list[str]) -> str:
    return subprocess.run(command, capture_output=True, text=True, check=True).stdout.strip()


def _optional_core_root() -> Path | None:
    """Resolve an optional local core checkout for development overrides."""
    raw = os.environ.get(_CORE_ROOT_ENV)
    if not raw:
        return None
    core_root = Path(raw).expanduser().resolve()
    core_src = core_root / "src"
    if not core_src.is_dir():
        raise RuntimeError(f"{_CORE_ROOT_ENV}={core_root} does not contain a src/ directory")
    return core_root


def _baseline() -> dict[str, object]:
    # Default: installed rextio dependency. Optional REXTIO_CORE_ROOT prepends a
    # local core src tree for development against unreleased cores.
    core_root = _optional_core_root()
    if core_root is not None:
        sys.path.insert(0, str(core_root / "src"))
    import networkx
    import rextio
    import rextio_networkx
    from rextio.plugins.api import PLUGIN_API_VERSION
    from rextio_networkx.host_compat import require_supported_plugin_api

    require_supported_plugin_api(PLUGIN_API_VERSION, consumer="benchmark")
    rextio_file = Path(rextio.__file__).resolve()
    if core_root is not None and not rextio_file.is_relative_to(core_root / "src"):
        raise RuntimeError(f"{_CORE_ROOT_ENV} is set but rextio imported from {rextio_file}")
    core_sha: str | None = None
    if core_root is not None and (core_root / ".git").exists():
        core_sha = _run_text(["git", "-C", str(core_root), "rev-parse", "HEAD"])
    return {
        "rextio_version": getattr(rextio, "__version__", "unknown"),
        "core_sha": core_sha,
        "plugin_api": PLUGIN_API_VERSION,
        "rextio_file": str(rextio_file),
        "rextio_core_root": str(core_root) if core_root is not None else None,
        "plugin_commit": _run_text(["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"]),
        "benchmark_harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "benchmark_cases_sha256": hashlib.sha256(
            (Path(__file__).with_name("cases.py")).read_bytes()
        ).hexdigest(),
        "rextio_networkx_version": rextio_networkx.__version__,
        "rextio_networkx_file": str(Path(rextio_networkx.__file__).resolve()),
        "networkx_version": networkx.__version__,
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cargo": _run_text(["cargo", "--version"]),
        "rustc": _run_text(["rustc", "--version"]),
    }


def _digest(algorithm: str, result: object) -> str:
    if algorithm == "components":
        assert type(result) is list
        signature = [
            {
                "container_type": type(component).__name__,
                "nodes": [[type(node).__name__, node] for node in sorted(component)],
            }
            for component in result
        ]
    elif algorithm == "bfs":
        assert type(result) is list
        signature = [
            [type(edge).__name__, [[type(node).__name__, node] for node in edge]] for edge in result
        ]
    else:
        assert type(result) is dict
        signature = [
            [
                [type(key).__name__, key],
                [
                    type(value).__name__,
                    value.hex() if type(value) is float else str(value),
                ],
            ]
            for key, value in result.items()
        ]
    encoded = json.dumps(signature, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _prepare_worker_call(module: object, case: dict[str, object]) -> tuple[Any, tuple[object, ...]]:
    algorithm = str(case["algorithm"])
    edges = [tuple(edge) for edge in case["edges"]]  # exact tuple boundary input
    if algorithm == "components":
        return getattr(module, "components_product"), (edges,)
    source = case["source"]
    return getattr(module, f"{algorithm}_product"), (edges, source)


def _worker_main(args: argparse.Namespace) -> int:
    os.environ["REXTIO_NATIVE_MODE"] = args.mode
    sys.path.insert(0, args.build_python)
    module = importlib.import_module(FIXTURE_MODULE)
    for line in sys.stdin:
        request = json.loads(line)
        if request["op"] == "close":
            return 0
        case = request["case"]
        iterations = int(request.get("iterations", 1))
        function, call_args = _prepare_worker_call(module, case)
        gc.collect()
        enabled = gc.isenabled()
        gc.disable()
        start = time.perf_counter_ns()
        try:
            for _ in range(iterations):
                materialized_result = function(*call_args)
                # Include result destruction in every timed iteration.  A
                # separate untimed call below supplies the correctness digest.
                del materialized_result
        finally:
            elapsed = time.perf_counter_ns() - start
            if enabled:
                gc.enable()
        verification_result = function(*call_args)
        response = {
            "elapsed_ns": elapsed,
            "iterations": iterations,
            "digest": _digest(str(case["algorithm"]), verification_result),
        }
        print(json.dumps(response, sort_keys=True), flush=True)
    return 0


class ModeWorker:
    """One persistent generated-wrapper process fixed to native or fallback."""

    def __init__(self, mode: str, build_python: Path) -> None:
        env = os.environ.copy()
        env["PYTHONHASHSEED"] = "0"
        # Prefer the installed rextio package; optionally prepend a local core
        # checkout when REXTIO_CORE_ROOT is set for development.
        path_parts = [str(PLUGIN_SRC)]
        core_root = _optional_core_root()
        if core_root is not None:
            path_parts.insert(0, str(core_root / "src"))
        existing = env.get("PYTHONPATH")
        if existing:
            path_parts.append(existing)
        env["PYTHONPATH"] = os.pathsep.join(path_parts)
        self.process = subprocess.Popen(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--worker",
                "--mode",
                mode,
                "--build-python",
                str(build_python),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        self.mode = mode

    def run(self, case: BenchmarkCase, iterations: int) -> dict[str, object]:
        """Run one timed request in this persistent mode process."""
        assert self.process.stdin is not None and self.process.stdout is not None
        request = {"op": "run", "case": case.to_dict(), "iterations": iterations}
        self.process.stdin.write(json.dumps(request, separators=(",", ":")) + "\n")
        self.process.stdin.flush()
        line = self.process.stdout.readline()
        if not line:
            assert self.process.stderr is not None
            stderr = self.process.stderr.read()
            raise RuntimeError(f"{self.mode} benchmark worker exited: {stderr}")
        return json.loads(line)

    def close(self) -> None:
        """Shut the worker down without leaving a child process."""
        if self.process.poll() is None and self.process.stdin is not None:
            self.process.stdin.write('{"op":"close"}\n')
            self.process.stdin.flush()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()


def _timer_floor_ns() -> int:
    previous = time.perf_counter_ns()
    deltas: list[int] = []
    for _ in range(20_000):
        current = time.perf_counter_ns()
        if current > previous:
            deltas.append(current - previous)
        previous = current
    return min(deltas)


def _paired_ci(
    samples: list[dict[str, int]], seed: int, resamples: int = 5_000
) -> dict[str, object]:
    logs = [math.log(sample["native_ns"] / sample["fallback_ns"]) for sample in samples]
    rng = random.Random(seed)
    means = sorted(
        statistics.fmean(logs[rng.randrange(len(logs))] for _ in logs) for _ in range(resamples)
    )
    low = means[int(0.025 * resamples)]
    high = means[min(resamples - 1, int(0.975 * resamples))]
    center = statistics.fmean(logs)
    return {
        "method": "paired bootstrap mean log(native/fallback), 5000 resamples",
        "seed": seed,
        "log_ratio_mean": center,
        "log_ratio_ci95": [low, high],
        "ratio_geomean": math.exp(center),
        "ratio_ci95": [math.exp(low), math.exp(high)],
    }


def _measure_cell(
    case: BenchmarkCase,
    workers: dict[str, ModeWorker],
    *,
    rounds: int,
    target_ns: int,
    seed: int,
) -> dict[str, object]:
    warmups = {mode: worker.run(case, 1) for mode, worker in workers.items()}
    if warmups["native"]["digest"] != warmups["fallback"]["digest"]:
        return {
            **case.to_dict(),
            "valid": False,
            "reason": "native/fallback correctness digest mismatch",
            "warmups": warmups,
            "samples": [],
        }

    iterations = 1
    while True:
        calibration = {mode: worker.run(case, iterations) for mode, worker in workers.items()}
        if min(int(item["elapsed_ns"]) for item in calibration.values()) >= target_ns:
            break
        iterations *= 2

    # A rare fast sample below 10 ms invalidates the attempt; double the common
    # iteration count and recollect every pair so all retained samples comply.
    for _attempt in range(4):
        samples: list[dict[str, int | str]] = []
        all_above_floor = True
        for round_index in range(rounds):
            schedule = ("native", "fallback") if round_index % 2 == 0 else ("fallback", "native")
            outcomes = {mode: workers[mode].run(case, iterations) for mode in schedule}
            native_ns = int(outcomes["native"]["elapsed_ns"])
            fallback_ns = int(outcomes["fallback"]["elapsed_ns"])
            if min(native_ns, fallback_ns) < 10_000_000:
                all_above_floor = False
            samples.append(
                {
                    "round": round_index,
                    "schedule": "AB" if schedule[0] == "native" else "BA",
                    "native_ns": native_ns,
                    "fallback_ns": fallback_ns,
                }
            )
        if all_above_floor:
            break
        iterations *= 2
    else:
        raise RuntimeError(f"could not calibrate every sample above 10 ms: {case.case_id}")

    typed_samples = [
        {"native_ns": int(item["native_ns"]), "fallback_ns": int(item["fallback_ns"])}
        for item in samples
    ]
    native_per_call = [sample["native_ns"] / iterations for sample in typed_samples]
    fallback_per_call = [sample["fallback_ns"] / iterations for sample in typed_samples]
    ci = _paired_ci(typed_samples, seed)
    return {
        **case.to_dict(),
        "valid": True,
        "iterations": iterations,
        "warmups": warmups,
        "correctness_digest": warmups["native"]["digest"],
        "samples": samples,
        "native_median_ns_per_call": statistics.median(native_per_call),
        "fallback_median_ns_per_call": statistics.median(fallback_per_call),
        "median_speedup_fallback_over_native": statistics.median(fallback_per_call)
        / statistics.median(native_per_call),
        "paired_ci": ci,
    }


def _break_even(cells: list[dict[str, object]]) -> dict[str, object]:
    results: dict[str, object] = {}
    groups = sorted({(str(cell["algorithm"]), str(cell["family"])) for cell in cells})
    for algorithm, family in groups:
        group = sorted(
            (cell for cell in cells if cell["algorithm"] == algorithm and cell["family"] == family),
            key=lambda cell: int(cell["requested_nodes"]),
        )
        sustained: int | None = None
        for index, cell in enumerate(group):
            suffix = group[index:]
            if cell["valid"] is True and all(
                item["valid"] is True and float(item["paired_ci"]["log_ratio_ci95"][1]) < 0.0  # type: ignore[index]
                for item in suffix
            ):
                sustained = int(cell["requested_nodes"])
                break
        results[f"{algorithm}/{family}"] = sustained if sustained is not None else "none"
    return results


def _format_core_provenance_line(provenance: dict[str, object]) -> str:
    """Render a truthful Markdown line for core/package provenance.

    Installed public rextio records ``core_sha=None`` plus package version and
    import path. A ``REXTIO_CORE_ROOT`` checkout records the frozen core SHA
    (when the checkout has ``.git``) and the override root/source path.
    """
    plugin_api = provenance["plugin_api"]
    core_sha = provenance.get("core_sha")
    core_root = provenance.get("rextio_core_root")
    rextio_file = provenance.get("rextio_file", "unknown")
    rextio_version = provenance.get("rextio_version", "unknown")

    if core_root is not None:
        if core_sha is not None:
            return (
                f"- Frozen core: `{core_sha}` from `{core_root}` "
                f"(source `{rextio_file}`) / API `{plugin_api}`"
            )
        return (
            f"- Core checkout: `{core_root}` "
            f"(source `{rextio_file}`, package `{rextio_version}`) / API `{plugin_api}`"
        )

    return f"- Installed rextio: `{rextio_version}` at `{rextio_file}` / API `{plugin_api}`"


def _write_markdown(path: Path, result: dict[str, object]) -> None:
    cells: list[dict[str, Any]] = result["cells"]  # type: ignore[assignment]
    native_warmups = [int(cell["warmups"]["native"]["elapsed_ns"]) for cell in cells]
    fallback_warmups = [int(cell["warmups"]["fallback"]["elapsed_ns"]) for cell in cells]
    retained_min_ns = min(
        min(int(sample["native_ns"]), int(sample["fallback_ns"]))
        for cell in cells
        for sample in cell["samples"]
    )
    losses = [
        cell
        for cell in cells
        if cell["valid"] and float(cell["median_speedup_fallback_over_native"]) < 1.0
    ]
    provenance: dict[str, object] = result["provenance"]  # type: ignore[assignment]
    lines = [
        "# Rextio NetworkX product-route benchmark",
        "",
        "Primary rows call the generated Rextio wrapper in two persistent processes; "
        "they are not standalone Rust/PyO3 measurements.",
        "",
        "## Run summary",
        "",
        _format_core_provenance_line(provenance),
        f"- Product commit: `{provenance['plugin_commit']}`",
        f"- One-time build: {float(result['method']['build_ns']) / 1e9:.3f} s",  # type: ignore[index]
        f"- First-call warm-up range: native {min(native_warmups) / 1e6:.3f}–{max(native_warmups) / 1e6:.3f} ms; fallback {min(fallback_warmups) / 1e6:.3f}–{max(fallback_warmups) / 1e6:.3f} ms",
        f"- Retained sample minimum: {retained_min_ns / 1e6:.3f} ms; timer floor: {result['method']['timer_floor_ns']} ns",  # type: ignore[index]
        f"- Route evidence: `check.json` SHA-256 `{result['route_evidence']['check_json_sha256']}`",  # type: ignore[index]
        f"- Observed loss cells: {len(losses)}" + (" (none)" if not losses else ""),
        "",
        "| Algorithm | Family | Requested nodes | Raw/effective nodes | Raw/effective edges | Reach | Native ms | Fallback ms | Speedup | Ratio CI95 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for cell in cells:
        if not cell["valid"]:
            lines.append(
                f"| {cell['algorithm']} | {cell['family']} | {cell['requested_nodes']} | "
                f"{cell['raw_node_occurrences']}/{cell['effective_nodes']} | "
                f"{cell['raw_edges']}/{cell['effective_edges']} | {cell['reachable_nodes']} | INVALID | INVALID | — | — |"
            )
            continue
        native_ms = float(cell["native_median_ns_per_call"]) / 1e6
        fallback_ms = float(cell["fallback_median_ns_per_call"]) / 1e6
        speedup = float(cell["median_speedup_fallback_over_native"])
        ratio_ci = cell["paired_ci"]["ratio_ci95"]
        lines.append(
            f"| {cell['algorithm']} | {cell['family']} | {cell['requested_nodes']} | "
            f"{cell['raw_node_occurrences']}/{cell['effective_nodes']} | "
            f"{cell['raw_edges']}/{cell['effective_edges']} | {cell['reachable_nodes']} | "
            f"{native_ms:.4f} | {fallback_ms:.4f} | {speedup:.2f}x | "
            f"[{ratio_ci[0]:.3f}, {ratio_ci[1]:.3f}] |"
        )
    lines.extend(["", "## Sustained measured break-even", ""])
    for family, size in result["break_even"].items():  # type: ignore[union-attr]
        lines.append(f"- `{family}`: {size}")
    lines.extend(
        [
            "",
            "Sustained break-even is the first measured size whose paired-bootstrap "
            "95% CI for log(native/fallback) is wholly below zero and remains so at "
            "every larger measured size in that family; `none` is not interpolated.",
            "",
            "## Loss cells",
            "",
            *(
                [
                    f"- `{cell['case_id']}`: native/fallback median ratio "
                    f"{1 / float(cell['median_speedup_fallback_over_native']):.3f}"
                    for cell in losses
                ]
                if losses
                else [
                    "- None at the measured sizes; this is a measured result, "
                    "not a claim below the smallest size."
                ]
            ),
            "",
            "## Explicit non-claims",
            "",
            "- Compilation is excluded from steady-state latency and reported separately.",
            "- No standalone PyO3 or Rust diagnostic row is presented as product speedup.",
            "- Results apply only to the exact signed-i64 / finite-f64 adapter contracts.",
            "- A correctness digest mismatch invalidates the cell and suppresses speedup.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parent_main(args: argparse.Namespace) -> int:
    provenance = _baseline()
    sizes = (32, 128) if args.smoke else tuple(args.sizes)
    rounds = 3 if args.smoke else args.rounds
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="rextio-networkx-bench-") as temporary:
        root = Path(temporary)
        (root / "rextio.toml").write_text(
            '[rust]\nbuild_tool = "cargo"\n\n[plugins]\nenabled = ["rextio-networkx"]\n',
            encoding="utf-8",
        )
        package = root / "src" / "nx_bench_app"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        (package / "kernels.py").write_text(KERNELS, encoding="utf-8")

        from rextio.cli.main import main

        build_start = time.perf_counter_ns()
        exit_code = main(["build", str(root), "--fallback=cpython"])
        build_ns = time.perf_counter_ns() - build_start
        if exit_code != 0:
            raise RuntimeError(f"benchmark fixture build failed with exit {exit_code}")
        check_path = root / ".rextio" / "reports" / "check.json"
        check = json.loads(check_path.read_text(encoding="utf-8"))
        functions = {
            function["qualname"]: function
            for module in check["modules"]
            for function in module["functions"]
        }
        expected_routes = [
            "nx_bench_app.kernels.components_product",
            "nx_bench_app.kernels.bfs_product",
            "nx_bench_app.kernels.dijkstra_product",
        ]
        route_evidence = {}
        for qualname in expected_routes:
            function = functions[qualname]
            if (
                function["route"] != "native-plugin:rextio-networkx"
                or function["native_status"] != "accepted"
            ):
                raise RuntimeError(f"benchmark route is not native plugin: {function}")
            route_evidence[qualname] = {
                "route": function["route"],
                "native_status": function["native_status"],
                "rule_ids": [claim["rule_id"] for claim in function["plugin_claims"]],
            }
        check_digest = hashlib.sha256(check_path.read_bytes()).hexdigest()
        shutil.copy2(check_path, output_dir / "check.json")

        build_python = root / ".rextio" / "build" / "python"
        workers = {mode: ModeWorker(mode, build_python) for mode in ("native", "fallback")}
        try:
            cells = [
                _measure_cell(
                    case,
                    workers,
                    rounds=rounds,
                    target_ns=max(20_000_000, int(args.target_ms * 1e6)),
                    seed=args.seed + index,
                )
                for index, case in enumerate(benchmark_cases(sizes))
            ]
        finally:
            for worker in workers.values():
                worker.close()

    result = {
        "schema": "rextio-networkx-product-benchmark-v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "provenance": provenance,
        "route_evidence": {
            "check_json_sha256": check_digest,
            "original_check_json": "check.json",
            "functions": route_evidence,
        },
        "method": {
            "modes": ["native", "fallback"],
            "persistent_processes": 2,
            "schedule": "alternating AB/BA paired rounds",
            "gc": "gc.collect before each sample, GC disabled symmetrically during timing",
            "minimum_sample_ms": 10,
            "calibration_target_ms": max(20.0, args.target_ms),
            "rounds": rounds,
            "seed": args.seed,
            "timer_floor_ns": _timer_floor_ns(),
            "timed_scope": (
                "generated wrapper + raw extraction + deduplicating petgraph/NetworkX "
                "construction + algorithm + exact Python result materialization + destruction"
            ),
            "excluded": "one-time fixture compilation; reported as build_ns",
            "build_ns": build_ns,
        },
        "cells": cells,
        "break_even": _break_even(cells),
        "non_claims": [
            "No standalone Rust/PyO3 diagnostic is labeled as product speedup.",
            "No cell with a correctness digest mismatch carries a speedup.",
            "No result is generalized beyond the exact covered contracts and measured sizes.",
        ],
    }
    raw_path = output_dir / "raw_samples.json"
    raw_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    _write_markdown(output_dir / "report.md", result)
    print(f"wrote {raw_path}")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--mode", choices=("native", "fallback"))
    parser.add_argument("--build-python")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument(
        "--sizes",
        nargs="+",
        type=int,
        default=[4, 8, 16, 32, 128, 512, 2048],
    )
    parser.add_argument("--rounds", type=int, default=9)
    parser.add_argument("--target-ms", type=float, default=20.0)
    parser.add_argument("--seed", type=int, default=20260715)
    parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "benchmarks" / "results"),
    )
    return parser


def main() -> int:
    """Run a worker or the orchestrating benchmark parent."""
    args = _parser().parse_args()
    if args.worker:
        if args.mode is None or args.build_python is None:
            raise SystemExit("worker requires --mode and --build-python")
        return _worker_main(args)
    return _parent_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
