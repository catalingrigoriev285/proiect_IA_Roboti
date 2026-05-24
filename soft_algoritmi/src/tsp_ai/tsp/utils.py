"""Shared utility functions for TSP algorithms."""

from __future__ import annotations

from typing import Iterable, List, Tuple

import numpy as np


def seed_rng(seed: int | None) -> np.random.Generator:
    """Create a numpy random generator with a fixed seed.

    Args:
        seed: Random seed or None.

    Returns:
        Numpy random number generator.
    """
    return np.random.default_rng(seed)


def validate_distance_matrix(D: List[List[float]]) -> int:
    """Validate a square distance matrix.

    Args:
        D: Distance matrix.

    Returns:
        Number of nodes.

    Raises:
        ValueError: If the matrix is invalid.
    """
    if not D or not isinstance(D, list):
        raise ValueError("Distance matrix must be a non-empty list.")
    n = len(D)
    for row in D:
        if len(row) != n:
            raise ValueError("Distance matrix must be square.")
    return n


def tour_cost(D: List[List[float]], tour: List[int]) -> float:
    """Compute total tour cost including return to start.

    Args:
        D: Distance matrix.
        tour: Ordered list of cities.

    Returns:
        Total tour cost.
    """
    cost = 0.0
    for i in range(len(tour) - 1):
        cost += D[tour[i]][tour[i + 1]]
    cost += D[tour[-1]][tour[0]]
    return float(cost)


def random_tour(n: int, rng: np.random.Generator) -> List[int]:
    """Generate a random permutation tour.

    Args:
        n: Number of nodes.
        rng: Random generator.

    Returns:
        Random tour permutation.
    """
    tour = list(range(n))
    rng.shuffle(tour)
    return tour


def swap_two(tour: List[int], i: int, j: int) -> List[int]:
    """Return a tour with two positions swapped.

    Args:
        tour: Original tour.
        i: First index.
        j: Second index.

    Returns:
        New tour with swapped positions.
    """
    new_tour = tour.copy()
    new_tour[i], new_tour[j] = new_tour[j], new_tour[i]
    return new_tour


def two_opt_swap(tour: List[int], i: int, k: int) -> List[int]:
    """Perform a 2-opt swap on the tour.

    Args:
        tour: Original tour.
        i: Start index of the segment.
        k: End index of the segment.

    Returns:
        New tour after 2-opt swap.
    """
    return tour[:i] + list(reversed(tour[i:k + 1])) + tour[k + 1 :]


def or_opt_move(tour: List[int], i: int, j: int, k: int) -> List[int]:
    """Move a segment [i, j] to follow position k.

    Args:
        tour: Original tour.
        i: Segment start index.
        j: Segment end index (inclusive).
        k: Insertion index after removal.

    Returns:
        New tour after or-opt move.
    """
    if i > j:
        i, j = j, i
    segment = tour[i : j + 1]
    remainder = tour[:i] + tour[j + 1 :]
    if k >= len(remainder):
        return remainder + segment
    return remainder[: k + 1] + segment + remainder[k + 1 :]


def nearest_neighbor_tour(D: List[List[float]], start: int) -> List[int]:
    """Construct a nearest neighbor tour starting from a city.

    Args:
        D: Distance matrix.
        start: Start city index.

    Returns:
        Greedy nearest neighbor tour.
    """
    n = len(D)
    unvisited = set(range(n))
    tour = [start]
    unvisited.remove(start)
    while unvisited:
        last = tour[-1]
        next_city = min(unvisited, key=lambda c: D[last][c])
        tour.append(next_city)
        unvisited.remove(next_city)
    return tour


def format_tour_route(
    tour: List[int],
    return_to_start: bool = True,
    separator: str = " -> ",
) -> str:
    """Format a tour as a city-to-city route string.

    Args:
        tour: Ordered list of cities.
        return_to_start: Whether to append the start city to close the tour.
        separator: Separator between cities.

    Returns:
        Route string (e.g., "0 -> 2 -> 3 -> 0").
    """
    if not tour:
        return ""
    route = tour[:]
    if return_to_start and tour[0] != tour[-1]:
        route = tour + [tour[0]]
    return separator.join(str(city) for city in route)
