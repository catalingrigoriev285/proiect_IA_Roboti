"""Wrapper pentru robotul Pioneer P3-DX in CoppeliaSim."""

from __future__ import annotations

import logging

from nav_robot.config import SENSOR_COUNT

log = logging.getLogger("coppelia.robot")


class PioneerP3DX:
    """Incapsulare handle-uri si comenzi de baza pentru Pioneer P3-DX.

    Asteapta o conexiune sim activa (obtinuta din `nav_robot.coppelia.client.connect`).
    Atribute populate de constructor:
        robot, left_motor, right_motor: handle-uri obiecte (int).
        sensors: lista de 16 handle-uri de senzori ultrasonici.

    IMPORTANT: modelul oficial Pioneer P3-DX din CoppeliaSim contine un child script
    care evita-obstacole care suprascrie `setJointTargetVelocity` la fiecare frame.
    Pentru a putea comanda robotul din Python, dezactivam acel script la init.
    """

    def __init__(self, sim, base_path: str = "/PioneerP3DX",
                 disable_child_script: bool = True) -> None:
        self.sim = sim
        self.base_path = base_path
        self.robot: int = sim.getObject(base_path)
        self.left_motor: int = sim.getObject(f"{base_path}/leftMotor")
        self.right_motor: int = sim.getObject(f"{base_path}/rightMotor")
        self.sensors: list[int] = [
            sim.getObject(f"{base_path}/ultrasonicSensor[{i}]")
            for i in range(SENSOR_COUNT)
        ]
        if disable_child_script:
            self._disable_builtin_scripts()

    def _disable_builtin_scripts(self) -> None:
        """Dezactiveaza child script-ul builtin (evita-obstacole) al modelului Pioneer.

        Daca scriptul ramane activ, va suprascrie comenzile noastre la fiecare pas
        de simulare si robotul fie nu se misca dupa planul nostru, fie are
        comportament neasteptat (rotire, oprire la perete).
        """
        sim = self.sim
        # Incercam toate tipurile de script atasate robotului (child + customization)
        for script_type_attr in ("scripttype_simulation", "scripttype_childscript",
                                  "scripttype_customizationscript"):
            stype = getattr(sim, script_type_attr, None)
            if stype is None:
                continue
            try:
                script_handle = sim.getScript(stype, self.robot)
            except Exception:
                continue
            if script_handle is None or script_handle == -1:
                continue
            try:
                sim.setScriptInt32Param(script_handle,
                                        sim.scriptintparam_enabled, 0)
                log.info("Dezactivat script %s pe %s (handle=%d).",
                         script_type_attr, self.base_path, script_handle)
            except Exception as e:
                log.debug("Nu am putut dezactiva %s: %s", script_type_attr, e)

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
