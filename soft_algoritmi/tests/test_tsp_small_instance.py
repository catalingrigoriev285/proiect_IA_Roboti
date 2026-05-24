"""Small instance test for exact backtracking."""

from tsp_ai.tsp.backtracking import solve_backtracking


def test_backtracking_small_instance() -> None:
    D = [
        [0, 10, 15, 20],
        [10, 0, 35, 25],
        [15, 35, 0, 30],
        [20, 25, 30, 0],
    ]
    result = solve_backtracking(D, mode="toate")
    assert result.cost == 80
