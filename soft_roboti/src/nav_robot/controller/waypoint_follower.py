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

    Strategie (imbunatatita pentru a evita blocaje la pereti):
        - Cand eroarea de yaw e MARE (>`rotate_threshold_rad`), robotul se roteste
          IN LOC (v_lin = 0) pana cand directia e corectata. Asta evita situatia
          in care robotul "frecaza" un perete in timp ce incearca sa viraje.
        - Cand eroarea e mica, merge cu viteza nominala si corectie P pe yaw.
        - Look-ahead: daca un waypoint ulterior este mai aproape decat cel curent
          (de exemplu robotul a "taiat coltul" intre celule), avanseaza la el.
        - Cand distanta robot->waypoint < `tolerance_m`, trece la urmatorul.

    Robotul "termina" cand toate waypoint-urile au fost vizitate.
    """

    def __init__(self, waypoints: list[tuple[float, float]],
                 v_lin: float = 0.4, k_omega: float = 2.5,
                 tolerance_m: float = 0.15,
                 rotate_threshold_rad: float = 0.5,
                 v_max_rad: float = ROBOT_MAX_VELOCITY,
                 lookahead: int = 3) -> None:
        self.waypoints = list(waypoints)
        self.v_lin = v_lin
        self.k_omega = k_omega
        self.tolerance_m = tolerance_m
        self.rotate_threshold_rad = rotate_threshold_rad
        self.v_max_rad = v_max_rad
        self.lookahead = max(1, lookahead)
        self.index = 0

    def is_done(self) -> bool:
        return self.index >= len(self.waypoints)

    def current_target(self) -> tuple[float, float] | None:
        return None if self.is_done() else self.waypoints[self.index]

    def advance(self) -> None:
        """Forteaza saltul la urmatorul waypoint (folosit la recovery din stuck)."""
        self.index += 1

    def step(self, x: float, y: float, yaw: float) -> tuple[float, float]:
        """Returneaza (v_left, v_right) in rad/s pentru iteratia curenta."""
        # Skip waypoints atinse
        while not self.is_done():
            wx, wy = self.waypoints[self.index]
            if math.hypot(wx - x, wy - y) < self.tolerance_m:
                self.index += 1
            else:
                break

        if self.is_done():
            return 0.0, 0.0

        # Look-ahead: daca un waypoint din fereastra urmatoare e mai aproape decat
        # cel curent, sarim direct la el (robotul a "taiat" curbe).
        best_i = self.index
        best_d = math.hypot(self.waypoints[best_i][0] - x,
                            self.waypoints[best_i][1] - y)
        upper = min(self.index + self.lookahead, len(self.waypoints))
        for i in range(self.index + 1, upper):
            wx, wy = self.waypoints[i]
            d = math.hypot(wx - x, wy - y)
            # Acceptam doar daca e semnificativ mai aproape (evita oscilatii).
            if d + 0.05 < best_d:
                best_i = i
                best_d = d
        if best_i != self.index:
            self.index = best_i

        wx, wy = self.waypoints[self.index]
        dx, dy = wx - x, wy - y
        desired_yaw = math.atan2(dy, dx)
        err = wrap_to_pi(desired_yaw - yaw)
        abs_err = abs(err)

        if abs_err > self.rotate_threshold_rad:
            # Rotire pura in loc - mai sigur la viraje stranse / langa pereti
            v_lin = 0.0
            # Foloseste un gain mai mare pentru rotire rapida, dar limitat
            omega = math.copysign(min(2.5, self.k_omega * abs_err * 1.2), err)
        else:
            # Mers normal, viteza redusa proportional cu err (dar nu pana la 0)
            slowdown = max(0.3, math.cos(err))
            v_lin = self.v_lin * slowdown
            omega = self.k_omega * err

        v_l, v_r = cmd_to_wheels(v_lin, omega)
        return clamp_wheels(v_l, v_r, self.v_max_rad)
