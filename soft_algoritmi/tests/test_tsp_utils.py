"""Unit tests for TSP utilities."""

from tsp_ai.tsp.utils import random_tour, tour_cost, two_opt_swap


def test_tour_cost_basic() -> None:
    D = [
        [0, 1, 2],
        [1, 0, 3],
        [2, 3, 0],
    ]
    tour = [0, 1, 2]
    assert tour_cost(D, tour) == 1 + 3 + 2


def test_two_opt_swap() -> None:
    tour = [0, 1, 2, 3, 4]
    swapped = two_opt_swap(tour, 1, 3)
    assert swapped == [0, 3, 2, 1, 4]


def test_random_tour_length() -> None:
    rng = __import__("numpy").random.default_rng(42)
    tour = random_tour(6, rng)
    assert sorted(tour) == list(range(6))
