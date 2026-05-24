"""RRT / RRT* in spatiu continuu (faza 5 - stub).

Pentru spatiu continuu (coordonate world m), nu pe grila.
Coliziunile sunt verificate prin discretizare pe GridMap.
"""

from __future__ import annotations

from nav_robot.map.grid_map import Cell, GridMap
from nav_robot.planners.base import PlanResult


class RRTPlanner:
    name = "rrt"

    def __init__(self, max_iter: int = 5000, step_size: float = 0.5,
                 goal_bias: float = 0.1, star: bool = False) -> None:
        self.max_iter = max_iter
        self.step_size = step_size
        self.goal_bias = goal_bias
        self.star = star

    def plan(self, grid: GridMap, start: Cell, goal: Cell) -> PlanResult:
        raise NotImplementedError(
            "RRTPlanner.plan - TODO faza 5: sample random + nearest neighbor + steer; "
            "varianta star face rewire local."
        )
