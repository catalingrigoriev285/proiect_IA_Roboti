"""Reprezentari de politici si helper-e de serializare."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from nav_robot.map.grid_map import Cell


class Policy:
    """Politica deterministica per celula (sau peste un Q-table).

    Constructorul accepta fie:
        - un Q-table (numpy array de forma (H, W, n_actions))
        - o matrice de actiuni (numpy array (H, W) de int) - politica pura
    """

    def __init__(self, action_grid: np.ndarray, q_table: np.ndarray | None = None,
                 width: int | None = None, height: int | None = None,
                 algo_name: str = "unknown") -> None:
        self.action_grid = action_grid.astype(np.int8)
        self.q_table = q_table  # poate fi None pentru politici GA
        self.height, self.width = action_grid.shape
        if width is not None:
            assert width == self.width
        if height is not None:
            assert height == self.height
        self.algo_name = algo_name

    @classmethod
    def from_q_table(cls, q_table: np.ndarray, algo_name: str = "qlearning") -> "Policy":
        """q_table forma (H, W, n_actions). Construieste action_grid = argmax."""
        action_grid = np.argmax(q_table, axis=2).astype(np.int8)
        return cls(action_grid=action_grid, q_table=q_table, algo_name=algo_name)

    def action(self, cell: Cell) -> int:
        x, y = cell
        return int(self.action_grid[y, x])

    def __call__(self, cell: Cell) -> int:
        return self.action(cell)

    # --------- Serializare ---------
    def to_dict(self) -> dict:
        return {
            "width": self.width,
            "height": self.height,
            "algo_name": self.algo_name,
            "action_grid": self.action_grid.tolist(),
            "q_table": self.q_table.tolist() if self.q_table is not None else None,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Policy":
        ag = np.array(d["action_grid"], dtype=np.int8)
        q = np.array(d["q_table"]) if d.get("q_table") is not None else None
        return cls(ag, q_table=q, algo_name=d.get("algo_name", "unknown"))

    def save(self, path: str | Path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return p.resolve()

    @classmethod
    def load(cls, path: str | Path) -> "Policy":
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(d)
