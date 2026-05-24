"""Planificatoare de traseu."""

from typing import Any

from nav_robot.planners.astar import AStarPlanner
from nav_robot.planners.base import PathPlanner, PlanResult
from nav_robot.planners.bfs import BFSPlanner
from nav_robot.planners.dijkstra import DijkstraPlanner
from nav_robot.planners.rrt import RRTPlanner

__all__ = [
    "PathPlanner", "PlanResult",
    "AStarPlanner", "DijkstraPlanner", "BFSPlanner", "RRTPlanner",
    "get_planner", "PLANNER_NAMES",
]

PLANNER_NAMES = ("astar", "dijkstra", "bfs", "rrt")


def get_planner(name: str, **kwargs: Any) -> PathPlanner:
    """Factory: returneaza o instanta de planner dupa nume.

    Args:
        name: 'astar' | 'dijkstra' | 'bfs' | 'rrt'.
        **kwargs: parametri specifici algoritmului
                  (ex. heuristic, diagonal, max_iter, step_size, ...).

    Raises:
        ValueError: daca name nu e cunoscut.
    """
    n = name.lower().strip()
    if n == "astar":
        return AStarPlanner(**kwargs)
    if n == "dijkstra":
        return DijkstraPlanner(**kwargs)
    if n == "bfs":
        return BFSPlanner(**kwargs)
    if n == "rrt":
        return RRTPlanner(**kwargs)
    raise ValueError(f"Planner necunoscut: {name!r}. Optiuni: {PLANNER_NAMES}")
