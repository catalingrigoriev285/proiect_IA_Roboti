"""Trainer generic pentru Q-Learning / SARSA pe GridWorldEnv."""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Protocol

import numpy as np

from nav_robot.rl.env import GridWorldEnv
from nav_robot.rl.policy import Policy

log = logging.getLogger("rl.trainer")


class _Agent(Protocol):
    """Minimal protocol pentru agentii compatibili cu trainer-ul generic."""

    name: str

    def select_action(self, state) -> int: ...
    def end_episode(self) -> None: ...
    def policy(self) -> Policy: ...


@dataclass
class EpisodeResult:
    reward: float
    steps: int
    reached_goal: bool


@dataclass
class TrainStats:
    """Statistici complete dupa antrenare."""
    algo: str
    episodes: int
    rewards: list[float] = field(default_factory=list)
    steps: list[int] = field(default_factory=list)
    success_flags: list[bool] = field(default_factory=list)
    epsilons: list[float] = field(default_factory=list)
    elapsed_s: float = 0.0

    def rolling_success(self, window: int = 50) -> list[float]:
        flags = np.array(self.success_flags, dtype=float)
        if len(flags) == 0:
            return []
        out = []
        for i in range(len(flags)):
            start = max(0, i - window + 1)
            out.append(float(flags[start:i + 1].mean()))
        return out

    def rolling_reward(self, window: int = 50) -> list[float]:
        rew = np.array(self.rewards, dtype=float)
        if len(rew) == 0:
            return []
        out = []
        for i in range(len(rew)):
            start = max(0, i - window + 1)
            out.append(float(rew[start:i + 1].mean()))
        return out


def train_agent(
    agent,
    env: GridWorldEnv,
    n_episodes: int = 1000,
    on_episode: Callable[[int, EpisodeResult, TrainStats], None] | None = None,
    progress_every: int = 50,
    should_stop: Callable[[], bool] | None = None,
) -> TrainStats:
    """Antreneaza un agent (Q-Learning sau SARSA) pe `n_episodes`.

    Args:
        agent: instanta cu metode select_action, end_episode, update (specific).
        env: mediul (GridWorldEnv).
        n_episodes: numarul de episoade.
        on_episode: callback (episode_idx, EpisodeResult, stats) - util pentru live plotting.
        progress_every: frecventa de logging.
        should_stop: callable optional - daca True, opreste antrenarea.

    Returns:
        TrainStats cu toate metricele.
    """
    import time
    stats = TrainStats(algo=agent.name, episodes=n_episodes)
    t_start = time.perf_counter()

    is_sarsa = (agent.name == "sarsa")

    for ep in range(n_episodes):
        if should_stop is not None and should_stop():
            log.info("Antrenare oprita la episodul %d/%d.", ep, n_episodes)
            stats.episodes = ep
            break

        s = env.reset()
        a = agent.select_action(s) if is_sarsa else None
        ep_reward = 0.0
        ep_steps = 0
        reached = False

        while True:
            if not is_sarsa:
                a = agent.select_action(s)
            res = env.step(a)
            if is_sarsa and not res.done:
                a_next = agent.select_action(res.state)
                agent.update(s, a, res.reward, res.state, a_next, res.done)
                a = a_next
            elif is_sarsa and res.done:
                agent.update(s, a, res.reward, res.state, 0, res.done)
            else:
                agent.update(s, a, res.reward, res.state, res.done)

            s = res.state
            ep_reward += res.reward
            ep_steps += 1
            if res.done:
                reached = res.info.get("reached_goal", False)
                break

        agent.end_episode()
        stats.rewards.append(ep_reward)
        stats.steps.append(ep_steps)
        stats.success_flags.append(reached)
        stats.epsilons.append(getattr(agent, "eps", 0.0))

        if on_episode is not None:
            on_episode(ep, EpisodeResult(ep_reward, ep_steps, reached), stats)

        if progress_every and (ep + 1) % progress_every == 0:
            window = stats.success_flags[-progress_every:]
            sr = sum(window) / len(window)
            mean_r = sum(stats.rewards[-progress_every:]) / len(window)
            log.info("[%s] ep %d/%d  eps=%.3f  success_rate=%.0f%%  reward_avg=%.1f",
                     agent.name, ep + 1, n_episodes,
                     getattr(agent, "eps", 0.0), sr * 100, mean_r)

    stats.elapsed_s = time.perf_counter() - t_start
    log.info("[%s] Antrenare finalizata in %.2fs (%d episoade).",
             agent.name, stats.elapsed_s, stats.episodes)
    return stats


def rollout(env: GridWorldEnv, policy: Policy,
            max_steps: int | None = None) -> EpisodeResult:
    """Ruleaza politica greedy (deterministica) o data si returneaza rezultatul."""
    s = env.reset()
    total = 0.0
    steps = 0
    reached = False
    limit = max_steps or env.max_steps
    for _ in range(limit):
        a = policy(s)
        res = env.step(a)
        total += res.reward
        s = res.state
        steps += 1
        if res.done:
            reached = res.info.get("reached_goal", False)
            break
    return EpisodeResult(total, steps, reached)


def evaluate_policy(env: GridWorldEnv, policy: Policy, n_episodes: int = 50,
                    random_start: bool = False) -> dict:
    """Evalueaza o politica pe N episoade greedy. Returneaza dict cu metrici agregate."""
    rewards = []
    steps_arr = []
    successes = 0
    original_random = env.random_start
    env.random_start = random_start
    try:
        for _ in range(n_episodes):
            r = rollout(env, policy)
            rewards.append(r.reward)
            steps_arr.append(r.steps)
            if r.reached_goal:
                successes += 1
    finally:
        env.random_start = original_random
    return {
        "success_rate": successes / n_episodes,
        "mean_reward": float(np.mean(rewards)),
        "mean_steps": float(np.mean(steps_arr)),
        "n_episodes": n_episodes,
    }
