"""Algoritm Bug2 - navigare reactiva spre tinta cunoscuta (faza 4 - stub).

Concept:
    1. Se calculeaza m-line: segmentul drept start->goal.
    2. Robotul merge spre goal pana intalneste un obstacol.
    3. Urmareste conturul obstacolului pana reintalneste m-line mai aproape de goal.
    4. Reia mersul direct catre goal.
"""

from __future__ import annotations


def bug2_navigate(sim, robot, goal_world: tuple[float, float]) -> bool:
    """
    Args:
        sim: API CoppeliaSim (din coppeliasim_zmqremoteapi_client).
        robot: instanta PioneerP3DX (vezi nav_robot.coppelia.robot).
        goal_world: (x_m, y_m) - tinta in coordonate world.

    Returns:
        True daca s-a atins tinta, False daca s-a abandonat (timeout / blocaj).
    """
    raise NotImplementedError(
        "bug2_navigate - TODO faza 4: stari GO_TO_GOAL / FOLLOW_WALL + verificare m-line."
    )
