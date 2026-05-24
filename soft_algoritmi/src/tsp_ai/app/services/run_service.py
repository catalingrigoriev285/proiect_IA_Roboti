"""Run orchestration and output persistence services."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from tsp_ai.app.services.result_schema import ExperimentResult
from tsp_ai.common.run_registry import RunRegistry


class RunService:
    """Orchestrate saving experiment outputs using RunRegistry."""

    def __init__(self, base_dir: str | Path = "outputs/runs") -> None:
        self.registry = RunRegistry(Path(base_dir))

    def save_run(
        self,
        prefix: str,
        config: Dict[str, Any],
        result: ExperimentResult,
        figures: Optional[Dict[str, Any]] = None,
        artifacts: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Save a run with config, results, plots, and artifacts.

        Args:
            prefix: Folder prefix.
            config: Configuration dictionary.
            result: ExperimentResult object.
            figures: Optional plot figures.
            artifacts: Optional artifacts to save as JSON files.

        Returns:
            Path to the run directory.
        """
        run_dir = self.registry.create_run_dir(prefix)
        self.registry.save_config(run_dir, config)
        self.registry.save_results(run_dir, result.to_dataframe())
        if figures:
            for name, fig in figures.items():
                self.registry.save_plot(run_dir, name, fig)
        if artifacts:
            artifacts_dir = run_dir / "artifacts"
            artifacts_dir.mkdir(exist_ok=True)
            for name, payload in artifacts.items():
                path = artifacts_dir / f"{name}.json"
                path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        summary_path = run_dir / "result.json"
        summary_path.write_text(json.dumps(result.to_json(), indent=2), encoding="utf-8")
        return run_dir
