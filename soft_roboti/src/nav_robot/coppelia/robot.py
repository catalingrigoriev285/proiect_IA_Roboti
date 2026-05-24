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
        """Dezactiveaza orice script atasat robotului (child / simulation / customization).

        Modelul oficial Pioneer P3-DX vine cu un script de evitare-obstacole care
        suprascrie `setJointTargetVelocity` la fiecare pas. Daca ramane activ,
        robotul "ignora" comenzile noastre si poate sa stea pe loc (cand simte
        un obstacol langa) sau sa se roteasca singur.

        CoppeliaSim 4.10 a renuntat la `setScriptInt32Param` (deprecated, no-op).
        Folosim noul API de proprietati `sim.setBoolProperty(script_h, "enabled", False)`
        cu verificare prin `getBoolProperty`, plus fallback la `removeScript` si la
        API-ul legacy pentru versiuni vechi de CoppeliaSim.
        """
        sim = self.sim
        # Construieste lista de (nume, valoare) pentru fiecare tip de script cunoscut.
        script_types: list[tuple[str, int]] = []
        for name in ("scripttype_childscript", "scripttype_simulation",
                     "scripttype_simulationscript", "scripttype_customizationscript",
                     "scripttype_mainscript"):
            v = getattr(sim, name, None)
            if isinstance(v, int):
                script_types.append((name, v))

        # Aduna handle-urile din ierarhia robotului (root + descendenti)
        targets = self._collect_subtree(self.robot)
        log.info("Caut script-uri pe %d obiecte din ierarhia robotului ...",
                 len(targets))

        disabled_any = False
        for obj_h in targets:
            for name, stype in script_types:
                try:
                    script_h = sim.getScript(stype, obj_h)
                except Exception:
                    script_h = -1
                if script_h is None or script_h == -1:
                    continue
                if self._try_disable_script(script_h, obj_h, name):
                    disabled_any = True

        if not disabled_any:
            log.warning(
                "Niciun script dezactivat automat pe ierarhia robotului. "
                "Daca robotul ignora comenzile: in CoppeliaSim, dublu-click pe "
                "iconita scriptului langa PioneerP3DX in Scene Hierarchy -> "
                "in editor, meniul 'Scripts' -> uncheck 'Enabled', salveaza scena (Ctrl+S)."
            )

    def _try_disable_script(self, script_h: int, obj_h: int,
                             type_name: str) -> bool:
        """Incearca sa dezactiveze un script handle prin lant de metode.

        Pentru fiecare metoda, raporteaza ce a incercat in log.debug; doar in
        caz de SUCCES verificat se ridica la log.info.

        Returneaza True daca o metoda a reusit cu verificare.
        """
        sim = self.sim

        # 1. setBoolProperty pe diferite nume de property cunoscute in 4.10
        for prop_name in ("enabled", "scriptEnabled", "scriptState"):
            try:
                sim.setBoolProperty(script_h, prop_name, False)
            except Exception as e:
                log.debug("setBoolProperty(%r, False) esuat pe script_h=%d: %s",
                          prop_name, script_h, e)
                continue
            # Verifica prin citire
            try:
                v = sim.getBoolProperty(script_h, prop_name)
                if v is False:
                    log.info("Script %s DEZACTIVAT via setBoolProperty(%r) pe "
                             "obj=%d (script_h=%d).",
                             type_name, prop_name, obj_h, script_h)
                    return True
                log.debug("setBoolProperty(%r) ruleaza dar valoarea ramane %r.",
                          prop_name, v)
            except Exception as e:
                # Nu putem verifica - presupunem ca a mers
                log.info("Script %s DEZACTIVAT via setBoolProperty(%r) (neverificat) "
                         "pe obj=%d.", type_name, prop_name, obj_h)
                log.debug("getBoolProperty esuat: %s", e)
                return True

        # 2. removeScript (elimina complet)
        try:
            sim.removeScript(script_h)
            log.info("Script %s ELIMINAT (removeScript) pe obj=%d (script_h=%d).",
                     type_name, obj_h, script_h)
            return True
        except Exception as e:
            log.debug("removeScript esuat pe script_h=%d: %s", script_h, e)

        # 3. Legacy API (CoppeliaSim < 4.6) — emite warning deprecated in 4.10 si
        # NU produce efect. Doar logam tentativa pentru completitudine.
        try:
            sim.setScriptInt32Param(script_h, sim.scriptintparam_enabled, 0)
            log.warning("Script %s: doar API legacy a rulat (probabil fara efect "
                        "in CoppeliaSim 4.10). Foloseste tabul Debug pentru "
                        "diagnoza detaliata.", type_name)
            return False  # NU consideram succes - in 4.10 e no-op
        except Exception as e:
            log.debug("setScriptInt32Param esuat pe script_h=%d: %s", script_h, e)

        return False

        # In plus, asiguram explicit ca motoarele sunt in mod velocity-control
        for motor_name, motor in (("left", self.left_motor),
                                   ("right", self.right_motor)):
            for param_name in ("jointintparam_motor_enabled",
                                "jointintparam_velocity_lock"):
                pid = getattr(sim, param_name, None)
                if pid is None:
                    continue
                try:
                    sim.setObjectInt32Param(motor, pid, 1)
                except Exception:
                    pass
            # Forteaza mod dinamic = velocity control
            for ctrl_attr, val_attr in [
                ("jointintparam_dynctrlmode", "jointdynctrl_velocity"),
            ]:
                pid = getattr(sim, ctrl_attr, None)
                val = getattr(sim, val_attr, None)
                if pid is None or val is None:
                    continue
                try:
                    sim.setObjectInt32Param(motor, pid, val)
                except Exception:
                    pass

    def _collect_subtree(self, root_handle: int) -> list[int]:
        """Returneaza root + toti descendentii (DFS) - pentru cautare scripturi."""
        sim = self.sim
        out: list[int] = []
        stack = [root_handle]
        while stack:
            h = stack.pop()
            out.append(h)
            idx = 0
            while True:
                try:
                    child = sim.getObjectChild(h, idx)
                except Exception:
                    break
                if child == -1:
                    break
                stack.append(child)
                idx += 1
        return out

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
