"""I/O utilities for TSP data sources."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import List, Tuple

import numpy as np


def read_matrix_file(path: str | Path) -> List[List[int]]:
    """Read a distance matrix from a plain text file.

    Args:
        path: Path to the matrix file.

    Returns:
        Distance matrix.

    Raises:
        ValueError: If the file format is invalid.
    """
    path = Path(path)
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    n = int(lines[0])
    matrix = []
    for row in lines[1:]:
        values = [int(x) for x in row.split()]
        if len(values) != n:
            raise ValueError("Invalid matrix row length.")
        matrix.append(values)
    if len(matrix) != n:
        raise ValueError("Invalid matrix size.")
    return matrix


def read_coordinates_csv(path: str | Path) -> List[Tuple[float, float]]:
    """Read coordinates from a CSV file with x,y columns.

    Args:
        path: Path to the CSV file.

    Returns:
        List of (x, y) coordinates.
    """
    path = Path(path)
    coords: List[Tuple[float, float]] = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            coords.append((float(row["x"]), float(row["y"])) )
    return coords


def coords_to_distance_matrix(coords: List[Tuple[float, float]]) -> List[List[float]]:
    """Build a Euclidean distance matrix from coordinates.

    Args:
        coords: List of (x, y) coordinates.

    Returns:
        Euclidean distance matrix.
    """
    n = len(coords)
    D = [[0.0 for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            dx = coords[i][0] - coords[j][0]
            dy = coords[i][1] - coords[j][1]
            dist = float(np.hypot(dx, dy))
            D[i][j] = dist
            D[j][i] = dist
    return D


def random_distance_matrix(
    n: int,
    low: int,
    high: int,
    seed: int | None = None,
) -> List[List[int]]:
    """Generate a random symmetric distance matrix.

    Args:
        n: Number of cities.
        low: Minimum distance value.
        high: Maximum distance value.
        seed: Random seed.

    Returns:
        Symmetric distance matrix.
    """
    rng = np.random.default_rng(seed)
    D = [[0 for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            value = int(rng.integers(low, high + 1))
            D[i][j] = value
            D[j][i] = value
    return D
