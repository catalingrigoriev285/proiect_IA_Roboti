"""Hill climbing metaheuristic for TSP."""

from __future__ import annotations

import time
from typing import Dict, List

import numpy as np

from tsp_ai.tsp.types import TSPResult
from tsp_ai.tsp.utils import (
    nearest_neighbor_tour,
    random_tour,
    seed_rng,
    swap_two,
    tour_cost,
    two_opt_swap,
    validate_distance_matrix,
)


def _best_neighbor(
    D: List[List[int]],
    tour: List[int],
    neighbor: str,
) -> List[int]:
    n = len(tour)
    best = tour
    best_cost = tour_cost(D, tour)
    for i in range(1, n - 1):
        for j in range(i + 1, n):
            if neighbor == "swap":
                candidate = swap_two(tour, i, j)
            else:
                candidate = two_opt_swap(tour, i, j)
            candidate_cost = tour_cost(D, candidate)
            if candidate_cost < best_cost:
                best = candidate
                best_cost = candidate_cost
    return best


def solve_hill_climbing(
    D: List[List[int]],
    restarts: int = 10,
    iterations: int = 200,
    neighbor: str = "2-opt",
    seed: int | None = 42,
    init_mode: str = "random",
) -> TSPResult:
    """Solve TSP using hill climbing with random restarts.

    Args:
        D: Distance matrix.
        restarts: Number of random restarts.
        iterations: Max iterations per restart.
        neighbor: Neighbor operator ('2-opt', 'swap', 'mixed').
        seed: Random seed.
        init_mode: Initialization mode ('random' or 'nn').

    Returns:
        TSPResult with the best tour found.
    """
    validate_distance_matrix(D)
    rng = seed_rng(seed)
    t0 = time.perf_counter()

    best_overall: List[int] = []
    best_cost = float("inf")
    history_cost: List[float] = []

    for _ in range(restarts):
        if init_mode == "nn":
            start_city = int(rng.integers(0, len(D)))
            current = nearest_neighbor_tour(D, start_city)
        else:
            current = random_tour(len(D), rng)

        for _ in range(iterations):
            if neighbor == "mixed":
                op = "swap" if rng.random() < 0.5 else "2-opt"
            else:
                op = "swap" if neighbor == "swap" else "2-opt"
            candidate = _best_neighbor(D, current, op)
            if tour_cost(D, candidate) < tour_cost(D, current):
                current = candidate
            history_cost.append(tour_cost(D, current))

        current_cost = tour_cost(D, current)
        if current_cost < best_cost:
            best_cost = current_cost
            best_overall = current

    elapsed = time.perf_counter() - t0
    params = {
        "restarts": restarts,
        "iterations": iterations,
        "neighbor": neighbor,
        "seed": seed,
        "init_mode": init_mode,
    }
    meta: Dict[str, int | float] = {"restarts": restarts, "iterations": iterations}
    history = {"cost_best": history_cost}
    return TSPResult(
        tour=best_overall,
        cost=float(best_cost),
        elapsed_sec=elapsed,
        algorithm="hc",
        params=params,
        meta=meta,
        history=history,
    )
