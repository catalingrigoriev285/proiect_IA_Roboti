"""Teste pentru PolicyGA (PyGAD)."""

import numpy as np
import pytest

pygad = pytest.importorskip("pygad")

from nav_robot.map.grid_map import GridMap
from nav_robot.rl.env import GridWorldEnv
from nav_robot.rl.genetic import PolicyGA, chromosome_to_policy
from nav_robot.rl.trainer import rollout


def empty_grid(w: int = 5, h: int = 5, start=(0, 0), goal=(4, 4)) -> GridMap:
    return GridMap(width=w, height=h, cells=np.zeros((h, w), dtype=np.uint8),
                   start=start, goal=goal)


class TestPolicyGA:
    def test_chromosome_decoding(self):
        chromo = np.arange(20) % 4
        p = chromosome_to_policy(chromo, width=5, height=4)
        assert p.action_grid.shape == (4, 5)
        assert p((0, 0)) == 0

    def test_runs_and_improves(self):
        # Pe 5x5 deschis, GA cu pop=40, gen=40 trebuie sa produca fitness > random
        g = empty_grid()
        env = GridWorldEnv(g, max_steps=80)
        ga = PolicyGA(env, pop_size=40, n_generations=40,
                      mutation_percent_genes=8.0, seed=42)
        stats = ga.run()
        assert stats.generations == 40
        assert ga.best_chromo is not None
        # Fitness final > random baseline
        random_fitness = -80.0   # 80 pasi, fiecare -1, fara goal
        assert max(stats.best_fitness) > random_fitness

    def test_best_policy_reaches_goal(self):
        g = empty_grid(4, 4, start=(0, 0), goal=(3, 3))
        env = GridWorldEnv(g, max_steps=60)
        ga = PolicyGA(env, pop_size=80, n_generations=120,
                      mutation_percent_genes=10.0, seed=7)
        ga.run()
        pol = ga.policy()
        # Incercam pe mai multe rollouts (politica e deterministica deci toate la fel)
        # dar evaluam ca cel putin reward > random baseline
        res = rollout(GridWorldEnv(g, max_steps=60), pol)
        assert res.reward > -60, \
            f"GA n-a invatat nimic; reward={res.reward}, steps={res.steps}"
