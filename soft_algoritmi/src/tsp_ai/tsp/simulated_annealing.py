"""Simulated annealing implementation for TSP."""

from __future__ import annotations

import math
import time
from typing import Dict, List

import numpy as np

from tsp_ai.tsp.types import TSPResult
from tsp_ai.tsp.utils import (
    nearest_neighbor_tour,
    or_opt_move,
    random_tour,
    seed_rng,
    swap_two,
    tour_cost,
    two_opt_swap,
    validate_distance_matrix,
)


def _schedule(temp: float, schedule: str, step: int, alpha: float) -> float:
    if schedule == "linear":
        return max(temp - alpha, 1e-9)
    if schedule == "logarithmic":
        return temp / (1.0 + alpha * math.log(2 + step))
    return temp * alpha


def _neighbor(
    tour: List[int],
    rng: np.random.Generator,
    probs: Dict[str, float],
) -> List[int]:
    keys = ["swap", "2-opt", "or-opt"]
    p = np.array([probs.get(k, 0.0) for k in keys], dtype=float)
    if p.sum() == 0:
        p = np.array([0.34, 0.33, 0.33])
    p = p / p.sum()
    choice = rng.choice(keys, p=p)
    n = len(tour)
    i, j = sorted(rng.choice(n, size=2, replace=False))
    if choice == "swap":
        return swap_two(tour, i, j)
    if choice == "2-opt":
        return two_opt_swap(tour, i, j)
    k = int(rng.integers(0, n - 1))
    return or_opt_move(tour, i, j, k)


def solve_simulated_annealing(
    D: List[List[int]],
    init_mode: str = "random",
    t_max: float = 1000.0,
    t_min: float = 1.0,
    alpha: float = 0.995,
    iterations: int = 2000,
    schedule: str = "geometric",
    neighbor_probs: Dict[str, float] | None = None,
    seed: int | None = 42,
) -> TSPResult:
    """Solve TSP using simulated annealing.

    Args:
        D: Distance matrix.
        init_mode: Initialization mode ('random', 'nn', 'nn-multistart-best').
        t_max: Initial temperature.
        t_min: Minimum temperature.
        alpha: Cooling factor for the schedule.
        iterations: Number of iterations.
        schedule: Temperature schedule ('geometric', 'linear', 'logarithmic').
        neighbor_probs: Probabilities for neighbor ops (swap, 2-opt, or-opt).
        seed: Random seed.

    Returns:
        TSPResult with the best tour found.
    """
    validate_distance_matrix(D)
    rng = seed_rng(seed)
    t0 = time.perf_counter()

    if init_mode == "nn":
        start_city = int(rng.integers(0, len(D)))
        current = nearest_neighbor_tour(D, start_city)
    elif init_mode == "nn-multistart-best":
        best = None
        best_cost = float("inf")
        for s in range(len(D)):
            tour = nearest_neighbor_tour(D, s)
            cost = tour_cost(D, tour)
            if cost < best_cost:
                best_cost = cost
                best = tour
        current = best if best is not None else random_tour(len(D), rng)
    else:
        current = random_tour(len(D), rng)

    current_cost = tour_cost(D, current)
    best = current
    best_cost = current_cost

    temperature = t_max
    history_current: List[float] = []
    history_best: List[float] = []
    history_temp: List[float] = []
    history_accept: List[float] = []

    accepted = 0
    for step in range(iterations):
        neighbor = _neighbor(current, rng, neighbor_probs or {})
        neighbor_cost = tour_cost(D, neighbor)
        delta = neighbor_cost - current_cost
        accept = delta < 0 or rng.random() < math.exp(-delta / max(temperature, 1e-9))
        if accept:
            current = neighbor
            current_cost = neighbor_cost
            accepted += 1
            if current_cost < best_cost:
                best_cost = current_cost
                best = current
        history_current.append(current_cost)
        history_best.append(best_cost)
        history_temp.append(temperature)
        history_accept.append(accepted / (step + 1))

        temperature = _schedule(temperature, schedule, step, alpha)
        if temperature < t_min:
            break

    elapsed = time.perf_counter() - t0
    params = {
        "init_mode": init_mode,
        "t_max": t_max,
        "t_min": t_min,
        "alpha": alpha,
        "iterations": iterations,
        "schedule": schedule,
        "neighbor_probs": neighbor_probs or {},
        "seed": seed,
    }
    meta: Dict[str, int | float] = {"iterations": len(history_best)}
    history = {
        "cost_current": history_current,
        "cost_best": history_best,
        "temperature": history_temp,
        "acceptance_rate": history_accept,
    }
    return TSPResult(
        tour=best,
        cost=float(best_cost),
        elapsed_sec=elapsed,
        algorithm="sa",
        params=params,
        meta=meta,
        history=history,
    )
