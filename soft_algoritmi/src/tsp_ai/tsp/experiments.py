"""Benchmark suites and experiment runners for TSP."""

from __future__ import annotations

from typing import Callable, Dict, Iterable, List, Sequence

import pandas as pd

from tsp_ai.tsp import solve_tsp
from tsp_ai.tsp.io_utils import random_distance_matrix


SUITE_SMALL = [5, 7, 8, 10, 12]
SUITE_MEDIUM = [15, 20, 30]
SUITE_LARGE = [50]


def run_tsp_benchmark(
    suite: str,
    algorithms: Sequence[str],
    seed: int = 42,
    repeats: int = 1,
    custom_sizes: Iterable[int] | None = None,
    params: Dict[str, Dict] | None = None,
    progress_cb: Callable[[int, int], None] | None = None,
    cancel_cb: Callable[[], bool] | None = None,
) -> pd.DataFrame:
    """Run benchmark suites for TSP algorithms.

    Args:
        suite: Suite name ('small', 'medium', 'large', 'custom').
        algorithms: Algorithms to include.
        seed: Random seed.
        repeats: Number of runs per size.
        custom_sizes: Custom list of sizes if suite is 'custom'.
        params: Optional per-algorithm parameters.

    Returns:
        DataFrame with benchmark results.
    """
    params = params or {}
    if suite == "small":
        sizes = SUITE_SMALL
    elif suite == "medium":
        sizes = SUITE_MEDIUM
    elif suite == "large":
        sizes = SUITE_LARGE
    elif suite == "custom" and custom_sizes is not None:
        sizes = list(custom_sizes)
    else:
        raise ValueError("Invalid benchmark suite.")

    rows = []
    total = len(sizes) * repeats * len(algorithms)
    step = 0
    for n in sizes:
        for rep in range(repeats):
            matrix_seed = seed + n * 100 + rep
            D = random_distance_matrix(n, low=1, high=100, seed=matrix_seed)
            optimal_cost = None
            if suite == "small":
                result_opt = solve_tsp("bkt", D, mode="toate")
                optimal_cost = result_opt.cost
            for algo in algorithms:
                if cancel_cb and cancel_cb():
                    raise RuntimeError("Cancelled")
                run_params = params.get(algo, {})
                result = solve_tsp(algo, D, **run_params)
                gap_pct = None
                if optimal_cost is not None and algo != "bkt":
                    gap_pct = 100.0 * (result.cost - optimal_cost) / optimal_cost
                rows.append(
                    {
                        "N": n,
                        "repeat": rep,
                        "algorithm": result.algorithm,
                        "cost": result.cost,
                        "elapsed_sec": result.elapsed_sec,
                        "gap_pct": gap_pct,
                    }
                )
                step += 1
                if progress_cb:
                    progress_cb(step, total)
    return pd.DataFrame(rows)
