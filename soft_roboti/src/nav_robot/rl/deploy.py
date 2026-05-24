"""Executa o politica RL pe robotul Pioneer P3-DX in CoppeliaSim.

Strategie:
    1. La fiecare pas: ia celula curenta a robotului (din pozitia world).
    2. Cere actiunea politicii pentru celula respectiva.
    3. Calculeaza celula vecina (target).
    4. Foloseste WaypointFollower (din Faza 3) pentru a ajunge fizic acolo.
    5. Repeta pana la goal sau timeout / coliziune detectata.
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass
from typing import Callable

from nav_robot.coppelia.robot import PioneerP3DX
from nav_robot.controller.waypoint_follower import WaypointFollower
from nav_robot.map.grid_map import Cell, GridMap
from nav_robot.rl.env import ACTIONS_4, ACTIONS_8
from nav_robot.rl.policy import Policy

log = logging.getLogger("rl.deploy")


@dataclass
class DeployReport:
    success: bool
    elapsed_s: float
    cells_visited: int
    final_cell: Cell
    aborted: bool = False
    trajectory: list[Cell] | None = None


def run_policy_in_coppelia(
    sim,
    robot: PioneerP3DX,
    grid: GridMap,
    policy: Policy,
    diagonal: bool = False,
    rate_hz: float = 20.0,
    cell_timeout_s: float = 8.0,
    global_timeout_s: float = 120.0,
    max_cells: int = 200,
    should_stop: Callable[[], bool] | None = None,
    on_step: Callable[[Cell, int, Cell], None] | None = None,
) -> DeployReport:
    """Ruleaza o politica deterministica in CoppeliaSim, celula cu celula.

    Args:
        sim: API CoppeliaSim.
        robot: instanta PioneerP3DX.
        grid: harta pentru conversie cell <-> world.
        policy: politica antrenata (returneaza actiune per celula).
        diagonal: foloseste 8 actiuni in loc de 4 (trebuie sa fie compatibil cu politica).
        rate_hz: frecventa buclei interne de control.
        cell_timeout_s: timp maxim pentru a atinge o celula vecina.
        global_timeout_s: timp maxim total.
        max_cells: limita de celule vizitate (safety).
        should_stop: callable -> True pentru a abandona.
        on_step: callback (current_cell, action, next_cell).
    """
    actions = ACTIONS_8 if diagonal else ACTIONS_4
    trajectory: list[Cell] = []
    dt = 1.0 / rate_hz
    t_start = time.perf_counter()

    def current_cell() -> Cell:
        x, y, _ = robot.pose()
        return grid.from_world(x, y)

    try:
        cur = current_cell()
        trajectory.append(cur)
        cells_visited = 0

        while cells_visited < max_cells:
            elapsed_total = time.perf_counter() - t_start
            if elapsed_total > global_timeout_s:
                robot.stop()
                log.warning("Timeout global %.1fs.", global_timeout_s)
                return DeployReport(False, elapsed_total, cells_visited,
                                    cur, aborted=True, trajectory=trajectory)
            if should_stop is not None and should_stop():
                robot.stop()
                return DeployReport(False, elapsed_total, cells_visited,
                                    cur, aborted=True, trajectory=trajectory)

            if cur == grid.goal:
                robot.stop()
                log.info("Goal atins in %.2fs (%d celule vizitate).",
                         elapsed_total, cells_visited)
                return DeployReport(True, elapsed_total, cells_visited,
                                    cur, trajectory=trajectory)

            # Cere actiunea politicii
            a = policy(cur)
            dx, dy = actions[a]
            target_cell: Cell = (cur[0] + dx, cur[1] + dy)

            if not grid.is_free(target_cell):
                log.warning("Politica indica celula invalida %s din %s; abandonez.",
                            target_cell, cur)
                robot.stop()
                return DeployReport(False, elapsed_total, cells_visited,
                                    cur, aborted=True, trajectory=trajectory)

            if on_step is not None:
                on_step(cur, a, target_cell)

            # Urmareste waypoint-ul fizic
            target_world = grid.to_world(target_cell)
            follower = WaypointFollower([target_world], v_lin=0.35, tolerance_m=0.15)
            t_cell = time.perf_counter()
            while not follower.is_done():
                if (time.perf_counter() - t_cell) > cell_timeout_s:
                    log.warning("Celula %s -> %s: cell_timeout (%.1fs).",
                                cur, target_cell, cell_timeout_s)
                    robot.stop()
                    return DeployReport(False, time.perf_counter() - t_start,
                                        cells_visited, cur, aborted=True,
                                        trajectory=trajectory)
                if should_stop is not None and should_stop():
                    robot.stop()
                    return DeployReport(False, time.perf_counter() - t_start,
                                        cells_visited, cur, aborted=True,
                                        trajectory=trajectory)
                x, y, yaw = robot.pose()
                v_l, v_r = follower.step(x, y, yaw)
                robot.set_velocity(v_l, v_r)
                time.sleep(dt)

            robot.stop()
            cur = current_cell()
            trajectory.append(cur)
            cells_visited += 1

        robot.stop()
        log.warning("Max cells (%d) atinsi fara goal.", max_cells)
        return DeployReport(False, time.perf_counter() - t_start, cells_visited,
                            cur, trajectory=trajectory)

    except Exception:
        robot.stop()
        raise
