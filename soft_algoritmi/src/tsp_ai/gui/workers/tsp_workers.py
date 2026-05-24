"""TSP-specific worker helpers."""

from __future__ import annotations

from typing import Dict, List, Tuple

import pandas as pd

from tsp_ai.tsp import solve_tsp
from tsp_ai.tsp.experiments import run_tsp_benchmark


def run_tsp_solver_worker(algorithm: str, D: List[List[int]], params: Dict) -> object:
    """Worker function for solving a TSP instance.

    Args:
        algorithm: Algorithm identifier.
        D: Distance matrix.
        params: Algorithm parameters.

    Returns:
        TSPResult.
    """
    return solve_tsp(algorithm, D, **params)


def run_tsp_benchmark_worker(
    suite: str,
    algorithms: List[str],
    seed: int,
    repeats: int,
    sizes: List[int] | None,
    params: Dict[str, Dict] | None,
    progress_cb=None,
    cancel_cb=None,
) -> pd.DataFrame:
    """Worker function for TSP benchmarks."""
    return run_tsp_benchmark(
        suite,
        algorithms,
        seed,
        repeats,
        sizes,
        params,
        progress_cb=progress_cb,
        cancel_cb=cancel_cb,
    )
