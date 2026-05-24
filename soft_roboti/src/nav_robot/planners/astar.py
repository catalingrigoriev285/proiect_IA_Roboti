"""A* pe occupancy grid (faza 2 - stub).

Heuristici planificate:
    - Manhattan (default, optim pentru 4-connectivity)
    - Octile / Euclidean (pentru 8-connectivity)
"""

from __future__ import annotations

from nav_robot.map.grid_map import Cell, GridMap
from nav_robot.planners.base import PlanResult


class AStarPlanner:
    name = "astar"

    def __init__(self, diagonal: bool = False, heuristic: str = "manhattan") -> None:
        self.diagonal = diagonal
        self.heuristic = heuristic

    def plan(self, grid: GridMap, start: Cell, goal: Cell) -> PlanResult:
        raise NotImplementedError(
            "AStarPlanner.plan - TODO faza 2: implementare A* cu heapq + heuristica Manhattan."
        )
