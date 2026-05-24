"""Nucleu comun pentru cautari informate / neinformate pe grid.

Folosit de AStarPlanner si DijkstraPlanner pentru a evita duplicare de cod.
BFS este implementat separat pentru ca foloseste un FIFO simplu, nu heap.
"""

from __future__ import annotations

import heapq
import math
from typing import Callable

from nav_robot.map.grid_map import Cell, GridMap
from nav_robot.planners.base import Path

SQRT2 = math.sqrt(2)


def step_cost(a: Cell, b: Cell) -> float:
    """Costul muchiei intre doua celule vecine: 1.0 cardinal, sqrt(2) diagonal."""
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])
    return SQRT2 if (dx + dy) == 2 else 1.0


def make_heuristic(name: str) -> Callable[[Cell, Cell], float]:
    """Returneaza o functie h(a, b) -> distanta estimata.

    Optiuni:
        - 'manhattan' : |dx| + |dy| (consistenta pentru 4-connectivity)
        - 'euclidean' : sqrt(dx^2 + dy^2)
        - 'octile'    : max(dx,dy) + (sqrt(2)-1)*min(dx,dy) (admisibila pentru 8-conn)
        - 'zero'      : 0 (transforma A* in Dijkstra)
    """
    if name == "manhattan":
        return lambda a, b: abs(a[0] - b[0]) + abs(a[1] - b[1])
    if name == "euclidean":
        return lambda a, b: math.hypot(a[0] - b[0], a[1] - b[1])
    if name == "octile":
        def _h(a, b):
            dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
            return max(dx, dy) + (SQRT2 - 1) * min(dx, dy)
        return _h
    if name == "zero":
        return lambda a, b: 0.0
    raise ValueError(f"Heuristic necunoscuta: {name!r}")


def weighted_search(
    grid: GridMap,
    start: Cell,
    goal: Cell,
    heuristic: Callable[[Cell, Cell], float],
    diagonal: bool = False,
) -> tuple[Path | None, int, float]:
    """A* generic cu heuristica configurabila (h=0 -> Dijkstra).

    Returns:
        (path, expanded_nodes, total_cost).
        path este None daca tinta nu este accesibila.
    """
    if start == goal:
        return [start], 0, 0.0
    if not grid.is_free(start) or not grid.is_free(goal):
        return None, 0, 0.0

    # Heap: (f, g, counter, cell). counter pentru tie-break stabil.
    open_heap: list[tuple[float, float, int, Cell]] = []
    counter = 0
    heapq.heappush(open_heap, (heuristic(start, goal), 0.0, counter, start))

    came_from: dict[Cell, Cell] = {}
    g_score: dict[Cell, float] = {start: 0.0}
    closed: set[Cell] = set()
    expanded = 0

    while open_heap:
        _f, g, _c, cur = heapq.heappop(open_heap)
        if cur in closed:
            continue
        closed.add(cur)
        expanded += 1

        if cur == goal:
            return _reconstruct(came_from, cur), expanded, g

        for nb in grid.neighbors(cur, diagonal=diagonal):
            if nb in closed:
                continue
            tentative_g = g + step_cost(cur, nb)
            if tentative_g < g_score.get(nb, float("inf")):
                g_score[nb] = tentative_g
                came_from[nb] = cur
                counter += 1
                heapq.heappush(
                    open_heap,
                    (tentative_g + heuristic(nb, goal), tentative_g, counter, nb),
                )

    return None, expanded, 0.0


def _reconstruct(came_from: dict[Cell, Cell], cur: Cell) -> Path:
    path: Path = [cur]
    while cur in came_from:
        cur = came_from[cur]
        path.append(cur)
    path.reverse()
    return path
