"""TSP algorithms and experimentation utilities."""

from __future__ import annotations

from typing import Any, Dict, List

from tsp_ai.tsp.backtracking import solve_backtracking
from tsp_ai.tsp.genetic_algorithm import solve_genetic_algorithm
from tsp_ai.tsp.hill_climbing import solve_hill_climbing
from tsp_ai.tsp.nearest_neighbor import solve_nearest_neighbor
from tsp_ai.tsp.simulated_annealing import solve_simulated_annealing
from tsp_ai.tsp.types import TSPResult

__all__ = ["solve_tsp", "TSPResult"]


def solve_tsp(algorithm: str, D: List[List[int]], **params: Any) -> TSPResult:
    """Solve a TSP instance with the selected algorithm.

    Args:
        algorithm: Algorithm identifier (bkt, nn, hc, sa, ga).
        D: Square distance matrix.
        **params: Algorithm-specific parameters.

    Returns:
        TSPResult with solution data.

    Raises:
        ValueError: If the algorithm is not recognized.
    """
    algo = algorithm.lower()
    if algo == "bkt":
        return solve_backtracking(D, **params)
    if algo == "nn":
        return solve_nearest_neighbor(D, **params)
    if algo == "hc":
        return solve_hill_climbing(D, **params)
    if algo == "sa":
        return solve_simulated_annealing(D, **params)
    if algo == "ga":
        return solve_genetic_algorithm(D, **params)
    raise ValueError(f"Unknown algorithm: {algorithm}")
