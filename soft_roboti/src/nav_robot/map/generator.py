"""Generator de harti aleatoare seed-based pentru testarea planificatorilor."""

from __future__ import annotations

from collections import deque

import numpy as np

from nav_robot.config import (
    DEFAULT_CELL_SIZE,
    DEFAULT_GRID_H,
    DEFAULT_GRID_W,
    DEFAULT_OBSTACLE_RATIO,
    MAX_GENERATION_RETRIES,
)
from nav_robot.map.grid_map import FREE, OBSTACLE, Cell, GridMap


def generate_random_map(
    width: int = DEFAULT_GRID_W,
    height: int = DEFAULT_GRID_H,
    obstacle_ratio: float = DEFAULT_OBSTACLE_RATIO,
    seed: int | None = None,
    start: Cell | None = None,
    goal: Cell | None = None,
    cell_size: float = DEFAULT_CELL_SIZE,
    cluster_size_range: tuple[int, int] = (1, 3),
) -> GridMap:
    """
    Genereaza o harta aleatoare reproductibila pe baza unui seed.

    Algoritm:
        1. Alege obiecte rectangulare (clustere de celule) plasate aleator
           pana cand fractiunea ocupata atinge `obstacle_ratio`.
        2. Pastreaza o bordura sigura de 1 celula libera pe contur.
        3. Forteaza start si goal sa fie libere.
        4. Verifica conectivitatea start <-> goal cu BFS; daca nu sunt
           conectate, regenereaza (pana la MAX_GENERATION_RETRIES).

    Args:
        width: latimea grilei in celule (X).
        height: inaltimea grilei in celule (Y).
        obstacle_ratio: fractiunea aproximativa de celule ocupate (0..1).
        seed: seed pentru numpy RNG; aceeasi valoare produce aceeasi harta.
        start: celula de start; default (1, 1).
        goal: celula tinta; default (width-2, height-2).
        cell_size: metri/celula (pentru conversia in coordonate world).
        cluster_size_range: (min, max) latime/inaltime pentru fiecare obstacol.

    Returns:
        GridMap valid cu start si goal conectate.

    Raises:
        RuntimeError: daca nu se poate genera o harta conectata in numarul
            maxim de incercari.
        ValueError: daca parametrii sunt invalizi.
    """
    if width < 4 or height < 4:
        raise ValueError("width si height trebuie sa fie >= 4")
    if not 0.0 <= obstacle_ratio < 0.9:
        raise ValueError("obstacle_ratio trebuie in [0, 0.9)")

    start = start if start is not None else (1, 1)
    goal = goal if goal is not None else (width - 2, height - 2)

    for attempt in range(MAX_GENERATION_RETRIES):
        attempt_seed = seed if seed is None else seed + attempt * 1000
        cells = _place_obstacles(
            width=width,
            height=height,
            obstacle_ratio=obstacle_ratio,
            cluster_size_range=cluster_size_range,
            rng=np.random.default_rng(attempt_seed),
        )

        # Borduri libere - lasam un cadru exterior de 1 celula (in afara
        # bordurii peretii implicit ar lasa robotul sa se nasca lipit de zid).
        cells[0, :] = FREE
        cells[-1, :] = FREE
        cells[:, 0] = FREE
        cells[:, -1] = FREE

        # Forteaza start / goal libere.
        cells[start[1], start[0]] = FREE
        cells[goal[1], goal[0]] = FREE

        if _connected(cells, start, goal):
            return GridMap(
                width=width,
                height=height,
                cells=cells,
                start=start,
                goal=goal,
                cell_size=cell_size,
                seed=seed,
            )

    raise RuntimeError(
        f"Nu am putut genera o harta cu start-goal conectate dupa "
        f"{MAX_GENERATION_RETRIES} incercari (seed={seed}, ratio={obstacle_ratio})."
    )


def _place_obstacles(
    width: int,
    height: int,
    obstacle_ratio: float,
    cluster_size_range: tuple[int, int],
    rng: np.random.Generator,
) -> np.ndarray:
    """Plaseaza clustere rectangulare pana se atinge fractiunea ceruta."""
    cells = np.zeros((height, width), dtype=np.uint8)
    target = int(obstacle_ratio * width * height)
    occupied = 0
    cmin, cmax = cluster_size_range
    max_iter = target * 10  # garantie de oprire

    for _ in range(max_iter):
        if occupied >= target:
            break
        w = int(rng.integers(cmin, cmax + 1))
        h = int(rng.integers(cmin, cmax + 1))
        x = int(rng.integers(0, max(1, width - w)))
        y = int(rng.integers(0, max(1, height - h)))
        block = cells[y : y + h, x : x + w]
        new = int(np.sum(block == FREE))
        block[:] = OBSTACLE
        occupied += new

    return cells


def _connected(cells: np.ndarray, start: Cell, goal: Cell) -> bool:
    """BFS rapid pe celule libere pentru a verifica conectivitatea start->goal."""
    height, width = cells.shape
    if cells[start[1], start[0]] != FREE or cells[goal[1], goal[0]] != FREE:
        return False

    visited = np.zeros_like(cells, dtype=bool)
    visited[start[1], start[0]] = True
    queue: deque[Cell] = deque([start])

    while queue:
        x, y = queue.popleft()
        if (x, y) == goal:
            return True
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and not visited[ny, nx]:
                if cells[ny, nx] == FREE:
                    visited[ny, nx] = True
                    queue.append((nx, ny))
    return False
