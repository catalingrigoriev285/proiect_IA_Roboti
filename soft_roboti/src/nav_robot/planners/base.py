"""Interfata comuna pentru planificatoare de traseu."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from nav_robot.map.grid_map import Cell, GridMap

Path = list[Cell]


@dataclass
class PlanResult:
    """Rezultatul unei rulari de planificare.

    Attributes:
        path: lista de celule de la start la goal (None daca nu s-a gasit).
        expanded_nodes: numarul de noduri expandate (pentru benchmark).
        cost: costul total al traseului (suma muchiilor).
        elapsed_s: durata in secunde a planificarii.
    """

    path: Path | None
    expanded_nodes: int = 0
    cost: float = 0.0
    elapsed_s: float = 0.0


class PathPlanner(Protocol):
    """Contract pentru orice algoritm de planificare a traseului."""

    name: str

    def plan(self, grid: GridMap, start: Cell, goal: Cell) -> PlanResult:
        """Calculeaza un traseu de la start la goal pe harta data.

        Returns:
            PlanResult cu path=None daca nu exista solutie.
        """
        ...
