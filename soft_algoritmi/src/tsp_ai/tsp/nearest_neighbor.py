"""Nearest neighbor heuristic for TSP."""

from __future__ import annotations

import time
from typing import Dict, List

from tsp_ai.tsp.types import TSPResult
from tsp_ai.tsp.utils import nearest_neighbor_tour, tour_cost, validate_distance_matrix


def solve_nearest_neighbor(
    D: List[List[int]],
    start_city: int = 0,
    multistart: bool = False,
) -> TSPResult:
    """Solve TSP using nearest neighbor heuristic.

    Args:
        D: Distance matrix.
        start_city: Start city index.
        multistart: If True, run from all start cities and take the best.

    Returns:
        TSPResult with the best tour found.
    """
    n = validate_distance_matrix(D)
    t0 = time.perf_counter()

    best_tour: List[int] = []
    best_cost = float("inf")
    starts = range(n) if multistart else [start_city]
    for s in starts:
        tour = nearest_neighbor_tour(D, s)
        cost = tour_cost(D, tour)
        if cost < best_cost:
            best_cost = cost
            best_tour = tour

    elapsed = time.perf_counter() - t0
    meta: Dict[str, int | float] = {"start_city": start_city, "multistart": int(multistart)}
    params = {"start_city": start_city, "multistart": multistart}
    return TSPResult(
        tour=best_tour,
        cost=float(best_cost),
        elapsed_sec=elapsed,
        algorithm="nn",
        params=params,
        meta=meta,
        history=None,
    )
