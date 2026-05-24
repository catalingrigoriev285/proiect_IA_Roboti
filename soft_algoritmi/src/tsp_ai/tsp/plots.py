"""Plotting utilities for TSP experiments."""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from tsp_ai.common.plotting import apply_mpl_style


def plot_runtime_vs_n(results: pd.DataFrame) -> plt.Figure:
    """Plot runtime vs N on a linear scale.

    Args:
        results: Benchmark results DataFrame.

    Returns:
        Matplotlib figure.
    """
    apply_mpl_style(dark=True)
    fig, ax = plt.subplots()
    sns.lineplot(data=results, x="N", y="elapsed_sec", hue="algorithm", marker="o", ax=ax)
    ax.set_title("Runtime vs N")
    ax.set_ylabel("Elapsed (s)")
    return fig


def plot_runtime_vs_n_log(results: pd.DataFrame) -> plt.Figure:
    """Plot runtime vs N on a log scale.

    Args:
        results: Benchmark results DataFrame.

    Returns:
        Matplotlib figure.
    """
    apply_mpl_style(dark=True)
    fig, ax = plt.subplots()
    sns.lineplot(data=results, x="N", y="elapsed_sec", hue="algorithm", marker="o", ax=ax)
    ax.set_yscale("log")
    ax.set_title("Runtime vs N (log)")
    ax.set_ylabel("Elapsed (s)")
    return fig


def plot_cost_vs_n(results: pd.DataFrame) -> plt.Figure:
    """Plot cost vs N.

    Args:
        results: Benchmark results DataFrame.

    Returns:
        Matplotlib figure.
    """
    apply_mpl_style(dark=True)
    fig, ax = plt.subplots()
    sns.lineplot(data=results, x="N", y="cost", hue="algorithm", marker="o", ax=ax)
    ax.set_title("Cost vs N")
    ax.set_ylabel("Tour cost")
    return fig


def plot_gap_vs_n(results: pd.DataFrame) -> plt.Figure:
    """Plot gap percent vs N.

    Args:
        results: Benchmark results DataFrame.

    Returns:
        Matplotlib figure.
    """
    apply_mpl_style(dark=True)
    fig, ax = plt.subplots()
    data = results.dropna(subset=["gap_pct"])
    sns.lineplot(data=data, x="N", y="gap_pct", hue="algorithm", marker="o", ax=ax)
    ax.set_title("Gap % vs N")
    ax.set_ylabel("Gap %")
    return fig


def plot_cost_history(history: Dict[str, List[float]], title: str) -> plt.Figure:
    """Plot cost history curves.

    Args:
        history: History dictionary with cost entries.
        title: Plot title.

    Returns:
        Matplotlib figure.
    """
    apply_mpl_style(dark=True)
    fig, ax = plt.subplots()
    for key, values in history.items():
        ax.plot(values, label=key)
    ax.set_title(title)
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Cost")
    ax.legend()
    return fig


def plot_temperature(history: Dict[str, List[float]]) -> plt.Figure:
    """Plot temperature schedule for SA.

    Args:
        history: History dictionary.

    Returns:
        Matplotlib figure.
    """
    apply_mpl_style(dark=True)
    fig, ax = plt.subplots()
    temps = history.get("temperature", [])
    ax.plot(temps)
    ax.set_title("Temperature Schedule")
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Temperature")
    return fig


def plot_acceptance(history: Dict[str, List[float]]) -> plt.Figure:
    """Plot acceptance rate history.

    Args:
        history: History dictionary.

    Returns:
        Matplotlib figure.
    """
    apply_mpl_style(dark=True)
    fig, ax = plt.subplots()
    acc = history.get("acceptance_rate", [])
    ax.plot(acc)
    ax.set_title("Acceptance Rate")
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Acceptance Rate")
    return fig


def plot_distance_heatmap(D: List[List[float]]) -> plt.Figure:
    """Plot a heatmap of the distance matrix.

    Args:
        D: Distance matrix.

    Returns:
        Matplotlib figure.
    """
    apply_mpl_style(dark=True)
    fig, ax = plt.subplots()
    sns.heatmap(np.array(D), ax=ax, cmap="viridis")
    ax.set_title("Distance Matrix Heatmap")
    return fig


def _coords_from_distance_matrix(
    distance_matrix: Sequence[Sequence[float]],
) -> List[Tuple[float, float]]:
    distances = np.array(distance_matrix, dtype=float)
    n = distances.shape[0]
    if n == 0:
        return []
    squared = distances ** 2
    j = np.eye(n) - np.ones((n, n)) / n
    b = -0.5 * j @ squared @ j
    eigenvalues, eigenvectors = np.linalg.eigh(b)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]
    positive = np.maximum(eigenvalues[:2], 0.0)
    coords = eigenvectors[:, :2] * np.sqrt(positive)
    if coords.shape[1] == 1:
        coords = np.hstack([coords, np.zeros((n, 1))])
    return [(float(x), float(y)) for x, y in coords]


def plot_tour(
    coords: Optional[Sequence[Tuple[float, float]]],
    tour: List[int],
    distance_matrix: Optional[Sequence[Sequence[float]]] = None,
) -> plt.Figure:
    """Plot a tour path from coordinates.

    Args:
        coords: Coordinates if available, otherwise None.
        tour: Tour list.

    Returns:
        Matplotlib figure.
    """
    apply_mpl_style(dark=True)
    fig, ax = plt.subplots()
    if not coords and distance_matrix is not None:
        coords = _coords_from_distance_matrix(distance_matrix)
    if coords:
        xs = [coords[i][0] for i in tour] + [coords[tour[0]][0]]
        ys = [coords[i][1] for i in tour] + [coords[tour[0]][1]]
        ax.plot(xs, ys, marker="o")
        ax.set_title("Tour Plot")
    else:
        ax.text(0.5, 0.5, "No coordinates available", ha="center", va="center")
        ax.set_axis_off()
    return fig


def plot_route(
    coords: Optional[Sequence[Tuple[float, float]]],
    tour: List[int],
    distance_matrix: Optional[Sequence[Sequence[float]]] = None,
) -> plt.Figure:
    """Plot a tour route on a blank canvas with numbered points and arrows.

    Args:
        coords: Coordinates if available, otherwise None.
        tour: Tour list.

    Returns:
        Matplotlib figure.
    """
    apply_mpl_style(dark=True)
    fig, ax = plt.subplots()
    ax.set_axis_off()
    if not coords and distance_matrix is not None:
        coords = _coords_from_distance_matrix(distance_matrix)
    if coords:
        xs = [coords[i][0] for i in tour]
        ys = [coords[i][1] for i in tour]
        ax.scatter(xs, ys)
        for city in tour:
            ax.annotate(str(city), (coords[city][0], coords[city][1]), textcoords="offset points", xytext=(4, 4))
        for i in range(len(tour)):
            a = tour[i]
            b = tour[(i + 1) % len(tour)]
            ax.annotate(
                "",
                xy=(coords[b][0], coords[b][1]),
                xytext=(coords[a][0], coords[a][1]),
                arrowprops={"arrowstyle": "->", "linewidth": 1},
            )
        ax.margins(0.1)
    else:
        ax.text(0.5, 0.5, "No coordinates available", ha="center", va="center")
        ax.set_axis_off()
    return fig
