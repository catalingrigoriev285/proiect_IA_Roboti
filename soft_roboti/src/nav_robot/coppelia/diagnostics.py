"""Probe-uri de diagnostic pentru conexiunea CoppeliaSim si robotul Pioneer.

Folosite din DebugTab pentru a izola cauza problemei "robotul nu se misca":
    1. probe_sim_info        - versiune CoppeliaSim, stare simulare
    2. probe_robot_hierarchy - lista de obiecte din ierarhia robotului + scripturi gasite
    3. test_motor_raw        - bypass disable scripts: setJointTargetVelocity + masoara deplasarea
    4. test_disable_methods  - incearca fiecare metoda de disable script, raporteaza ce a mers
    5. emergency_stop        - opreste robotul (v_l = v_r = 0)
"""

from __future__ import annotations

import logging
import time
from typing import Any

log = logging.getLogger("coppelia.diag")


# Numele starilor de simulare (pentru afisaj usor)
_SIM_STATE_NAMES = {
    0: "stopped",
    8: "paused",
    16: "advancing_lastbeforestop",
    17: "advancing_running",
    18: "advancing_lastbeforepause",
    20: "advancing_firstafterstop",
    21: "advancing_lastbeforepause",
    22: "advancing_firstafterpause",
}


def probe_sim_info(sim) -> dict:
    """Returneaza informatii de baza despre conexiune si starea simularii."""
    info: dict[str, Any] = {}

    for name, attr in [("version", "intparam_program_version"),
                        ("compilation_version", "intparam_compilation_version")]:
        try:
            pid = getattr(sim, attr)
            info[name] = sim.getInt32Param(pid)
        except Exception as e:
            info[f"{name}_err"] = str(e)

    try:
        state = sim.getSimulationState()
        info["sim_state"] = state
        info["sim_state_name"] = _SIM_STATE_NAMES.get(state, f"unknown({state})")
    except Exception as e:
        info["sim_state_err"] = str(e)

    # Cateva atribute API-related (sa vedem ce nume exista)
    apis_present = []
    for attr in ("setBoolProperty", "getBoolProperty", "removeScript",
                 "getScript", "setScriptInt32Param",
                 "scripttype_simulation", "scripttype_simulationscript",
                 "scripttype_childscript", "scripttype_customizationscript"):
        if hasattr(sim, attr):
            apis_present.append(attr)
    info["apis_present"] = apis_present

    return info


def probe_robot_hierarchy(sim, base_path: str = "/PioneerP3DX") -> dict:
    """Listeaza ierarhia robotului si scripturile gasite pe fiecare obiect.

    Returneaza: {robot_handle, hierarchy: [...], scripts: [...]}
    """
    info: dict[str, Any] = {"base_path": base_path}

    try:
        robot_h = sim.getObject(base_path)
        info["robot_handle"] = robot_h
    except Exception as e:
        info["error"] = f"sim.getObject({base_path!r}) esuat: {e}"
        return info

    # Walk hierarchy (DFS)
    hierarchy: list[dict] = []

    def _walk(h: int, depth: int) -> None:
        try:
            alias = sim.getObjectAlias(h)
        except Exception:
            alias = "?"
        try:
            type_str = sim.getObjectTypeName(h) if hasattr(sim, "getObjectTypeName") else ""
        except Exception:
            type_str = ""
        hierarchy.append({"handle": h, "depth": depth,
                          "alias": alias, "type": type_str})
        i = 0
        while True:
            try:
                child = sim.getObjectChild(h, i)
            except Exception:
                break
            if child == -1:
                break
            _walk(child, depth + 1)
            i += 1

    _walk(robot_h, 0)
    info["hierarchy"] = hierarchy

    # Tipuri de script cunoscute
    script_types: list[tuple[str, int]] = []
    for name in ("scripttype_simulation", "scripttype_simulationscript",
                 "scripttype_childscript", "scripttype_customizationscript",
                 "scripttype_mainscript"):
        v = getattr(sim, name, None)
        if isinstance(v, int):
            script_types.append((name, v))
    info["script_types_probed"] = [n for n, _ in script_types]

    # Cauta scripturi pe fiecare obiect
    scripts: list[dict] = []
    seen_handles: set[int] = set()
    for node in hierarchy:
        h = node["handle"]
        for name, stype in script_types:
            try:
                sh = sim.getScript(stype, h)
            except Exception:
                continue
            if sh is None or sh == -1 or sh in seen_handles:
                continue
            seen_handles.add(sh)
            rec: dict[str, Any] = {
                "on_obj": h, "on_alias": node["alias"],
                "script_handle": sh, "script_type": name,
            }
            # Incearca sa citeasca property "enabled"
            for prop_name in ("enabled", "scriptEnabled", "scriptState"):
                try:
                    rec[f"prop_{prop_name}"] = sim.getBoolProperty(sh, prop_name)
                    break
                except Exception as e:
                    rec[f"prop_{prop_name}_err"] = str(e)[:80]
            scripts.append(rec)
    info["scripts"] = scripts
    info["scripts_count"] = len(scripts)

    return info


def test_motor_raw(sim, base_path: str = "/PioneerP3DX",
                    duration_s: float = 3.0, vel_rad_s: float = 2.0,
                    force_start: bool = True) -> dict:
    """Trimite setJointTargetVelocity FARA disable-scripts, masoara deplasarea.

    Daca delta_m ~ 0:
      - daca sim_state != 17 (advancing_running) => sim nu ruleaza, comenzi no-op
      - daca motor_enabled = 0 => jointul nu e in mod motor
      - daca dynctrlmode != velocity => alt control loop
      - altfel scriptul builtin suprascrie comenzile
    """
    result: dict[str, Any] = {"vel_rad_s": vel_rad_s, "duration_s": duration_s}
    try:
        robot = sim.getObject(base_path)
        left = sim.getObject(f"{base_path}/leftMotor")
        right = sim.getObject(f"{base_path}/rightMotor")
    except Exception as e:
        result["error"] = f"sim.getObject esuat: {e}"
        return result

    # Stare initiala sim
    try:
        s0 = sim.getSimulationState()
        result["sim_state_before"] = s0
        result["sim_state_before_name"] = _SIM_STATE_NAMES.get(s0, f"unknown({s0})")
    except Exception as e:
        result["sim_state_before_err"] = str(e)

    # Daca cerut, asigura ca rulam
    if force_start:
        try:
            if sim.getSimulationState() != getattr(sim, "simulation_advancing_running", 17):
                sim.startSimulation()
                # asteapta pana e running (max 2s)
                deadline = time.perf_counter() + 2.0
                while time.perf_counter() < deadline:
                    if sim.getSimulationState() == getattr(sim, "simulation_advancing_running", 17):
                        break
                    time.sleep(0.05)
        except Exception as e:
            result["start_err"] = str(e)
        try:
            s1 = sim.getSimulationState()
            result["sim_state_after_start"] = s1
            result["sim_state_after_start_name"] = _SIM_STATE_NAMES.get(s1, f"unknown({s1})")
        except Exception:
            pass

    # Inspectie parametri joint (motor enabled, ctrlmode, max force)
    joint_info: dict[str, dict] = {}
    for name, jh in [("left", left), ("right", right)]:
        ji: dict[str, Any] = {"handle": jh}
        for attr in ("jointintparam_motor_enabled", "jointintparam_dynctrlmode",
                     "jointintparam_velocity_lock", "jointintparam_ctrl_enabled"):
            pid = getattr(sim, attr, None)
            if pid is None:
                continue
            try:
                ji[attr] = sim.getObjectInt32Param(jh, pid)
            except Exception as e:
                ji[f"{attr}_err"] = str(e)[:60]
        for attr in ("jointfloatparam_upper_limit", "jointfloatparam_velocity"):
            pid = getattr(sim, attr, None)
            if pid is None:
                continue
            try:
                ji[attr] = sim.getObjectFloatParam(jh, pid)
            except Exception:
                pass
        try:
            ji["current_target_velocity"] = sim.getJointTargetVelocity(jh)
        except Exception:
            pass
        joint_info[name] = ji
    result["joints_before"] = joint_info

    # Pozitie initiala
    try:
        p0 = sim.getObjectPosition(robot, sim.handle_world)
        result["pose_start"] = (round(p0[0], 3), round(p0[1], 3))
    except Exception as e:
        result["pose_start_err"] = str(e)
        return result

    # FORTEAZA explicit motoarele in mod velocity-control
    enable_attr = getattr(sim, "jointintparam_motor_enabled", None)
    ctrl_attr = getattr(sim, "jointintparam_dynctrlmode", None)
    ctrl_val = getattr(sim, "jointdynctrl_velocity", None)
    for jh in (left, right):
        if enable_attr is not None:
            try:
                sim.setObjectInt32Param(jh, enable_attr, 1)
            except Exception:
                pass
        if ctrl_attr is not None and ctrl_val is not None:
            try:
                sim.setObjectInt32Param(jh, ctrl_attr, ctrl_val)
            except Exception:
                pass

    n_writes = 0
    t0 = time.perf_counter()
    last_pose = p0
    samples: list[tuple[float, float, float]] = []
    while time.perf_counter() - t0 < duration_s:
        try:
            sim.setJointTargetVelocity(left, vel_rad_s)
            sim.setJointTargetVelocity(right, vel_rad_s)
            n_writes += 1
        except Exception as e:
            result["set_err"] = str(e)
            break
        try:
            last_pose = sim.getObjectPosition(robot, sim.handle_world)
            samples.append((time.perf_counter() - t0, last_pose[0], last_pose[1]))
        except Exception:
            pass
        time.sleep(0.05)

    # Citeste valoare target finala (sa vedem daca a fost suprascrisa)
    try:
        result["left_target_after"] = sim.getJointTargetVelocity(left)
        result["right_target_after"] = sim.getJointTargetVelocity(right)
    except Exception:
        pass

    # STOP
    try:
        sim.setJointTargetVelocity(left, 0.0)
        sim.setJointTargetVelocity(right, 0.0)
    except Exception:
        pass

    # Stare finala sim
    try:
        s2 = sim.getSimulationState()
        result["sim_state_after"] = s2
        result["sim_state_after_name"] = _SIM_STATE_NAMES.get(s2, f"unknown({s2})")
    except Exception:
        pass

    result["pose_end"] = (round(last_pose[0], 3), round(last_pose[1], 3))
    dx = last_pose[0] - p0[0]
    dy = last_pose[1] - p0[1]
    result["delta_m"] = round((dx * dx + dy * dy) ** 0.5, 4)
    result["n_writes"] = n_writes
    result["moved"] = result["delta_m"] > 0.05
    # Doar primele si ultimele cateva sample-uri pentru a vedea evolutia
    if samples:
        keep = samples[:3] + samples[-3:]
        result["samples_head_tail"] = [
            (round(t, 2), round(x, 3), round(y, 3)) for t, x, y in keep
        ]
    return result


def probe_all_scene_scripts(sim) -> dict:
    """Listeaza TOATE scripturile din scena, nu doar pe ierarhia robotului.

    In CoppeliaSim 4.6+ scripturile pot fi obiecte separate in scene tree.
    Folosim mai multe API-uri pentru a le gasi.
    """
    out: dict[str, Any] = {}

    # Metoda 1: sim.getObjects(sim.handle_scene, sim.object_script_type) - daca exista
    script_type_id = getattr(sim, "object_script_type", None)
    method1: list[dict] = []
    if script_type_id is not None:
        try:
            handles = sim.getObjectsInTree(sim.handle_scene, script_type_id, 0)
            for h in handles:
                rec: dict[str, Any] = {"handle": h}
                try:
                    rec["alias"] = sim.getObjectAlias(h)
                except Exception:
                    pass
                for prop in ("enabled", "scriptEnabled"):
                    try:
                        rec[f"prop_{prop}"] = sim.getBoolProperty(h, prop)
                        break
                    except Exception:
                        pass
                method1.append(rec)
        except Exception as e:
            out["method1_err"] = str(e)
    out["scene_scripts_via_objects"] = method1

    # Metoda 2: itereaza prin toata scena cu getObject('/') si descendenti, caut script tip
    method2: list[dict] = []
    try:
        root_children = []
        i = 0
        while True:
            try:
                ch = sim.getObjectChild(sim.handle_scene if hasattr(sim, "handle_scene") else -1, i)
            except Exception:
                break
            if ch == -1:
                break
            root_children.append(ch)
            i += 1
        out["scene_root_children"] = len(root_children)
    except Exception as e:
        out["scene_root_err"] = str(e)

    # Metoda 3: per obiect din scena, incearca sim.getScript pentru fiecare tip
    method3: list[dict] = []
    try:
        # Listeaza primele 100 obiecte din scena
        all_handles: list[int] = []
        for i in range(200):
            try:
                # Multe versiuni: sim.getObjectsInTree(sim.handle_scene, sim.handle_all)
                pass
            except Exception:
                pass
        # Foloseste sim.getObjects daca exista
        try:
            handles = sim.getObjectsInTree(sim.handle_scene, sim.handle_all, 0)
            all_handles = list(handles)
        except Exception:
            all_handles = []
        out["scene_total_objects"] = len(all_handles)

        script_types: list[tuple[str, int]] = []
        for name in ("scripttype_simulation", "scripttype_childscript",
                     "scripttype_customizationscript"):
            v = getattr(sim, name, None)
            if isinstance(v, int):
                script_types.append((name, v))

        seen: set[int] = set()
        for h in all_handles:
            try:
                alias = sim.getObjectAlias(h)
            except Exception:
                alias = "?"
            for type_name, stype in script_types:
                try:
                    sh = sim.getScript(stype, h)
                except Exception:
                    continue
                if sh is None or sh == -1 or sh in seen:
                    continue
                seen.add(sh)
                rec = {"obj_handle": h, "obj_alias": alias,
                       "script_handle": sh, "script_type": type_name}
                # Verifica enabled
                for prop in ("enabled", "scriptEnabled"):
                    try:
                        rec[f"prop_{prop}"] = sim.getBoolProperty(sh, prop)
                        break
                    except Exception:
                        pass
                method3.append(rec)
        out["scene_scripts_via_getScript"] = method3
    except Exception as e:
        out["method3_err"] = str(e)

    return out


def test_disable_methods(sim, base_path: str = "/PioneerP3DX") -> dict:
    """Pentru fiecare script gasit pe ierarhie, incearca TOATE metodele de disable
    si raporteaza care a mers (cu verificare prin getBoolProperty).
    """
    out: dict[str, Any] = {"results": []}

    try:
        robot = sim.getObject(base_path)
    except Exception as e:
        out["error"] = str(e)
        return out

    # Adaug handle-urile robotului si descendentilor
    handles = [robot]
    i = 0
    while True:
        try:
            ch = sim.getObjectChild(robot, i)
        except Exception:
            break
        if ch == -1:
            break
        handles.append(ch)
        i += 1

    script_types: list[tuple[str, int]] = []
    for name in ("scripttype_simulation", "scripttype_simulationscript",
                 "scripttype_childscript", "scripttype_customizationscript"):
        v = getattr(sim, name, None)
        if isinstance(v, int):
            script_types.append((name, v))

    seen: set[int] = set()
    for h in handles:
        for type_name, stype in script_types:
            try:
                sh = sim.getScript(stype, h)
            except Exception:
                continue
            if sh is None or sh == -1 or sh in seen:
                continue
            seen.add(sh)
            rec = {"obj_handle": h, "script_handle": sh,
                   "script_type": type_name, "attempts": []}

            # 1. setBoolProperty + verify
            for prop in ("enabled", "scriptEnabled"):
                attempt: dict[str, Any] = {"method": f"setBoolProperty({prop}, False)"}
                try:
                    sim.setBoolProperty(sh, prop, False)
                    attempt["set_ok"] = True
                    try:
                        v = sim.getBoolProperty(sh, prop)
                        attempt["verified"] = (v is False)
                        attempt["value_after"] = v
                    except Exception as e:
                        attempt["verify_err"] = str(e)[:80]
                except Exception as e:
                    attempt["set_err"] = str(e)[:80]
                rec["attempts"].append(attempt)

            # 2. removeScript
            attempt = {"method": "removeScript"}
            try:
                sim.removeScript(sh)
                attempt["set_ok"] = True
            except Exception as e:
                attempt["set_err"] = str(e)[:80]
            rec["attempts"].append(attempt)

            # 3. setScriptInt32Param (legacy)
            attempt = {"method": "setScriptInt32Param(scriptintparam_enabled, 0)"}
            try:
                sim.setScriptInt32Param(sh, sim.scriptintparam_enabled, 0)
                attempt["set_ok"] = True
            except Exception as e:
                attempt["set_err"] = str(e)[:80]
            rec["attempts"].append(attempt)

            out["results"].append(rec)

    return out


def emergency_stop(sim, base_path: str = "/PioneerP3DX") -> dict:
    """Set motors to 0. Returneaza {ok: bool, err: str?}."""
    try:
        left = sim.getObject(f"{base_path}/leftMotor")
        right = sim.getObject(f"{base_path}/rightMotor")
        sim.setJointTargetVelocity(left, 0.0)
        sim.setJointTargetVelocity(right, 0.0)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "err": str(e)}


def format_probe(info: dict, title: str) -> str:
    """Pretty-print pentru afisare in QTextEdit."""
    import json
    lines = [f"=== {title} ===",
             json.dumps(info, indent=2, default=str),
             ""]
    return "\n".join(lines)
