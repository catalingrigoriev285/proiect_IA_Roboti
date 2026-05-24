"""Q-Learning tabular (off-policy)."""

from __future__ import annotations

import random

import numpy as np

from nav_robot.map.grid_map import Cell
from nav_robot.rl.env import GridWorldEnv
from nav_robot.rl.policy import Policy


class QLearningAgent:
    """Agent Q-Learning tabular cu politica epsilon-greedy si epsilon decay.

    Update Bellman:
        Q[s, a] += alpha * (r + gamma * max(Q[s', :]) - Q[s, a])
    """

    name = "qlearning"

    def __init__(self, env: GridWorldEnv,
                 alpha: float = 0.1, gamma: float = 0.95,
                 eps_start: float = 1.0, eps_decay: float = 0.995,
                 eps_min: float = 0.05,
                 seed: int | None = None) -> None:
        self.env = env
        self.alpha = alpha
        self.gamma = gamma
        self.eps = eps_start
        self.eps_decay = eps_decay
        self.eps_min = eps_min
        self.q = np.zeros((env.grid.height, env.grid.width, env.n_actions),
                          dtype=np.float32)
        self._rng = random.Random(seed)

    def select_action(self, state: Cell) -> int:
        if self._rng.random() < self.eps:
            return self._rng.randrange(self.env.n_actions)
        x, y = state
        return int(np.argmax(self.q[y, x]))

    def select_action_greedy(self, state: Cell) -> int:
        x, y = state
        return int(np.argmax(self.q[y, x]))

    def update(self, s: Cell, a: int, r: float, s_next: Cell, done: bool) -> None:
        sx, sy = s
        nx, ny = s_next
        target = r if done else r + self.gamma * float(np.max(self.q[ny, nx]))
        self.q[sy, sx, a] += self.alpha * (target - self.q[sy, sx, a])

    def end_episode(self) -> None:
        self.eps = max(self.eps_min, self.eps * self.eps_decay)

    def policy(self) -> Policy:
        return Policy.from_q_table(self.q, algo_name=self.name)
