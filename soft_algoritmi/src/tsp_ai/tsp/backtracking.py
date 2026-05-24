"""Exact backtracking TSP solver with branch-and-bound."""

from __future__ import annotations

import time
from typing import Dict, List, Tuple

from tsp_ai.tsp.types import TSPResult
from tsp_ai.tsp.utils import tour_cost, validate_distance_matrix


def solve_backtracking(
    D: List[List[int]],
    mode: str = "toate",
    time_limit: float | None = None,
    y_solutions: int | None = None,
) -> TSPResult:
    """Solve TSP via exact backtracking with branch-and-bound.

    Args:
        D: Distance matrix.
        mode: Stop mode ('prima', 'toate', 'timp', 'y_solutii').
        time_limit: Time limit in seconds for 'timp' mode.
        y_solutions: Maximum number of solutions for 'y_solutii' mode.

    Returns:
        TSPResult with the best tour found.
    """
    n = validate_distance_matrix(D)
    start = 0
    best_cost = float("inf")
    best_tour: List[int] = []
    solutions_found = 0
    stop_reason = "completed"
    t0 = time.perf_counter()

    min_edge = [min(row[i] for i in range(n) if i != idx) for idx, row in enumerate(D)]

    def bound(cost_so_far: float, remaining: List[int]) -> float:
        return cost_so_far + sum(min_edge[i] for i in remaining)

    def should_stop() -> bool:
        nonlocal stop_reason
        if mode == "timp" and time_limit is not None:
            if time.perf_counter() - t0 >= time_limit:
                stop_reason = "time_limit"
                return True
        if mode == "y_solutii" and y_solutions is not None:
            if solutions_found >= y_solutions:
                stop_reason = "solution_limit"
                return True
        return False

    def dfs(path: List[int], remaining: List[int], cost_so_far: float) -> None:
        nonlocal best_cost, best_tour, solutions_found
        if should_stop():
            return
        if not remaining:
            total_cost = cost_so_far + D[path[-1]][start]
            solutions_found += 1
            if total_cost < best_cost:
                best_cost = total_cost
                best_tour = path.copy()
            if mode == "prima":
                return
            return
        if bound(cost_so_far, remaining) >= best_cost:
            return
        last = path[-1]
        for idx, city in enumerate(remaining):
            next_cost = cost_so_far + D[last][city]
            if next_cost >= best_cost:
                continue
            dfs(path + [city], remaining[:idx] + remaining[idx + 1 :], next_cost)
            if mode == "prima" and best_tour:
                return
            if should_stop():
                return

    remaining = [i for i in range(n) if i != start]
    dfs([start], remaining, 0.0)
    elapsed = time.perf_counter() - t0
    if not best_tour:
        best_tour = [start] + remaining
        best_cost = tour_cost(D, best_tour)

    meta: Dict[str, float | int | str] = {
        "solutions_found": solutions_found,
        "stop_reason": stop_reason,
        "start_city": start,
    }
    params = {
        "mode": mode,
        "time_limit": time_limit,
        "y_solutions": y_solutions,
    }
    return TSPResult(
        tour=best_tour,
        cost=float(best_cost),
        elapsed_sec=elapsed,
        algorithm="bkt",
        params=params,
        meta=meta,
        history=None,
    )
