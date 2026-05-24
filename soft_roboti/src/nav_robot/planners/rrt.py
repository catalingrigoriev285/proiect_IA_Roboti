"""RRT / RRT* discretizat pe occupancy grid.

Pentru simplicitate, lucram in spatiul celulelor (intregi) si verificam
coliziunile cu un algoritm Bresenham. Pentru spatii continue reale ar trebui
sa folosim coordonate float si verificare cu sferele de coliziune ale robotului.
"""

from __future__ import annotations

import math
import random
import time

from nav_robot.map.grid_map import Cell, GridMap
from nav_robot.planners._search import step_cost
from nav_robot.planners.base import Path, PlanResult


class RRTPlanner:
    """Rapidly-exploring Random Tree (varianta de baza sau RRT*).

    Algoritm:
        1. Initializeaza arborele cu nodul `start`.
        2. La fiecare iteratie sample-eaza o celula random (cu probabilitate
           `goal_bias` esantioneaza direct `goal`).
        3. Gaseste nodul cel mai apropiat din arbore.
        4. "Steer" - genereaza o noua celula in directia sample-ului, la
           distanta cel mult `step_size` celule.
        5. Daca linia intre cele doua celule e libera, adauga noul nod.
        6. (RRT*) Rewire: pentru nodurile vecine (in raza r), daca trecerea
           prin noul nod scade costul g, modifica parintele.
        7. Daca noul nod e suficient de aproape de goal si linia e libera,
           returneaza traseul.

    Limitari:
        Drumul nu e garantat optim pentru RRT pur; RRT* converge asimptotic
        catre optim cu numar suficient de iteratii.
    """

    name = "rrt"

    def __init__(
        self,
        max_iter: int = 5000,
        step_size: float = 3.0,
        goal_bias: float = 0.1,
        connect_radius: float = 1.5,
        star: bool = False,
        seed: int | None = None,
    ) -> None:
        self.max_iter = max_iter
        self.step_size = step_size
        self.goal_bias = goal_bias
        self.connect_radius = connect_radius
        self.star = star
        self.seed = seed

    def plan(self, grid: GridMap, start: Cell, goal: Cell) -> PlanResult:
        t0 = time.perf_counter()

        if start == goal:
            return PlanResult(path=[start], cost=0.0,
                              elapsed_s=time.perf_counter() - t0)
        if not grid.is_free(start) or not grid.is_free(goal):
            return PlanResult(path=None, elapsed_s=time.perf_counter() - t0)

        rng = random.Random(self.seed)

        # Lista de noduri. Pentru fiecare: parent index (sau -1 pt root) + g_score.
        nodes: list[Cell] = [start]
        parent: list[int] = [-1]
        g_score: list[float] = [0.0]

        # r dinamic pentru RRT* (formula clasica simplificata)
        gamma = 5.0  # constanta empirica
        d = 2.0      # dimensiunea spatiului

        for it in range(self.max_iter):
            # Sample
            if rng.random() < self.goal_bias:
                rand_cell: Cell = goal
            else:
                rand_cell = self._sample_free(grid, rng)

            # Nearest
            i_near = self._nearest_index(nodes, rand_cell)
            near = nodes[i_near]

            # Steer
            new = self._steer(near, rand_cell)
            if new == near or not grid.is_free(new):
                continue
            if not self._line_free(grid, near, new):
                continue

            # Adauga nodul
            new_g = g_score[i_near] + _euclid(near, new)
            i_new = len(nodes)
            nodes.append(new)
            parent.append(i_near)
            g_score.append(new_g)

            # RRT*: rewire prin vecini in raza r
            if self.star:
                n_nodes = len(nodes)
                r = min(self.step_size,
                        gamma * (math.log(n_nodes) / n_nodes) ** (1.0 / d))
                # Cauta parinte mai bun pentru `new`
                for j, nb in enumerate(nodes[:-1]):
                    if _euclid(nb, new) <= r and self._line_free(grid, nb, new):
                        alt = g_score[j] + _euclid(nb, new)
                        if alt < g_score[i_new]:
                            parent[i_new] = j
                            g_score[i_new] = alt
                # Rewire vecini prin `new`
                for j, nb in enumerate(nodes[:-1]):
                    if _euclid(nb, new) <= r and self._line_free(grid, new, nb):
                        alt = g_score[i_new] + _euclid(new, nb)
                        if alt < g_score[j]:
                            parent[j] = i_new
                            g_score[j] = alt

            # Verifica conexiunea la goal
            if _euclid(new, goal) <= self.connect_radius \
                    and self._line_free(grid, new, goal):
                # Conecteaza goal ca ultim nod
                g_goal = g_score[i_new] + _euclid(new, goal)
                nodes.append(goal)
                parent.append(i_new)
                g_score.append(g_goal)
                path = _reconstruct(nodes, parent, len(nodes) - 1)
                cost = _path_cost(path)
                return PlanResult(
                    path=path,
                    expanded_nodes=len(nodes),
                    cost=cost,
                    elapsed_s=time.perf_counter() - t0,
                )

        return PlanResult(
            path=None,
            expanded_nodes=len(nodes),
            elapsed_s=time.perf_counter() - t0,
        )

    # ----- helpers -----
    def _sample_free(self, grid: GridMap, rng: random.Random) -> Cell:
        # Pana cand picam pe o celula libera (rare cazuri de probabilitate scazuta)
        for _ in range(100):
            x = rng.randint(0, grid.width - 1)
            y = rng.randint(0, grid.height - 1)
            if grid.is_free((x, y)):
                return (x, y)
        # fallback - returnam o celula libera oarecare
        return grid.start

    def _nearest_index(self, nodes: list[Cell], target: Cell) -> int:
        best, best_d = 0, float("inf")
        tx, ty = target
        for i, (x, y) in enumerate(nodes):
            d = (x - tx) * (x - tx) + (y - ty) * (y - ty)
            if d < best_d:
                best_d = d
                best = i
        return best

    def _steer(self, from_cell: Cell, to_cell: Cell) -> Cell:
        """Genereaza o celula in directia `to_cell` la distanta <= step_size."""
        dx = to_cell[0] - from_cell[0]
        dy = to_cell[1] - from_cell[1]
        dist = math.hypot(dx, dy)
        if dist <= self.step_size:
            return to_cell
        ratio = self.step_size / dist
        nx = int(round(from_cell[0] + dx * ratio))
        ny = int(round(from_cell[1] + dy * ratio))
        return (nx, ny)

    @staticmethod
    def _line_free(grid: GridMap, a: Cell, b: Cell) -> bool:
        """Bresenham pe celule: True daca toata linia trece doar prin celule libere."""
        for cell in _bresenham(a, b):
            if not grid.is_free(cell):
                return False
        return True


def _euclid(a: Cell, b: Cell) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _bresenham(a: Cell, b: Cell):
    """Generator de celule pe linia (a -> b) - algoritm Bresenham."""
    x0, y0 = a
    x1, y1 = b
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        yield (x0, y0)
        if x0 == x1 and y0 == y1:
            return
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def _reconstruct(nodes: list[Cell], parent: list[int], end_index: int) -> Path:
    path: Path = []
    i = end_index
    while i != -1:
        path.append(nodes[i])
        i = parent[i]
    path.reverse()
    return path


def _path_cost(path: Path) -> float:
    return sum(_euclid(path[i], path[i + 1]) for i in range(len(path) - 1))
