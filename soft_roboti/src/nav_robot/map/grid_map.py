"""GridMap - reprezentarea unei harti 2D cu celule libere / obstacole."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import numpy as np

from nav_robot.config import DEFAULT_CELL_SIZE


FREE: int = 0
OBSTACLE: int = 1

Cell = tuple[int, int]


@dataclass
class GridMap:
    """
    Harta 2D de tip occupancy grid.

    Convensii:
        cells[y, x] = 0 -> celula libera
        cells[y, x] = 1 -> obstacol
        coordonata (0, 0) este coltul stanga-jos in spatiul world.

    Attributes:
        width: numar de celule pe orizontala (X).
        height: numar de celule pe verticala (Y).
        cells: numpy.ndarray (height, width) cu valori 0/1.
        start: celula (x, y) de pornire a robotului.
        goal: celula (x, y) a tintei.
        cell_size: metri per celula (folosit la conversia in coordonate world).
        seed: seed-ul folosit la generare (None daca harta a fost incarcata manual).
    """

    width: int
    height: int
    cells: np.ndarray
    start: Cell
    goal: Cell
    cell_size: float = DEFAULT_CELL_SIZE
    seed: int | None = None

    def __post_init__(self) -> None:
        if self.cells.shape != (self.height, self.width):
            raise ValueError(
                f"cells.shape={self.cells.shape} nu corespunde cu (height={self.height}, width={self.width})"
            )
        if self.cells.dtype != np.uint8:
            self.cells = self.cells.astype(np.uint8)
        if not self._in_bounds(self.start):
            raise ValueError(f"start={self.start} este in afara hartii")
        if not self._in_bounds(self.goal):
            raise ValueError(f"goal={self.goal} este in afara hartii")

    # ------------------------------------------------------------------
    # Interogari
    # ------------------------------------------------------------------
    def is_free(self, cell: Cell) -> bool:
        """True daca celula este in harta si nu este obstacol."""
        x, y = cell
        if not self._in_bounds(cell):
            return False
        return bool(self.cells[y, x] == FREE)

    def neighbors(self, cell: Cell, diagonal: bool = False) -> list[Cell]:
        """
        Returneaza celulele libere vecine cu `cell`.

        Args:
            cell: celula curenta (x, y).
            diagonal: daca True, include cei 4 vecini diagonali (8-connectivity).

        Returns:
            Lista de celule libere accesibile direct.
        """
        x, y = cell
        offsets: Iterable[Cell] = ((1, 0), (-1, 0), (0, 1), (0, -1))
        if diagonal:
            offsets = list(offsets) + [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        result: list[Cell] = []
        for dx, dy in offsets:
            n = (x + dx, y + dy)
            if self.is_free(n):
                result.append(n)
        return result

    def _in_bounds(self, cell: Cell) -> bool:
        x, y = cell
        return 0 <= x < self.width and 0 <= y < self.height

    # ------------------------------------------------------------------
    # Conversii harta <-> world
    # ------------------------------------------------------------------
    def to_world(self, cell: Cell) -> tuple[float, float]:
        """Centrul celulei in coordonate world (metri), origine la (0, 0)."""
        x, y = cell
        return ((x + 0.5) * self.cell_size, (y + 0.5) * self.cell_size)

    def from_world(self, x_m: float, y_m: float) -> Cell:
        """Celula care contine punctul world (x_m, y_m)."""
        return (int(x_m // self.cell_size), int(y_m // self.cell_size))

    def world_size(self) -> tuple[float, float]:
        """Dimensiunile hartii in metri (lungime_x, lungime_y)."""
        return (self.width * self.cell_size, self.height * self.cell_size)

    # ------------------------------------------------------------------
    # Serializare
    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "width": self.width,
            "height": self.height,
            "cell_size": self.cell_size,
            "start": list(self.start),
            "goal": list(self.goal),
            "seed": self.seed,
            "cells": self.cells.tolist(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GridMap":
        return cls(
            width=int(data["width"]),
            height=int(data["height"]),
            cells=np.array(data["cells"], dtype=np.uint8),
            start=tuple(data["start"]),
            goal=tuple(data["goal"]),
            cell_size=float(data.get("cell_size", DEFAULT_CELL_SIZE)),
            seed=data.get("seed"),
        )

    def save(self, path: str | Path) -> Path:
        """Salveaza harta in JSON. Returneaza calea absoluta."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        return path.resolve()

    @classmethod
    def load(cls, path: str | Path) -> "GridMap":
        with Path(path).open("r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))
