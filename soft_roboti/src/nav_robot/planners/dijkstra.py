"""Dijkstra pe occupancy grid (= A* cu heuristica zero)."""

from __future__ import annotations

import time

from nav_robot.map.grid_map import Cell, GridMap
from nav_robot.planners._search import make_heuristic, weighted_search
from nav_robot.planners.base import PlanResult


class DijkstraPlanner:
    """Dijkstra clasic: expandeaza nodurile in ordinea costului cumulat g(n).

    Echivalent cu A* unde heuristica h(n) = 0. Garanteaza optimum global pe muchii
    pozitive (1.0 cardinal, sqrt(2) diagonal in cazul nostru).
    """

    name = "dijkstra"

    def __init__(self, diagonal: bool = False) -> None:
        self.diagonal = diagonal
        self._heuristic = make_heuristic("zero")

    def plan(self, grid: GridMap, start: Cell, goal: Cell) -> PlanResult:
        t0 = time.perf_counter()
        path, expanded, cost = weighted_search(
            grid, start, goal, self._heuristic, diagonal=self.diagonal
        )
        return PlanResult(
            path=path,
            expanded_nodes=expanded,
            cost=cost,
            elapsed_s=time.perf_counter() - t0,
        )
