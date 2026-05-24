"""Vizualizari matplotlib pentru RL: heatmap Q-values, sageti politica, curbe."""

from __future__ import annotations

import numpy as np
from matplotlib.axes import Axes

from nav_robot.map.grid_map import GridMap
from nav_robot.rl.env import ACTIONS_4, ACTIONS_8
from nav_robot.rl.policy import Policy


def plot_q_heatmap(grid: GridMap, q_table: np.ndarray, ax: Axes,
                   title: str = "Q-values (max per celula)") -> Axes:
    """Heatmap cu max(Q[s, :]) pe fiecare celula libera."""
    values = q_table.max(axis=2).astype(float)
    # Mascheaza obstacolele
    masked = np.ma.masked_where(grid.cells != 0, values)
    im = ax.imshow(masked, origin="lower",
                   extent=(0, grid.width, 0, grid.height),
                   cmap="viridis", interpolation="nearest", aspect="equal")
    ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    _mark_start_goal(ax, grid)
    ax.set_title(title)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    return ax


def plot_policy_arrows(grid: GridMap, policy: Policy, ax: Axes,
                       title: str = "Politica (argmax)") -> Axes:
    """Sageti pe fiecare celula libera, in directia data de politica."""
    actions = ACTIONS_8 if policy.action_grid.max() > 3 else ACTIONS_4
    xs, ys, us, vs = [], [], [], []
    for y in range(grid.height):
        for x in range(grid.width):
            if grid.cells[y, x] != 0 or (x, y) == grid.goal:
                continue
            a = int(policy.action_grid[y, x])
            dx, dy = actions[a]
            xs.append(x + 0.5)
            ys.append(y + 0.5)
            us.append(dx * 0.4)
            vs.append(dy * 0.4)
    # Fundal: obstacole negre
    obs = np.ma.masked_where(grid.cells == 0, grid.cells.astype(float))
    ax.imshow(obs, origin="lower", cmap="gray_r",
              extent=(0, grid.width, 0, grid.height),
              interpolation="nearest", aspect="equal", alpha=0.7)
    ax.quiver(xs, ys, us, vs, color="#3498db", angles="xy",
              scale_units="xy", scale=1, width=0.005)
    _mark_start_goal(ax, grid)
    ax.set_xlim(0, grid.width)
    ax.set_ylim(0, grid.height)
    ax.set_aspect("equal")
    ax.set_title(title)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    return ax


def plot_rewards(rewards: list[float], ax: Axes,
                 rolling: list[float] | None = None,
                 title: str = "Recompensa per episod") -> Axes:
    ax.plot(rewards, color="#bbbbbb", linewidth=0.8, label="per episod")
    if rolling is not None and rolling:
        ax.plot(rolling, color="#3498db", linewidth=2.0, label="media (window=50)")
    ax.set_xlabel("Episod")
    ax.set_ylabel("Recompensa totala")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right")
    return ax


def plot_success_rate(rolling_success: list[float], ax: Axes,
                      title: str = "Rata de succes (rolling)") -> Axes:
    ax.plot([s * 100 for s in rolling_success], color="#27ae60", linewidth=2.0)
    ax.set_xlabel("Episod")
    ax.set_ylabel("Success rate (%)")
    ax.set_ylim(0, 105)
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    return ax


def plot_ga_convergence(stats, ax: Axes,
                        title: str = "GA: convergenta fitness") -> Axes:
    """stats = GAStats; ploteaza best + mean per generatie."""
    gens = list(range(1, len(stats.best_fitness) + 1))
    ax.plot(gens, stats.best_fitness, color="#3498db", linewidth=2.0, label="best")
    ax.plot(gens, stats.mean_fitness, color="#bbbbbb", linewidth=1.0, label="mean")
    ax.set_xlabel("Generatie")
    ax.set_ylabel("Fitness")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    return ax


def _mark_start_goal(ax: Axes, grid: GridMap) -> None:
    sx, sy = grid.start
    gx, gy = grid.goal
    ax.scatter([sx + 0.5], [sy + 0.5], c="#2ecc71", s=120, marker="o",
               edgecolors="black", linewidths=1.0, zorder=10)
    ax.scatter([gx + 0.5], [gy + 0.5], c="#e74c3c", s=140, marker="*",
               edgecolors="black", linewidths=1.0, zorder=10)
