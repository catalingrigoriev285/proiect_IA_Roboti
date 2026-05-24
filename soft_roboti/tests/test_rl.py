"""Teste pentru GridWorldEnv, Q-Learning, SARSA si Trainer."""

import numpy as np
import pytest

from nav_robot.map import generate_random_map
from nav_robot.map.grid_map import FREE, GridMap, OBSTACLE
from nav_robot.rl.env import ACTIONS_4, GridWorldEnv
from nav_robot.rl.policy import Policy
from nav_robot.rl.qlearning import QLearningAgent
from nav_robot.rl.sarsa import SARSAAgent
from nav_robot.rl.trainer import evaluate_policy, rollout, train_agent


def empty_grid(w: int = 5, h: int = 5, start=(0, 0), goal=(4, 4)) -> GridMap:
    return GridMap(width=w, height=h, cells=np.zeros((h, w), dtype=np.uint8),
                   start=start, goal=goal)


# ----------------------------------------------------------------------
# Env
# ----------------------------------------------------------------------
class TestEnv:
    def test_reset_state_is_start(self):
        env = GridWorldEnv(empty_grid())
        s = env.reset()
        assert s == env.grid.start

    def test_step_north_increases_y(self):
        env = GridWorldEnv(empty_grid(), max_steps=10)
        env.reset()
        # Action 0 = N = (0, +1)
        r = env.step(0)
        assert r.state == (0, 1)
        assert r.reward == env.step_cost
        assert not r.done

    def test_collision_penalty_at_boundary(self):
        env = GridWorldEnv(empty_grid(start=(0, 0)))
        env.reset()
        # Action 3 = V (vest) - iesim din harta -> coliziune
        r = env.step(3)
        assert r.state == (0, 0)  # robot ramane pe loc
        assert r.reward == env.step_cost + env.collision_penalty
        assert r.info["collided"] is True

    def test_goal_terminates_episode(self):
        env = GridWorldEnv(empty_grid(start=(3, 4), goal=(4, 4)))
        env.reset()
        r = env.step(1)  # E = (+1, 0)
        assert r.state == (4, 4)
        assert r.done
        assert r.reward > 0

    def test_max_steps_terminates(self):
        env = GridWorldEnv(empty_grid(), max_steps=3)
        env.reset()
        for i in range(3):
            r = env.step(0)
            if i < 2:
                assert not r.done
            else:
                assert r.done

    def test_obstacle_collision(self):
        cells = np.zeros((3, 3), dtype=np.uint8)
        cells[1, 1] = OBSTACLE
        g = GridMap(width=3, height=3, cells=cells, start=(0, 1), goal=(2, 1))
        env = GridWorldEnv(g)
        env.reset()
        # E -> (1, 1) e obstacol -> coliziune
        r = env.step(1)
        assert r.state == (0, 1)
        assert r.info["collided"]


# ----------------------------------------------------------------------
# Policy
# ----------------------------------------------------------------------
class TestPolicy:
    def test_from_qtable(self):
        q = np.zeros((3, 3, 4))
        q[1, 1, 2] = 5.0  # actiunea 2 e cea mai buna in (1,1)
        p = Policy.from_q_table(q)
        assert p((1, 1)) == 2

    def test_save_load_roundtrip(self, tmp_path):
        q = np.random.rand(4, 4, 4).astype(np.float32)
        p1 = Policy.from_q_table(q)
        p1.save(tmp_path / "policy.json")
        p2 = Policy.load(tmp_path / "policy.json")
        assert np.array_equal(p1.action_grid, p2.action_grid)
        assert p1.algo_name == p2.algo_name


# ----------------------------------------------------------------------
# Q-Learning converges on simple grid
# ----------------------------------------------------------------------
class TestQLearningConverges:
    def test_converges_5x5_empty(self):
        g = empty_grid(5, 5, start=(0, 0), goal=(4, 4))
        env = GridWorldEnv(g, max_steps=200)
        agent = QLearningAgent(env, alpha=0.3, gamma=0.95,
                               eps_start=1.0, eps_decay=0.95, eps_min=0.02,
                               seed=42)
        train_agent(agent, env, n_episodes=300, progress_every=0)

        # Politica greedy ar trebui sa ajunga la goal in <= 2*Manhattan + tolerance
        pol = agent.policy()
        env2 = GridWorldEnv(g, max_steps=50)
        res = rollout(env2, pol)
        assert res.reached_goal
        assert res.steps <= 12   # Manhattan e 8, permitem 4 ocoluri

    def test_eps_decays(self):
        g = empty_grid()
        env = GridWorldEnv(g)
        agent = QLearningAgent(env, eps_start=1.0, eps_decay=0.99, eps_min=0.1)
        for _ in range(500):
            agent.end_episode()
        assert agent.eps == pytest.approx(0.1, abs=1e-3)


# ----------------------------------------------------------------------
# SARSA also converges
# ----------------------------------------------------------------------
class TestSARSAConverges:
    def test_converges_5x5_empty(self):
        g = empty_grid(5, 5, start=(0, 0), goal=(4, 4))
        env = GridWorldEnv(g, max_steps=200)
        agent = SARSAAgent(env, alpha=0.3, gamma=0.95,
                           eps_start=1.0, eps_decay=0.95, eps_min=0.02,
                           seed=42)
        train_agent(agent, env, n_episodes=500, progress_every=0)
        pol = agent.policy()
        env2 = GridWorldEnv(g, max_steps=50)
        res = rollout(env2, pol)
        assert res.reached_goal


# ----------------------------------------------------------------------
# Trainer + statistici
# ----------------------------------------------------------------------
class TestTrainerStats:
    def test_collects_all_metrics(self):
        g = empty_grid()
        env = GridWorldEnv(g, max_steps=100)
        agent = QLearningAgent(env, seed=1)
        stats = train_agent(agent, env, n_episodes=20, progress_every=0)
        assert len(stats.rewards) == 20
        assert len(stats.steps) == 20
        assert len(stats.success_flags) == 20
        assert len(stats.epsilons) == 20

    def test_rolling_success_monotonic_window(self):
        g = empty_grid()
        env = GridWorldEnv(g)
        agent = QLearningAgent(env, seed=1)
        stats = train_agent(agent, env, n_episodes=10, progress_every=0)
        r = stats.rolling_success(window=5)
        assert len(r) == 10
        assert all(0 <= v <= 1 for v in r)


# ----------------------------------------------------------------------
# evaluate_policy
# ----------------------------------------------------------------------
class TestEvaluate:
    def test_random_policy_low_success(self):
        g = empty_grid(8, 8)
        env = GridWorldEnv(g, max_steps=40)
        # politica complet random = actiunea 0 (N) intotdeauna - nu ajunge pe diag
        random_policy = Policy(np.zeros((8, 8), dtype=np.int8), algo_name="random")
        metrics = evaluate_policy(env, random_policy, n_episodes=10)
        assert metrics["success_rate"] < 0.5
