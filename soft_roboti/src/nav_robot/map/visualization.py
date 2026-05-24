"""Vizualizare matplotlib pentru harti si trasee planificate."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.colors import ListedColormap
from matplotlib.figure import Figure

from nav_robot.map.grid_map import Cell, GridMap

_CMAP = ListedColormap(["#ffffff", "#202020"])  # 0 = alb (liber), 1 = negru (obstacol)


def plot_map(grid: GridMap, ax: Axes | None = None, title: str | None = None) -> Axes:
    """
    Deseneaza harta cu obstacole, start (verde) si goal (rosu).

    Args:
        grid: harta de afisat.
        ax: axes existente; daca None se creeaza o figura noua.
        title: titlu optional; default include seed-ul daca exista.

    Returns:
        Axes-ul matplotlib pe care s-a desenat.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 7))

    ax.imshow(
        grid.cells,
        cmap=_CMAP,
        origin="lower",
        extent=(0, grid.width, 0, grid.height),
        interpolation="nearest",
    )

    # Linii de grila
    ax.set_xticks(np.arange(0, grid.width + 1, 1), minor=True)
    ax.set_yticks(np.arange(0, grid.height + 1, 1), minor=True)
    ax.grid(which="minor", color="#dddddd", linewidth=0.5)
    ax.tick_params(which="minor", length=0)

    # Start + goal
    sx, sy = grid.start
    gx, gy = grid.goal
    ax.scatter([sx + 0.5], [sy + 0.5], c="#2ecc71", s=180, marker="o",
               edgecolors="black", linewidths=1.0, zorder=5, label="start")
    ax.scatter([gx + 0.5], [gy + 0.5], c="#e74c3c", s=180, marker="*",
               edgecolors="black", linewidths=1.0, zorder=5, label="goal")

    if title is None:
        seed_str = f"seed={grid.seed}" if grid.seed is not None else "seed=?"
        title = f"GridMap {grid.width}x{grid.height} ({seed_str})"
    ax.set_title(title)
    ax.set_xlabel("X (celule)")
    ax.set_ylabel("Y (celule)")
    ax.set_aspect("equal")
    ax.set_xlim(0, grid.width)
    ax.set_ylim(0, grid.height)
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), framealpha=0.9)
    return ax


def plot_path(grid: GridMap, path: Sequence[Cell], ax: Axes | None = None,
              color: str = "#3498db", label: str | None = "traseu") -> Axes:
    """
    Suprapune un traseu peste o harta deja desenata (sau o deseneaza nou).

    Args:
        grid: harta de fundal.
        path: lista de celule (x, y) de la start la goal.
        ax: axes existente; daca None se apeleaza plot_map mai intai.
        color: culoarea liniei traseului.
        label: text pentru legenda.

    Returns:
        Axes-ul pe care s-a desenat.
    """
    if ax is None:
        ax = plot_map(grid)
    if not path:
        return ax
    xs = [c[0] + 0.5 for c in path]
    ys = [c[1] + 0.5 for c in path]
    ax.plot(xs, ys, color=color, linewidth=2.5, marker="o", markersize=4,
            label=label, zorder=4)
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), framealpha=0.9)
    return ax


def save_figure(fig: Figure, output_path: str | Path, dpi: int = 150) -> Path:
    """Salveaza figura ca PNG si returneaza calea absoluta."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=dpi, bbox_inches="tight")
    return out.resolve()
