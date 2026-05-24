"""Plotting utilities for NLP experiments."""

from __future__ import annotations

from typing import List

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.model_selection import learning_curve

from tsp_ai.common.plotting import apply_mpl_style


def plot_confusion_matrix(cm: np.ndarray, title: str, subtitle: str | None = None) -> plt.Figure:
    """Plot a confusion matrix heatmap.

    Args:
        cm: Confusion matrix array.
        dataset: Dataset name.
        model: Model name.

    Returns:
        Matplotlib figure.
    """
    apply_mpl_style(dark=True)
    fig, ax = plt.subplots()
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax)
    if subtitle:
        ax.set_title(f"{title} ({subtitle})")
    else:
        ax.set_title(title)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    return fig


def plot_learning_curve(estimator, X, y) -> plt.Figure:
    """Plot a learning curve for a model.

    Args:
        estimator: Scikit-learn estimator.
        X: Training texts.
        y: Labels.

    Returns:
        Matplotlib figure.
    """
    apply_mpl_style(dark=True)
    train_sizes, train_scores, test_scores = learning_curve(
        estimator, X, y, cv=3, n_jobs=1, train_sizes=np.linspace(0.1, 1.0, 5)
    )
    fig, ax = plt.subplots()
    ax.plot(train_sizes, train_scores.mean(axis=1), label="Train")
    ax.plot(train_sizes, test_scores.mean(axis=1), label="Validation")
    ax.set_title("Learning Curve")
    ax.set_xlabel("Training Size")
    ax.set_ylabel("Score")
    ax.legend()
    return fig


def plot_model_comparison(rows: List[dict]) -> plt.Figure:
    """Plot a model comparison bar chart.

    Args:
        rows: List of results dicts with dataset/model/metric.

    Returns:
        Matplotlib figure.
    """
    apply_mpl_style(dark=True)
    fig, ax = plt.subplots()
    labels = [f"{r['dataset']}-{r['model']}" for r in rows]
    scores = [r["macro_f1"] for r in rows]
    ax.bar(labels, scores)
    ax.set_title("Model Comparison (Macro F1)")
    ax.set_ylabel("Macro F1")
    ax.set_xticklabels(labels, rotation=45, ha="right")
    return fig


def plot_comparison_bars(rows: List[dict], title: str) -> plt.Figure:
    """Plot a comparison bar chart for classifier scores.

    Args:
        rows: List of result dictionaries.
        title: Plot title.

    Returns:
        Matplotlib figure.
    """
    apply_mpl_style(dark=True)
    fig, ax = plt.subplots()
    labels = [r["label"] for r in rows]
    scores = [r["accuracy"] for r in rows]
    ax.bar(labels, scores, color="#38BDF8")
    ax.set_title(title)
    ax.set_ylabel("Accuracy")
    ax.set_xticklabels(labels, rotation=30, ha="right")
    return fig


def plot_heatmap(grid: np.ndarray, x_labels: List[str], y_labels: List[str], title: str) -> plt.Figure:
    """Plot a heatmap for grid search results.

    Args:
        grid: 2D accuracy grid.
        x_labels: Labels for max_features.
        y_labels: Labels for ngram ranges.
        title: Plot title.

    Returns:
        Matplotlib figure.
    """
    apply_mpl_style(dark=True)
    fig, ax = plt.subplots()
    sns.heatmap(grid, annot=True, fmt=".3f", cmap="viridis", ax=ax)
    ax.set_xticklabels(x_labels, rotation=30, ha="right")
    ax.set_yticklabels(y_labels, rotation=0)
    ax.set_title(title)
    ax.set_xlabel("max_features")
    ax.set_ylabel("ngram_range")
    return fig
