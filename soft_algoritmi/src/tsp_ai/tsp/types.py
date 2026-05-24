"""Dataclasses and typing helpers for TSP algorithms."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class TSPResult:
    """Result container for TSP algorithms.

    Args:
        tour: Ordered list of city indices.
        cost: Total tour cost including return to start.
        elapsed_sec: Execution time in seconds.
        algorithm: Algorithm identifier.
        params: Algorithm parameters used.
        meta: Extra metadata.
        history: Optional history data for convergence plots.
    """

    tour: List[int]
    cost: float
    elapsed_sec: float
    algorithm: str
    params: Dict[str, Any]
    meta: Dict[str, Any]
    history: Optional[Dict[str, List[float]]] = None
