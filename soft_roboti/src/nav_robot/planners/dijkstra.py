"""Dijkstra pe occupancy grid (faza 2 - stub)."""

from __future__ import annotations

from nav_robot.map.grid_map import Cell, GridMap
from nav_robot.planners.base import PlanResult


class DijkstraPlanner:
    name = "dijkstra"

    def __init__(self, diagonal: bool = False) -> None:
        self.diagonal = diagonal

    def plan(self, grid: GridMap, start: Cell, goal: Cell) -> PlanResult:
        raise NotImplementedError(
            "DijkstraPlanner.plan - TODO faza 2: heap cu cost cumulat, fara heuristica."
        )
