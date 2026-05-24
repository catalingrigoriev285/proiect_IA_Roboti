"""Teste pentru A*, Dijkstra, BFS, RRT."""

import math

import numpy as np
import pytest

from nav_robot.map import GridMap, generate_random_map
from nav_robot.map.grid_map import FREE, OBSTACLE
from nav_robot.planners import (
    AStarPlanner, BFSPlanner, DijkstraPlanner, RRTPlanner,
    PLANNER_NAMES, get_planner,
)


def empty_grid(w: int = 10, h: int = 10, start=(0, 0), goal=(9, 9)) -> GridMap:
    cells = np.zeros((h, w), dtype=np.uint8)
    return GridMap(width=w, height=h, cells=cells, start=start, goal=goal)


def blocked_grid() -> GridMap:
    """Grila 5x5 cu peretele vertical care lasa o singura iesire sus."""
    cells = np.zeros((5, 5), dtype=np.uint8)
    cells[1:5, 2] = OBSTACLE  # zid de la (2,1) pana la (2,4); doar (2,0) liber sus
    return GridMap(width=5, height=5, cells=cells, start=(0, 0), goal=(4, 0))


def disconnected_grid() -> GridMap:
    cells = np.zeros((5, 5), dtype=np.uint8)
    cells[:, 2] = OBSTACLE   # zid complet vertical - imparte grila in 2
    return GridMap(width=5, height=5, cells=cells, start=(0, 0), goal=(4, 4))


# ----------------------------------------------------------------------
# A*
# ----------------------------------------------------------------------
class TestAStar:
    def test_optimum_4conn(self):
        g = empty_grid(10, 10, start=(0, 0), goal=(9, 9))
        res = AStarPlanner(diagonal=False, heuristic="manhattan").plan(g, g.start, g.goal)
        assert res.path is not None
        assert res.path[0] == g.start and res.path[-1] == g.goal
        # Manhattan distance este 18, deci pathul are 19 celule (inclusiv start)
        assert len(res.path) == 19
        assert res.cost == pytest.approx(18.0)

    def test_optimum_8conn(self):
        g = empty_grid(10, 10, start=(0, 0), goal=(9, 9))
        res = AStarPlanner(diagonal=True, heuristic="octile").plan(g, g.start, g.goal)
        # Diagonala in linie dreapta: 9 pasi diagonali
        assert res.path is not None and len(res.path) == 10
        assert res.cost == pytest.approx(9 * math.sqrt(2))

    def test_around_obstacle(self):
        g = blocked_grid()
        res = AStarPlanner(heuristic="manhattan").plan(g, g.start, g.goal)
        assert res.path is not None
        # Trebuie sa ocoleasca prin (2, 0) - unica iesire
        assert (2, 0) in res.path

    def test_no_path_returns_none(self):
        g = disconnected_grid()
        res = AStarPlanner().plan(g, g.start, g.goal)
        assert res.path is None

    def test_start_equals_goal(self):
        g = empty_grid()
        res = AStarPlanner().plan(g, (3, 3), (3, 3))
        assert res.path == [(3, 3)]
        assert res.cost == 0.0

    def test_invalid_heuristic_raises(self):
        with pytest.raises(ValueError):
            AStarPlanner(heuristic="bogus")


# ----------------------------------------------------------------------
# Dijkstra
# ----------------------------------------------------------------------
class TestDijkstra:
    def test_matches_astar_cost(self):
        # Pe orice harta, costul optim Dijkstra trebuie sa fie cel al A*
        for seed in (1, 7, 42):
            g = generate_random_map(width=12, height=12, obstacle_ratio=0.2, seed=seed)
            res_a = AStarPlanner().plan(g, g.start, g.goal)
            res_d = DijkstraPlanner().plan(g, g.start, g.goal)
            assert res_a.path is not None and res_d.path is not None
            assert res_d.cost == pytest.approx(res_a.cost)

    def test_astar_never_expands_more_than_dijkstra(self):
        # Cu heuristica admisibila si consistenta, A* nu poate expanda mai
        # multe noduri decat Dijkstra pentru aceeasi problema.
        for seed in (1, 2, 3, 7, 42):
            g = generate_random_map(width=20, height=20, obstacle_ratio=0.25, seed=seed)
            res_a = AStarPlanner(heuristic="manhattan").plan(g, g.start, g.goal)
            res_d = DijkstraPlanner().plan(g, g.start, g.goal)
            assert res_a.expanded_nodes <= res_d.expanded_nodes, \
                f"seed={seed}: A* {res_a.expanded_nodes} > Dijkstra {res_d.expanded_nodes}"


# ----------------------------------------------------------------------
# BFS
# ----------------------------------------------------------------------
class TestBFS:
    def test_returns_shortest_in_steps_4conn(self):
        g = empty_grid(8, 8, start=(0, 0), goal=(7, 0))
        res = BFSPlanner(diagonal=False).plan(g, g.start, g.goal)
        assert res.path is not None and len(res.path) == 8

    def test_disconnected_returns_none(self):
        g = disconnected_grid()
        res = BFSPlanner().plan(g, g.start, g.goal)
        assert res.path is None


# ----------------------------------------------------------------------
# RRT
# ----------------------------------------------------------------------
class TestRRT:
    def test_finds_path_on_open_map(self):
        g = empty_grid(20, 20, start=(0, 0), goal=(19, 19))
        res = RRTPlanner(max_iter=2000, step_size=3.0, seed=42).plan(g, g.start, g.goal)
        assert res.path is not None
        assert res.path[0] == g.start and res.path[-1] == g.goal

    def test_reproducible_with_seed(self):
        g = empty_grid(20, 20, start=(0, 0), goal=(19, 19))
        a = RRTPlanner(max_iter=1000, seed=7).plan(g, g.start, g.goal)
        b = RRTPlanner(max_iter=1000, seed=7).plan(g, g.start, g.goal)
        assert a.path == b.path

    def test_star_variant_runs(self):
        g = generate_random_map(width=15, height=15, obstacle_ratio=0.2, seed=3)
        res = RRTPlanner(max_iter=3000, step_size=3.0, star=True, seed=1).plan(
            g, g.start, g.goal,
        )
        # RRT* poate sau nu sa gaseasca - dar nu trebuie sa arunce.
        assert res.elapsed_s >= 0


# ----------------------------------------------------------------------
# Factory
# ----------------------------------------------------------------------
class TestFactory:
    @pytest.mark.parametrize("name", PLANNER_NAMES)
    def test_get_planner_works(self, name):
        p = get_planner(name)
        assert hasattr(p, "plan")
        assert p.name == name

    def test_unknown_name(self):
        with pytest.raises(ValueError):
            get_planner("bogus")


# ----------------------------------------------------------------------
# Compara toti pe aceeasi harta (smoke test integrare)
# ----------------------------------------------------------------------
def test_all_planners_agree_on_solvability():
    g = generate_random_map(width=20, height=20, obstacle_ratio=0.25, seed=42)
    results = {n: get_planner(n, seed=42 if n == "rrt" else None).plan(g, g.start, g.goal)
               if n == "rrt" else get_planner(n).plan(g, g.start, g.goal)
               for n in PLANNER_NAMES}
    # Toate trebuie sa gaseasca un drum (generator garanteaza conectivitatea)
    for n, r in results.items():
        assert r.path is not None, f"{n} nu a gasit drum"
        assert r.path[0] == g.start and r.path[-1] == g.goal
