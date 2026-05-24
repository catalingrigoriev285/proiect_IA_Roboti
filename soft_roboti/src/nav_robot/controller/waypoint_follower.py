"""WaypointFollower - urmareste o lista de waypoint-uri (Faza 3)."""

from __future__ import annotations

import math

from nav_robot.config import ROBOT_MAX_VELOCITY
from nav_robot.controller.differential_drive import clamp_wheels, cmd_to_wheels


def wrap_to_pi(angle: float) -> float:
    """Normalizeaza un unghi la intervalul [-pi, pi]."""
    return math.atan2(math.sin(angle), math.cos(angle))


class WaypointFollower:
    """Conduce robotul printr-o lista de waypoint-uri in coordonate world (metri).

    Strategie:
        - viteza liniara constanta `v_lin` cand robotul priveste catre waypoint,
          redusa exponential la viraje mari (`exp(-2*|err|)`);
        - P-controller pe diferenta de unghi (yaw error) -> omega;
        - cand distanta robot->waypoint < `tolerance_m`, trece la urmatorul.

    Robotul "termina" cand toate waypoint-urile au fost vizitate.
    """

    def __init__(self, waypoints: list[tuple[float, float]],
                 v_lin: float = 0.4, k_omega: float = 2.5,
                 tolerance_m: float = 0.15,
                 v_max_rad: float = ROBOT_MAX_VELOCITY) -> None:
        self.waypoints = list(waypoints)
        self.v_lin = v_lin
        self.k_omega = k_omega
        self.tolerance_m = tolerance_m
        self.v_max_rad = v_max_rad
        self.index = 0

    def is_done(self) -> bool:
        return self.index >= len(self.waypoints)

    def current_target(self) -> tuple[float, float] | None:
        return None if self.is_done() else self.waypoints[self.index]

    def step(self, x: float, y: float, yaw: float) -> tuple[float, float]:
        """Returneaza (v_left, v_right) in rad/s pentru iteratia curenta.

        Daca ne aflam la o distanta < tolerance fata de waypoint-ul curent,
        avansam la urmatorul (eventual mai multe consecutive daca toate sunt apropiate).
        """
        # Skip waypoints aflate deja in tolerance
        while not self.is_done():
            wx, wy = self.waypoints[self.index]
            if math.hypot(wx - x, wy - y) < self.tolerance_m:
                self.index += 1
            else:
                break

        if self.is_done():
            return 0.0, 0.0

        wx, wy = self.waypoints[self.index]
        dx, dy = wx - x, wy - y
        desired_yaw = math.atan2(dy, dx)
        err = wrap_to_pi(desired_yaw - yaw)

        # Incetinim viteza liniara cand virajul e mare (ca sa nu derapeze)
        v_lin = self.v_lin * math.exp(-2.0 * abs(err))
        omega = self.k_omega * err

        v_l, v_r = cmd_to_wheels(v_lin, omega)
        return clamp_wheels(v_l, v_r, self.v_max_rad)
