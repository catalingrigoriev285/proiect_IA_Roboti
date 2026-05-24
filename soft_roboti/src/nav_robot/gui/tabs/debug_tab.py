"""Tab Debug: verifica de ce robotul nu se misca in CoppeliaSim.

Buton -> probe -> output text. Toate probele ruleaza intr-un worker thread.
"""

from __future__ import annotations

import json
import logging

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame, QGroupBox, QHBoxLayout, QLabel, QMessageBox, QPushButton,
    QScrollArea, QSplitter, QTextEdit, QVBoxLayout, QWidget,
)
from PySide6.QtCore import Qt

from nav_robot.gui.worker import run_async

log = logging.getLogger("gui.debug")


class DebugTab(QWidget):
    """Probe de diagnoza pentru integrarea cu CoppeliaSim."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._thread = None
        self._worker = None
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        left = self._wrap_scroll(self._build_buttons())
        right = self._build_output()
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(left); splitter.addWidget(right)
        splitter.setStretchFactor(0, 0); splitter.setStretchFactor(1, 1)
        splitter.setSizes([320, 800])
        layout = QVBoxLayout(self); layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(splitter)

    def _wrap_scroll(self, widget: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidget(widget); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        return scroll

    def _build_buttons(self) -> QWidget:
        wrap = QFrame()
        v = QVBoxLayout(wrap); v.setContentsMargins(4, 4, 4, 4); v.setSpacing(6)

        intro = QLabel(
            "<b>Probe diagnoza</b><br>"
            "Ruleaza pe rand butoanele de jos pentru a izola cauza "
            "<i>robotul nu se misca</i>."
        )
        intro.setWordWrap(True)
        v.addWidget(intro)

        gb_info = QGroupBox("Informatii generale")
        v_info = QVBoxLayout(gb_info)
        b1 = QPushButton("1. Probe CoppeliaSim (versiune, stare, API-uri)")
        b2 = QPushButton("2. Probe robot (ierarhie + scripturi gasite)")
        b2b = QPushButton("2b. Probe TOATA scena (scripturi globale)")
        b1.clicked.connect(self._probe_sim)
        b2.clicked.connect(self._probe_robot)
        b2b.clicked.connect(self._probe_scene_scripts)
        v_info.addWidget(b1); v_info.addWidget(b2); v_info.addWidget(b2b)

        gb_mot = QGroupBox("Test miscare")
        v_mot = QVBoxLayout(gb_mot)
        b3 = QPushButton("3. Test motor RAW (fara disable scripturi)")
        b3.setToolTip("Trimite setJointTargetVelocity 3s. Daca delta_m < 0.05 si "
                       "scripturile sunt active, scriptul builtin Pioneer ti le suprascrie.")
        b4 = QPushButton("4. Test toate metodele de disable script")
        b4.setToolTip("Pentru fiecare script gasit incearca setBoolProperty / "
                       "removeScript / setScriptInt32Param si raporteaza care a mers.")
        b5 = QPushButton("5. Test miscare DUPA disable scripturi")
        b5.setToolTip("Disable script + test motor. Daca delta_m > 0.05, am rezolvat.")
        b3.clicked.connect(self._test_motor_raw)
        b4.clicked.connect(self._test_disable)
        b5.clicked.connect(self._test_disable_then_move)
        v_mot.addWidget(b3); v_mot.addWidget(b4); v_mot.addWidget(b5)

        gb_act = QGroupBox("Actiuni rapide")
        v_act = QVBoxLayout(gb_act)
        b_stop = QPushButton("STOP motoare (urgenta)")
        b_stop.setStyleSheet("background:#c0392b; color:white; font-weight:bold;")
        b_stop.clicked.connect(self._emergency_stop)
        b_clear = QPushButton("Sterge output")
        b_clear.clicked.connect(lambda: self.output.clear())
        v_act.addWidget(b_stop); v_act.addWidget(b_clear)

        v.addWidget(gb_info); v.addWidget(gb_mot); v.addWidget(gb_act); v.addStretch(1)
        return wrap

    def _build_output(self) -> QWidget:
        wrap = QFrame(); wrap.setFrameShape(QFrame.Shape.StyledPanel)
        v = QVBoxLayout(wrap); v.setContentsMargins(4, 4, 4, 4)
        v.addWidget(QLabel("<b>Rezultate probe (cele mai noi jos)</b>"))
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Consolas", 9))
        self.output.setStyleSheet("background:#1e1e1e; color:#e0e0e0;")
        v.addWidget(self.output, stretch=1)
        return wrap

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _append(self, title: str, payload: dict | str) -> None:
        if isinstance(payload, dict):
            body = json.dumps(payload, indent=2, default=str)
        else:
            body = str(payload)
        sep = "─" * 60
        self.output.append(f"\n{sep}\n=== {title} ===\n{body}\n")
        # Scroll to bottom
        sb = self.output.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _run(self, title: str, task) -> None:
        log.info("Debug: %s ...", title)

        def done(result):
            self._append(title, result)
            log.info("Debug %s: gata.", title)

        def fail(err):
            self._append(f"{title} - EROARE", str(err))
            log.error("Debug %s esuat: %s", title, err)

        self._thread, self._worker = run_async(self, task, on_done=done, on_fail=fail)

    # ------------------------------------------------------------------
    # Probe handlers
    # ------------------------------------------------------------------
    def _probe_sim(self) -> None:
        def task():
            from nav_robot.coppelia.client import connect
            from nav_robot.coppelia.diagnostics import probe_sim_info
            _, sim = connect()
            return probe_sim_info(sim)
        self._run("1. probe_sim_info", task)

    def _probe_robot(self) -> None:
        def task():
            from nav_robot.coppelia.client import connect
            from nav_robot.coppelia.diagnostics import probe_robot_hierarchy
            _, sim = connect()
            return probe_robot_hierarchy(sim)
        self._run("2. probe_robot_hierarchy", task)

    def _probe_scene_scripts(self) -> None:
        def task():
            from nav_robot.coppelia.client import connect
            from nav_robot.coppelia.diagnostics import probe_all_scene_scripts
            _, sim = connect()
            return probe_all_scene_scripts(sim)
        self._run("2b. probe_all_scene_scripts", task)

    def _test_motor_raw(self) -> None:
        def task():
            from nav_robot.coppelia.client import connect, ensure_simulation_running
            from nav_robot.coppelia.diagnostics import test_motor_raw
            _, sim = connect()
            running = ensure_simulation_running(sim)
            res = test_motor_raw(sim, duration_s=3.0, vel_rad_s=2.0)
            res["sim_was_running"] = running
            return res
        self._run("3. test_motor_raw (3s, vel=2.0 rad/s)", task)

    def _test_disable(self) -> None:
        def task():
            from nav_robot.coppelia.client import connect, ensure_simulation_running
            from nav_robot.coppelia.diagnostics import test_disable_methods
            _, sim = connect()
            ensure_simulation_running(sim)
            return test_disable_methods(sim)
        self._run("4. test_disable_methods", task)

    def _test_disable_then_move(self) -> None:
        def task():
            from nav_robot.coppelia.client import connect, ensure_simulation_running
            from nav_robot.coppelia.diagnostics import (
                test_disable_methods, test_motor_raw,
            )
            _, sim = connect()
            ensure_simulation_running(sim)
            disable_res = test_disable_methods(sim)
            move_res = test_motor_raw(sim, duration_s=3.0, vel_rad_s=2.0)
            return {"disable": disable_res, "move_after_disable": move_res}
        self._run("5. disable + move", task)

    def _emergency_stop(self) -> None:
        def task():
            from nav_robot.coppelia.client import connect
            from nav_robot.coppelia.diagnostics import emergency_stop
            _, sim = connect()
            return emergency_stop(sim)
        self._run("STOP", task)
