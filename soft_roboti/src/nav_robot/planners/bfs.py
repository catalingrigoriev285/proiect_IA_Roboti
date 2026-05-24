"""BFS pe occupancy grid - drum cu cele mai putine celule traversate."""

from __future__ import annotations

import time
from collections import deque

from nav_robot.map.grid_map import Cell, GridMap
from nav_robot.planners._search import step_cost
from nav_robot.planners.base import Path, PlanResult


class BFSPlanner:
    """Cautare in latime (FIFO).

    Returneaza un drum minim in *numar de pasi* (nu in distanta euclidiana cand
    e activata diagonala). Util ca baseline si pentru harti unde toate muchiile
    au cost egal.
    """

    name = "bfs"

    def __init__(self, diagonal: bool = False) -> None:
        self.diagonal = diagonal

    def plan(self, grid: GridMap, start: Cell, goal: Cell) -> PlanResult:
        t0 = time.perf_counter()

        if start == goal:
            return PlanResult(path=[start], cost=0.0,
                              elapsed_s=time.perf_counter() - t0)
        if not grid.is_free(start) or not grid.is_free(goal):
            return PlanResult(path=None, elapsed_s=time.perf_counter() - t0)

        queue: deque[Cell] = deque([start])
        came_from: dict[Cell, Cell] = {}
        visited: set[Cell] = {start}
        expanded = 0

        while queue:
            cur = queue.popleft()
            expanded += 1
            if cur == goal:
                path = _reconstruct(came_from, cur)
                cost = _path_cost(path)
                return PlanResult(
                    path=path,
                    expanded_nodes=expanded,
                    cost=cost,
                    elapsed_s=time.perf_counter() - t0,
                )
            for nb in grid.neighbors(cur, diagonal=self.diagonal):
                if nb not in visited:
                    visited.add(nb)
                    came_from[nb] = cur
                    queue.append(nb)

        return PlanResult(
            path=None,
            expanded_nodes=expanded,
            elapsed_s=time.perf_counter() - t0,
        )


def _reconstruct(came_from: dict[Cell, Cell], cur: Cell) -> Path:
    path: Path = [cur]
    while cur in came_from:
        cur = came_from[cur]
        path.append(cur)
    path.reverse()
    return path


def _path_cost(path: Path) -> float:
    return sum(step_cost(path[i], path[i + 1]) for i in range(len(path) - 1))
