"""Algoritm Bug2 - navigare reactiva spre tinta cunoscuta.

Conceptual:
    1. m-line: linia dreapta start -> goal.
    2. Robotul merge spre goal (GO_TO_GOAL).
    3. Cand intalneste un obstacol, marcheaza hit_point si trece in FOLLOW_WALL
       (urmareste peretele in sens fix).
    4. Cand robotul ajunge din nou pe m-line si este mai aproape de goal decat
       hit_point-ul, revine la GO_TO_GOAL.
    5. Iesirea: ajuns la goal sau aborteaza (timeout).

Limitari:
    Bug2 garanteaza atingerea goal-ului doar daca exista un drum si peretele
    nu formeaza un labirint patologic; in caz contrar poate oscila.
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from nav_robot.config import (
    ROBOT_BASE_VELOCITY, ROBOT_MAX_VELOCITY, SENSOR_MAX_RANGE,
)
from nav_robot.controller.differential_drive import clamp_wheels, cmd_to_wheels
from nav_robot.controller.waypoint_follower import wrap_to_pi
from nav_robot.coppelia.sensors import min_distance, read_all_sensors
from nav_robot.reactive.wall_following import (
    FRONT_SENSORS, RIGHT_SENSORS, wall_follow_step,
)

log = logging.getLogger("reactive.bug2")


class _State(Enum):
    GO_TO_GOAL = "GO_TO_GOAL"
    FOLLOW_WALL = "FOLLOW_WALL"


@dataclass
class Bug2Report:
    """Rezultatul rularii Bug2."""
    success: bool
    elapsed_s: float
    steps: int
    final_pose: tuple[float, float, float]
    final_distance_to_goal: float
    aborted: bool = False
    state_history: list[str] = field(default_factory=list)


def _distance_to_m_line(x: float, y: float,
                        sx: float, sy: float,
                        gx: float, gy: float) -> float:
    """Distanta punctului (x, y) la dreapta start->goal."""
    dx, dy = gx - sx, gy - sy
    norm = math.hypot(dx, dy)
    if norm < 1e-9:
        return math.hypot(x - sx, y - sy)
    return abs(dy * x - dx * y + gx * sy - gy * sx) / norm


def bug2_navigate(
    sim,
    robot,
    goal_world: tuple[float, float],
    front_stop: float = 0.5,
    goal_tolerance: float = 0.3,
    m_line_tolerance: float = 0.2,
    v_base: float = ROBOT_BASE_VELOCITY,
    k_omega: float = 2.5,
    timeout_s: float = 90.0,
    rate_hz: float = 20.0,
    should_stop: Callable[[], bool] | None = None,
    on_progress: Callable[[str, tuple[float, float, float], float], None] | None = None,
) -> Bug2Report:
    """Conduce robotul (instanta PioneerP3DX) catre goal_world folosind algoritmul Bug2.

    Args:
        sim: API CoppeliaSim.
        robot: instanta PioneerP3DX (vezi nav_robot.coppelia.robot).
        goal_world: (gx, gy) coordonate world in metri.
        front_stop: distanta sub care comutam la FOLLOW_WALL.
        goal_tolerance: distanta sub care consideram tinta atinsa.
        m_line_tolerance: cat de aproape de m-line trebuie sa fim pentru a o
                         considera reintersectata.
        v_base: viteza nominala (rad/s).
        k_omega: gain P pe yaw error (pentru GO_TO_GOAL).
        timeout_s: limita maxima de timp.
        rate_hz: frecventa buclei de control.
        should_stop: callable optional verificat la fiecare pas.
        on_progress: callback (state_str, (x,y,yaw), dist_to_goal) la fiecare ~0.5s.
    """
    gx, gy = goal_world
    sx, sy, _ = robot.pose()  # start = pozitia curenta

    state = _State.GO_TO_GOAL
    hit_point: tuple[float, float] | None = None
    hit_dist_to_goal: float | None = None
    dt = 1.0 / rate_hz
    t_start = time.perf_counter()
    last_progress = t_start
    history: list[str] = []
    steps = 0

    try:
        while True:
            now = time.perf_counter()
            elapsed = now - t_start
            x, y, yaw = robot.pose()
            d_goal = math.hypot(gx - x, gy - y)

            if d_goal < goal_tolerance:
                robot.stop()
                log.info("Goal atins in %.2fs (steps=%d).", elapsed, steps)
                return Bug2Report(True, elapsed, steps, (x, y, yaw), d_goal,
                                  state_history=history)
            if elapsed > timeout_s:
                robot.stop()
                log.warning("Timeout Bug2 dupa %.1fs.", timeout_s)
                return Bug2Report(False, elapsed, steps, (x, y, yaw), d_goal,
                                  aborted=True, state_history=history)
            if should_stop is not None and should_stop():
                robot.stop()
                log.info("Stop solicitat de utilizator.")
                return Bug2Report(False, elapsed, steps, (x, y, yaw), d_goal,
                                  aborted=True, state_history=history)

            readings = read_all_sensors(sim, robot.sensors)
            d_front = min_distance(readings, FRONT_SENSORS)
            d_right = min_distance(readings, RIGHT_SENSORS)

            # --- Tranzitii ---
            if state == _State.GO_TO_GOAL and d_front < front_stop:
                hit_point = (x, y)
                hit_dist_to_goal = d_goal
                state = _State.FOLLOW_WALL
                log.info("HIT obstacle la (%.2f, %.2f), comut la FOLLOW_WALL.", x, y)

            elif state == _State.FOLLOW_WALL and hit_point is not None:
                # Reintersectie m-line + mai aproape de goal => GO_TO_GOAL
                d_mline = _distance_to_m_line(x, y, sx, sy, gx, gy)
                # Iesim doar dupa ce ne-am indepartat suficient de hit_point
                # (evita comutarea imediata in acelasi loc)
                far_from_hit = math.hypot(x - hit_point[0], y - hit_point[1]) > 0.4
                if (d_mline < m_line_tolerance and
                        d_goal < (hit_dist_to_goal or float("inf")) - 0.05 and
                        far_from_hit):
                    state = _State.GO_TO_GOAL
                    log.info("Reintersectare m-line, comut la GO_TO_GOAL.")

            # --- Comportament per stare ---
            if state == _State.GO_TO_GOAL:
                desired_yaw = math.atan2(gy - y, gx - x)
                err = wrap_to_pi(desired_yaw - yaw)
                # Reduce viteza la viraje mari
                v_lin = 0.4 * math.exp(-2.0 * abs(err))
                omega = k_omega * err
                v_l, v_r = cmd_to_wheels(v_lin, omega)
                v_l, v_r = clamp_wheels(v_l, v_r, ROBOT_MAX_VELOCITY)
            else:
                v_l, v_r, _ = wall_follow_step(d_right, d_front, v_base=v_base,
                                               front_stop=front_stop * 0.8,
                                               sensor_max=SENSOR_MAX_RANGE)

            robot.set_velocity(v_l, v_r)

            history.append(state.value)
            steps += 1

            if on_progress is not None and (now - last_progress) >= 0.5:
                on_progress(state.value, (x, y, yaw), d_goal)
                last_progress = now

            time.sleep(dt)

    except Exception:
        robot.stop()
        raise
