"""A* pe occupancy grid."""

from __future__ import annotations

import time

from nav_robot.map.grid_map import Cell, GridMap
from nav_robot.planners._search import make_heuristic, weighted_search
from nav_robot.planners.base import PlanResult


class AStarPlanner:
    """A* cu heuristica configurabila si 4 / 8-connectivity.

    Pentru 4-conn, heuristica 'manhattan' este admisibila si consistenta.
    Pentru 8-conn, foloseste 'octile' (sau 'euclidean' - admisibila dar mai slaba).
    """

    name = "astar"

    def __init__(self, diagonal: bool = False, heuristic: str = "manhattan") -> None:
        self.diagonal = diagonal
        self.heuristic_name = heuristic
        self._heuristic = make_heuristic(heuristic)

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
