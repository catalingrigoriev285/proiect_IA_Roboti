"""WaypointFollower - urmareste o lista de waypoint-uri (faza 3 - stub)."""

from __future__ import annotations


class WaypointFollower:
    """Conduce robotul printr-o lista de waypoint-uri in coordonate world.

    Strategie: viteza liniara constanta + P-controller pe diferenta de unghi
    intre orientarea curenta si directia catre waypoint-ul tinta. La distanta
    < tolerance fata de waypoint, trecem la urmatorul.
    """

    def __init__(self, waypoints: list[tuple[float, float]],
                 v_lin: float = 0.3, k_omega: float = 2.0,
                 tolerance_m: float = 0.15) -> None:
        self.waypoints = waypoints
        self.v_lin = v_lin
        self.k_omega = k_omega
        self.tolerance_m = tolerance_m
        self.index = 0

    def is_done(self) -> bool:
        return self.index >= len(self.waypoints)

    def step(self, x: float, y: float, yaw: float) -> tuple[float, float]:
        """Returneaza (v_left, v_right) pentru iteratia curenta.

        Args:
            x, y: pozitia curenta a robotului (m, world).
            yaw: orientarea curenta (rad, world).
        """
        raise NotImplementedError(
            "WaypointFollower.step - TODO faza 3: calcul dx, dy, distanta, atan2 -> "
            "delta_yaw normalizat, P-controller pe omega, transformare in v_left/v_right."
        )
