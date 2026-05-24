"""Unified result schema for TSP and NLP experiments."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd


@dataclass
class ExperimentResult:
    """Unified experiment result schema.

    Args:
        run_type: Type of run (tsp, nlp).
        task: Task identifier (solver, bench, lab10_taskX).
        metrics: List of metric rows to store in results.csv.
        summary: Short summary fields for UI display.
    """

    run_type: str
    task: str
    metrics: List[Dict[str, Any]]
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert metrics to a DataFrame.

        Returns:
            DataFrame built from metrics rows.
        """
        return pd.DataFrame(self.metrics)

    def to_json(self) -> Dict[str, Any]:
        """Convert the result summary to a JSON-serializable dict.

        Returns:
            Dictionary representation of the summary.
        """
        return {
            "run_type": self.run_type,
            "task": self.task,
            "summary": self.summary,
        }
