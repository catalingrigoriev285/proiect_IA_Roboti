"""Run registry utilities for reproducible experiment outputs."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import pandas as pd


def _timestamp() -> str:
    """Return a compact timestamp suitable for folder names.

    Returns:
        A timestamp string in YYYYMMDD-HHMMSS format.
    """
    return time.strftime("%Y%m%d-%H%M%S")


@dataclass
class RunRegistry:
    """Manage experiment output directories and artifacts.

    Args:
        base_dir: Base output directory for runs.
    """

    base_dir: Path

    def __post_init__(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_run_dir(self, prefix: str) -> Path:
        """Create and return a new run directory.

        Args:
            prefix: Prefix to include in the folder name.

        Returns:
            Path to the created run directory.
        """
        run_dir = self.base_dir / f"{_timestamp()}_{prefix}"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "plots").mkdir(exist_ok=True)
        (run_dir / "artifacts").mkdir(exist_ok=True)
        return run_dir

    def save_config(self, run_dir: Path, config: Dict[str, Any]) -> None:
        """Save configuration to config.json.

        Args:
            run_dir: Run directory path.
            config: Configuration dictionary.
        """
        path = run_dir / "config.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, sort_keys=True)

    def save_results(self, run_dir: Path, results: pd.DataFrame) -> None:
        """Save results to results.csv.

        Args:
            run_dir: Run directory path.
            results: Results DataFrame.
        """
        path = run_dir / "results.csv"
        results.to_csv(path, index=False)

    def save_plot(self, run_dir: Path, name: str, fig) -> Path:
        """Save a matplotlib figure to the plots folder.

        Args:
            run_dir: Run directory path.
            name: Base name of the plot file (without extension).
            fig: Matplotlib figure.

        Returns:
            Path to the saved plot.
        """
        plot_path = run_dir / "plots" / f"{name}.png"
        fig.savefig(plot_path, dpi=150, bbox_inches="tight")
        return plot_path

    def save_artifact(self, run_dir: Path, name: str, payload: Dict[str, Any]) -> Path:
        """Save a JSON artifact to the artifacts folder.

        Args:
            run_dir: Run directory path.
            name: Base name of the artifact file (without extension).
            payload: JSON-serializable artifact.

        Returns:
            Path to the saved artifact.
        """
        artifact_path = run_dir / "artifacts" / f"{name}.json"
        with artifact_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)
        return artifact_path

    def record_run(
        self,
        prefix: str,
        config: Dict[str, Any],
        results: pd.DataFrame,
        figures: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Create a run folder and save config, results, and plots.

        Args:
            prefix: Prefix for the run folder name.
            config: Configuration dictionary.
            results: Results DataFrame.
            figures: Optional mapping of plot name to matplotlib figure.

        Returns:
            Path to the created run directory.
        """
        run_dir = self.create_run_dir(prefix=prefix)
        self.save_config(run_dir, config)
        self.save_results(run_dir, results)
        if figures:
            for name, fig in figures.items():
                self.save_plot(run_dir, name, fig)
        return run_dir

    @staticmethod
    def list_runs(base_dir: Path) -> Iterable[Path]:
        """List run directories sorted by creation time.

        Args:
            base_dir: Base output directory for runs.

        Returns:
            Iterable of run directory paths.
        """
        if not base_dir.exists():
            return []
        return sorted(
            [p for p in base_dir.iterdir() if p.is_dir()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
