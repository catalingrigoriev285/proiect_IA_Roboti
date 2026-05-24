"""Bucla de executie a unui traseu in CoppeliaSim (Faza 3)."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Callable

from nav_robot.coppelia.robot import PioneerP3DX
from nav_robot.controller.waypoint_follower import WaypointFollower
from nav_robot.map.grid_map import Cell, GridMap

log = logging.getLogger("controller.runner")


@dataclass
class RunReport:
    """Rezultatul rularii unui traseu."""
    success: bool
    waypoints_total: int
    waypoints_reached: int
    elapsed_s: float
    final_pose: tuple[float, float, float]
    aborted: bool = False


def path_cells_to_world(grid: GridMap, path: list[Cell]) -> list[tuple[float, float]]:
    """Converteste o lista de celule in coordonate world (centrele celulelor)."""
    return [grid.to_world(c) for c in path]


def run_path_in_coppelia(
    sim,
    robot: PioneerP3DX,
    waypoints_world: list[tuple[float, float]],
    rate_hz: float = 20.0,
    timeout_s: float = 120.0,
    v_lin: float = 0.4,
    tolerance_m: float = 0.15,
    should_stop: Callable[[], bool] | None = None,
    on_progress: Callable[[int, int, tuple[float, float, float]], None] | None = None,
) -> RunReport:
    """Conduce robotul Pioneer P3-DX prin lista de waypoint-uri (in coordonate world).

    Args:
        sim: API CoppeliaSim (din `coppelia.client.connect`).
        robot: instanta PioneerP3DX deja initializata.
        waypoints_world: lista de (x_m, y_m).
        rate_hz: frecventa buclei de control.
        timeout_s: limita de siguranta in secunde.
        v_lin: viteza liniara dorita (m/s).
        tolerance_m: distanta sub care un waypoint e considerat atins.
        should_stop: callable optional verificat la fiecare pas; returneaza True ->
                     abandoneaza traseul (folosit pentru butonul Stop din GUI).
        on_progress: callback (index_curent, total, (x, y, yaw)) la fiecare ~0.5s.

    Returns:
        RunReport cu success, timpi, pozitie finala.
    """
    if not waypoints_world:
        return RunReport(True, 0, 0, 0.0, robot.pose())

    follower = WaypointFollower(
        waypoints_world, v_lin=v_lin, tolerance_m=tolerance_m,
    )
    dt = 1.0 / rate_hz
    t_start = time.perf_counter()
    last_progress = t_start

    try:
        while not follower.is_done():
            now = time.perf_counter()
            elapsed = now - t_start
            if elapsed > timeout_s:
                log.warning("Timeout (%.1fs) - opresc robotul.", timeout_s)
                robot.stop()
                return RunReport(
                    False, len(waypoints_world), follower.index,
                    elapsed, robot.pose(), aborted=True,
                )
            if should_stop is not None and should_stop():
                log.info("Stop solicitat de utilizator.")
                robot.stop()
                return RunReport(
                    False, len(waypoints_world), follower.index,
                    elapsed, robot.pose(), aborted=True,
                )

            x, y, yaw = robot.pose()
            v_l, v_r = follower.step(x, y, yaw)
            robot.set_velocity(v_l, v_r)

            if on_progress is not None and (now - last_progress) >= 0.5:
                on_progress(follower.index, len(waypoints_world), (x, y, yaw))
                last_progress = now

            time.sleep(dt)

        robot.stop()
        elapsed = time.perf_counter() - t_start
        log.info("Traseu finalizat: %d/%d waypoints in %.2fs",
                 follower.index, len(waypoints_world), elapsed)
        return RunReport(True, len(waypoints_world), follower.index,
                         elapsed, robot.pose())

    except Exception:
        robot.stop()
        raise
