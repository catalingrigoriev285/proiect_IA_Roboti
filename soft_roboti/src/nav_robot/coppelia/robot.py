"""Wrapper pentru robotul Pioneer P3-DX in CoppeliaSim."""

from __future__ import annotations

from nav_robot.config import SENSOR_COUNT


class PioneerP3DX:
    """Incapsulare handle-uri si comenzi de baza pentru Pioneer P3-DX.

    Asteapta o conexiune sim activa (obtinuta din `nav_robot.coppelia.client.connect`).
    Atribute populate de constructor:
        robot, left_motor, right_motor: handle-uri obiecte (int).
        sensors: lista de 16 handle-uri de senzori ultrasonici.
    """

    def __init__(self, sim, base_path: str = "/PioneerP3DX") -> None:
        self.sim = sim
        self.base_path = base_path
        self.robot: int = sim.getObject(base_path)
        self.left_motor: int = sim.getObject(f"{base_path}/leftMotor")
        self.right_motor: int = sim.getObject(f"{base_path}/rightMotor")
        self.sensors: list[int] = [
            sim.getObject(f"{base_path}/ultrasonicSensor[{i}]")
            for i in range(SENSOR_COUNT)
        ]

    # ------------------------------------------------------------------
    # Motoare
    # ------------------------------------------------------------------
    def set_velocity(self, v_left: float, v_right: float) -> None:
        """Seteaza vitezele tinta (rad/s) pentru cele doua motoare."""
        self.sim.setJointTargetVelocity(self.left_motor, float(v_left))
        self.sim.setJointTargetVelocity(self.right_motor, float(v_right))

    def stop(self) -> None:
        """Opreste robotul (v_left = v_right = 0)."""
        self.set_velocity(0.0, 0.0)

    # ------------------------------------------------------------------
    # Pozitie / orientare in lumea CoppeliaSim
    # ------------------------------------------------------------------
    def position(self) -> tuple[float, float, float]:
        """Pozitia (x, y, z) in coordonate world (metri)."""
        x, y, z = self.sim.getObjectPosition(self.robot, self.sim.handle_world)
        return float(x), float(y), float(z)

    def orientation(self) -> float:
        """Yaw-ul robotului (rad) in jurul axei Z (world)."""
        _, _, gamma = self.sim.getObjectOrientation(self.robot, self.sim.handle_world)
        return float(gamma)

    def pose(self) -> tuple[float, float, float]:
        """Returneaza (x, y, yaw) - pose 2D."""
        x, y, _ = self.position()
        return x, y, self.orientation()
