"""Construirea dinamica a scenei CoppeliaSim din GridMap (faza 3 - stub)."""

from __future__ import annotations

from nav_robot.map.grid_map import GridMap


def build_obstacles_from_map(sim, grid: GridMap, height_m: float = 0.5,
                             parent_name: str = "MapObstacles") -> list[int]:
    """Plaseaza cate un cuboid in scena pentru fiecare celula obstacol.

    Cuboizii sunt grupati sub un dummy comun pentru a putea fi sterse rapid intre rulari.

    Args:
        sim: API CoppeliaSim.
        grid: harta sursa.
        height_m: inaltimea pe Z a cuboizilor.
        parent_name: numele dummy-ului parinte.

    Returns:
        Lista handle-urilor create.
    """
    raise NotImplementedError(
        "build_obstacles_from_map - TODO faza 3: pentru fiecare celula obstacol, "
        "creeaza sim.createPrimitiveShape(sim.primitiveshape_cuboid, [cell_size, cell_size, h]) "
        "si pozitioneaza cu sim.setObjectPosition. Returneaza lista handle-uri."
    )


def clear_obstacles(sim, handles: list[int]) -> None:
    """Sterge cuboizii create anterior pentru a re-genera scena."""
    raise NotImplementedError(
        "clear_obstacles - TODO faza 3: sim.removeObjects(handles)."
    )
