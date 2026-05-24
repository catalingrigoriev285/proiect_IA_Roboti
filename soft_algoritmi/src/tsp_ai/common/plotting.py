"""Shared matplotlib and seaborn utilities."""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import seaborn as sns


def apply_mpl_style(dark: bool = True) -> None:
    """Apply a consistent matplotlib and seaborn style.

    Args:
        dark: Whether to use the dark theme palette.
    """
    sns.set_theme(style="whitegrid", context="talk")
    if dark:
        plt.rcParams.update(
            {
                "figure.facecolor": "#0F172A",
                "axes.facecolor": "#111827",
                "axes.edgecolor": "#334155",
                "axes.labelcolor": "#E5E7EB",
                "text.color": "#E5E7EB",
                "xtick.color": "#94A3B8",
                "ytick.color": "#94A3B8",
                "grid.color": "#334155",
                "grid.alpha": 0.4,
            }
        )
    plt.rcParams.update(
        {
            "figure.figsize": (8, 5),
            "axes.titlesize": 14,
            "axes.labelsize": 12,
            "legend.fontsize": 10,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def create_figure(dark: bool = True) -> plt.Figure:
    """Create a new matplotlib figure with the project style applied.

    Returns:
        A matplotlib Figure.
    """
    apply_mpl_style(dark=dark)
    fig = plt.figure()
    return fig


def create_placeholder_figure(dark: bool = True) -> plt.Figure:
    """Create a blank figure that matches the app theme background."""
    apply_mpl_style(dark=dark)
    fig, ax = plt.subplots()
    ax.set_axis_off()
    ax.set_facecolor(plt.rcParams.get("axes.facecolor", "#111827"))
    fig.patch.set_facecolor(plt.rcParams.get("figure.facecolor", "#0F172A"))
    return fig
