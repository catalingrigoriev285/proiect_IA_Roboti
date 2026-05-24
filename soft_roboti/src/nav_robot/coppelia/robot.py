"""Wrapper pentru robotul Pioneer P3-DX in CoppeliaSim (faza 3 - stub)."""

from __future__ import annotations


class PioneerP3DX:
    """Incapsulare handle-uri si comenzi de baza pentru Pioneer P3-DX.

    Asteapta o conexiune sim activa (obtinuta din nav_robot.coppelia.client.connect()).

    Atribute (dupa initializare):
        robot, left_motor, right_motor: handle-uri obiecte.
        sensors: lista de 16 handle-uri de senzori ultrasonici.
    """

    def __init__(self, sim, base_path: str = "/PioneerP3DX") -> None:
        self.sim = sim
        self.base_path = base_path
        # Atribute populate de _resolve_handles()
        self.robot: int | None = None
        self.left_motor: int | None = None
        self.right_motor: int | None = None
        self.sensors: list[int] = []
        raise NotImplementedError(
            "PioneerP3DX.__init__ - TODO faza 3: apel _resolve_handles() ce cere "
            "sim.getObject pentru /PioneerP3DX, leftMotor, rightMotor, ultrasonicSensor[0..15]. "
            "(Vezi lab 06 cerinta 3.1.)"
        )

    def set_velocity(self, v_left: float, v_right: float) -> None:
        """Seteaza vitezele tinta (rad/s) pentru motoare."""
        raise NotImplementedError("PioneerP3DX.set_velocity - TODO faza 3.")

    def stop(self) -> None:
        """Opreste robotul (v_left = v_right = 0)."""
        raise NotImplementedError("PioneerP3DX.stop - TODO faza 3: set_velocity(0, 0).")

    def position(self) -> tuple[float, float, float]:
        """Pozitia (x, y, z) in coordonate world."""
        raise NotImplementedError("PioneerP3DX.position - TODO faza 3: sim.getObjectPosition.")

    def orientation(self) -> float:
        """Yaw-ul robotului (rad) in jurul axei Z (world)."""
        raise NotImplementedError("PioneerP3DX.orientation - TODO faza 3: sim.getObjectOrientation[2].")
