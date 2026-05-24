"""GridWorldEnv: mediu RL pe grid, API tip Gymnasium."""

from __future__ import annotations

import random
from dataclasses import dataclass

import numpy as np

from nav_robot.map.grid_map import Cell, GridMap


# Actiuni: (dx, dy)
ACTIONS_4 = ((0, 1), (1, 0), (0, -1), (-1, 0))    # N, E, S, V
ACTIONS_8 = ACTIONS_4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))

ACTION_LABELS_4 = ["N", "E", "S", "V"]
ACTION_LABELS_8 = ACTION_LABELS_4 + ["NE", "SE", "NV", "SV"]


@dataclass
class StepResult:
    state: Cell
    reward: float
    done: bool
    info: dict


class GridWorldEnv:
    """Mediu RL discret pe GridMap.

    Stari: celulele libere (x, y).
    Actiuni: 4 sau 8 directii.
    Recompense:
        - reach_goal_bonus la atingerea goal-ului (default +100)
        - collision_penalty la lovire obstacol / iesire din harta (default -10);
          robotul ramane pe loc
        - step_cost per pas (default -1)
    Episod terminat: ajuns la goal SAU `max_steps` atinsi.

    API:
        reset(seed=None) -> state
        step(action_idx) -> StepResult
    """

    def __init__(self, grid: GridMap, diagonal: bool = False,
                 max_steps: int | None = None,
                 reach_goal_bonus: float = 100.0,
                 collision_penalty: float = -10.0,
                 step_cost: float = -1.0,
                 random_start: bool = False,
                 seed: int | None = None) -> None:
        self.grid = grid
        self.actions = ACTIONS_8 if diagonal else ACTIONS_4
        self.action_labels = ACTION_LABELS_8 if diagonal else ACTION_LABELS_4
        self.n_actions = len(self.actions)
        self.max_steps = max_steps or (grid.width * grid.height * 2)
        self.reach_goal_bonus = reach_goal_bonus
        self.collision_penalty = collision_penalty
        self.step_cost = step_cost
        self.random_start = random_start
        self._rng = random.Random(seed)

        # Stare
        self.state: Cell = grid.start
        self.steps: int = 0
        self.total_reward: float = 0.0

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------
    def reset(self, seed: int | None = None) -> Cell:
        """Reseteaza mediul. Returneaza starea initiala."""
        if seed is not None:
            self._rng.seed(seed)

        if self.random_start:
            self.state = self._random_free_cell()
        else:
            self.state = self.grid.start
        self.steps = 0
        self.total_reward = 0.0
        return self.state

    def step(self, action: int) -> StepResult:
        """Aplica o actiune. Returneaza StepResult(state, reward, done, info)."""
        if not (0 <= action < self.n_actions):
            raise ValueError(f"Actiune invalida: {action}")
        dx, dy = self.actions[action]
        x, y = self.state
        nx, ny = x + dx, y + dy
        new_cell = (nx, ny)

        if self.grid.is_free(new_cell):
            self.state = new_cell
            reward = self.step_cost
            collided = False
        else:
            reward = self.step_cost + self.collision_penalty
            collided = True

        self.steps += 1
        done = False
        if self.state == self.grid.goal:
            reward += self.reach_goal_bonus
            done = True
        elif self.steps >= self.max_steps:
            done = True

        self.total_reward += reward
        return StepResult(
            state=self.state,
            reward=reward,
            done=done,
            info={"collided": collided, "steps": self.steps,
                  "reached_goal": self.state == self.grid.goal},
        )

    # ------------------------------------------------------------------
    # Utilitare
    # ------------------------------------------------------------------
    def _random_free_cell(self) -> Cell:
        free = self.free_cells()
        # Eviti goal-ul ca start (altfel episodul se termina imediat)
        candidates = [c for c in free if c != self.grid.goal]
        return self._rng.choice(candidates) if candidates else self.grid.start

    def free_cells(self) -> list[Cell]:
        return [(x, y) for y in range(self.grid.height)
                for x in range(self.grid.width)
                if self.grid.cells[y, x] == 0]

    def state_count(self) -> int:
        return self.grid.width * self.grid.height

    def state_to_index(self, state: Cell) -> int:
        x, y = state
        return y * self.grid.width + x

    def index_to_state(self, idx: int) -> Cell:
        return (idx % self.grid.width, idx // self.grid.width)
