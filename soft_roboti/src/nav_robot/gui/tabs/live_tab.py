"""Tab Live: harta in timp real cu pozitia robotului + predictie + statistici.

Stanga: matplotlib map cu obstacole, start/goal, robot (sageata), trail (linie
estompata cu ultimele N pozitii), predictie (extrapolare 2s din viteza curenta),
plus traseul planificat daca exista.

Dreapta: panou statistici live (pozitie, yaw, viteze, senzori, distanta la goal,
rata de update).

Polling: QTimer in firul GUI, citeste sim la 5 Hz (default). Fiecare apel ZMQ
e scurt; daca devine prea costisitor se poate muta intr-un thread.
"""

from __future__ import annotations

import collections
import logging
import math
import time

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.colors import ListedColormap
from matplotlib.figure import Figure
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox, QFormLayout, QFrame, QGroupBox, QHBoxLayout, QLabel,
    QMessageBox, QPushButton, QScrollArea, QSpinBox, QSplitter,
    QVBoxLayout, QWidget,
)

log = logging.getLogger("gui.live")

_CMAP = ListedColormap(["#ffffff", "#202020"])
_TRAIL_MAX = 250


class LiveTab(QWidget):
    """Vizualizare in timp real a robotului + statistici."""

    def __init__(self, map_tab, algo_tab, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.map_tab = map_tab
        self.algo_tab = algo_tab
        self._sim = None
        self._robot = None
        self._trail: collections.deque[tuple[float, float, float]] = collections.deque(maxlen=_TRAIL_MAX)
        self._last_poll_t: float | None = None
        self._poll_rates: collections.deque[float] = collections.deque(maxlen=30)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        left = self._build_map()
        right = self._wrap_scroll(self._build_stats())
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(left); splitter.addWidget(right)
        splitter.setStretchFactor(0, 1); splitter.setStretchFactor(1, 0)
        splitter.setSizes([700, 320])
        layout = QVBoxLayout(self); layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(splitter)

    def _wrap_scroll(self, widget: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidget(widget); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        return scroll

    def _build_map(self) -> QWidget:
        wrap = QFrame(); wrap.setFrameShape(QFrame.Shape.StyledPanel)
        v = QVBoxLayout(wrap); v.setContentsMargins(4, 4, 4, 4)
        v.addWidget(QLabel("<b>Harta live: robot + trail + predictie</b>"))
        self.figure = Figure(figsize=(7, 7), tight_layout=True)
        self.canvas = FigureCanvasQTAgg(self.figure)
        v.addWidget(self.canvas, stretch=1)
        return wrap

    def _build_stats(self) -> QWidget:
        wrap = QFrame()
        v = QVBoxLayout(wrap); v.setSpacing(8); v.setContentsMargins(4, 4, 4, 4)

        gb_ctrl = QGroupBox("Control polling")
        f = QFormLayout(gb_ctrl)
        self.sp_rate = QSpinBox(); self.sp_rate.setRange(1, 20); self.sp_rate.setValue(5); self.sp_rate.setSuffix(" Hz")
        self.cb_pred = QCheckBox("Arata predictie (2s)"); self.cb_pred.setChecked(True)
        self.cb_trail = QCheckBox("Arata trail"); self.cb_trail.setChecked(True)
        self.cb_path = QCheckBox("Arata traseu planificat (din tab Algoritmi)"); self.cb_path.setChecked(True)
        f.addRow("Rata:", self.sp_rate)
        f.addRow(self.cb_pred)
        f.addRow(self.cb_trail)
        f.addRow(self.cb_path)
        self.sp_rate.valueChanged.connect(self._on_rate_change)

        gb_btn = QGroupBox("Actiuni")
        v_btn = QVBoxLayout(gb_btn)
        self.btn_start = QPushButton("Conecteaza si porneste polling")
        self.btn_stop = QPushButton("Stop polling")
        self.btn_reset_trail = QPushButton("Sterge trail")
        self.btn_start.clicked.connect(self._on_start)
        self.btn_stop.clicked.connect(self._on_stop)
        self.btn_reset_trail.clicked.connect(lambda: (self._trail.clear(), self._redraw()))
        for b in (self.btn_start, self.btn_stop, self.btn_reset_trail):
            v_btn.addWidget(b)

        gb_pos = QGroupBox("Pozitie robot")
        self.lbl_pos = QLabel("—"); self.lbl_pos.setFont(QFont("Consolas", 10))
        QVBoxLayout(gb_pos).addWidget(self.lbl_pos)

        gb_vel = QGroupBox("Viteze")
        self.lbl_vel = QLabel("—"); self.lbl_vel.setFont(QFont("Consolas", 10))
        QVBoxLayout(gb_vel).addWidget(self.lbl_vel)

        gb_sens = QGroupBox("Senzori (min, m)")
        self.lbl_sens = QLabel("—"); self.lbl_sens.setFont(QFont("Consolas", 10))
        QVBoxLayout(gb_sens).addWidget(self.lbl_sens)

        gb_goal = QGroupBox("Goal & predictie")
        self.lbl_goal = QLabel("—"); self.lbl_goal.setFont(QFont("Consolas", 10))
        QVBoxLayout(gb_goal).addWidget(self.lbl_goal)

        gb_stat = QGroupBox("Status conexiune")
        self.lbl_status = QLabel("Neconectat."); self.lbl_status.setFont(QFont("Consolas", 10))
        self.lbl_status.setWordWrap(True)
        QVBoxLayout(gb_stat).addWidget(self.lbl_status)

        for gb in (gb_ctrl, gb_btn, gb_pos, gb_vel, gb_sens, gb_goal, gb_stat):
            v.addWidget(gb)
        v.addStretch(1)
        return wrap

    # ------------------------------------------------------------------
    # Control polling
    # ------------------------------------------------------------------
    def _on_start(self) -> None:
        if self.map_tab.current_grid is None:
            QMessageBox.warning(self, "Nicio harta",
                                "Genereaza intai o harta in tab-ul Generare harta.")
            return
        try:
            from nav_robot.coppelia.client import connect
            from nav_robot.coppelia.robot import PioneerP3DX
            _, self._sim = connect()
            self._robot = PioneerP3DX(self._sim)
        except Exception as e:
            log.error("Conectare esuata: %s", e)
            QMessageBox.critical(self, "Conexiune CoppeliaSim", str(e))
            self._sim = None; self._robot = None
            return
        self._trail.clear()
        self._poll_rates.clear()
        self._last_poll_t = None
        self._on_rate_change(self.sp_rate.value())
        self._timer.start()
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.lbl_status.setText("Conectat. Polling pornit.")
        log.info("Live polling pornit la %d Hz.", self.sp_rate.value())
        self._draw_static()

    def _on_stop(self) -> None:
        self._timer.stop()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.lbl_status.setText("Polling oprit.")
        log.info("Live polling oprit.")

    def _on_rate_change(self, hz: int) -> None:
        self._timer.setInterval(int(1000 / max(1, hz)))

    # ------------------------------------------------------------------
    # Polling
    # ------------------------------------------------------------------
    def _poll(self) -> None:
        if self._sim is None or self._robot is None:
            return
        t_now = time.perf_counter()
        if self._last_poll_t is not None:
            dt = t_now - self._last_poll_t
            if dt > 0:
                self._poll_rates.append(1.0 / dt)
        self._last_poll_t = t_now

        try:
            x, y, yaw = self._robot.pose()
        except Exception as e:
            self.lbl_status.setText(f"Eroare pose: {e}")
            return

        # Viteze curente (rad/s) din motoare
        v_l_rad = v_r_rad = math.nan
        try:
            v_l_rad = float(self._sim.getJointVelocity(self._robot.left_motor))
            v_r_rad = float(self._sim.getJointVelocity(self._robot.right_motor))
        except Exception:
            pass

        # Convertire la (v_lin, omega) m/s, rad/s
        from nav_robot.controller.differential_drive import wheels_to_cmd
        try:
            v_lin, omega = wheels_to_cmd(v_l_rad, v_r_rad)
        except Exception:
            v_lin, omega = math.nan, math.nan

        # Senzori (front, left, right) - min distanta
        sens_info = {"front": math.inf, "left": math.inf, "right": math.inf}
        try:
            from nav_robot.coppelia.sensors import min_distance, read_all_sensors
            from nav_robot.reactive.wall_following import (
                FRONT_SENSORS, LEFT_SENSORS, RIGHT_SENSORS,
            )
            readings = read_all_sensors(self._sim, self._robot.sensors)
            sens_info["front"] = min_distance(readings, FRONT_SENSORS)
            sens_info["left"] = min_distance(readings, LEFT_SENSORS)
            sens_info["right"] = min_distance(readings, RIGHT_SENSORS)
        except Exception:
            pass

        # Goal & distanta
        grid = self.map_tab.current_grid
        gx, gy = grid.to_world(grid.goal)
        d_goal = math.hypot(gx - x, gy - y)

        # Predictie 2s linear: integrare Euler din v_lin, omega
        pred_pts: list[tuple[float, float]] = []
        if self.cb_pred.isChecked() and not math.isnan(v_lin):
            px, py, pyaw = x, y, yaw
            dt = 0.1
            for _ in range(20):  # 2 secunde
                px += v_lin * math.cos(pyaw) * dt
                py += v_lin * math.sin(pyaw) * dt
                pyaw += omega * dt
                pred_pts.append((px, py))

        # Trail
        self._trail.append((x, y, yaw))

        # Update stats labels
        self.lbl_pos.setText(
            f"x   : {x:7.3f} m\n"
            f"y   : {y:7.3f} m\n"
            f"yaw : {yaw:7.3f} rad  ({math.degrees(yaw):+.1f}°)"
        )
        self.lbl_vel.setText(
            f"v_l : {v_l_rad:7.3f} rad/s\n"
            f"v_r : {v_r_rad:7.3f} rad/s\n"
            f"v_lin: {v_lin:6.3f} m/s\n"
            f"omega: {omega:6.3f} rad/s"
        )
        self.lbl_sens.setText(
            f"front: {self._fmt_dist(sens_info['front'])}\n"
            f"left : {self._fmt_dist(sens_info['left'])}\n"
            f"right: {self._fmt_dist(sens_info['right'])}"
        )
        pred_end = pred_pts[-1] if pred_pts else (x, y)
        self.lbl_goal.setText(
            f"goal world: ({gx:.2f}, {gy:.2f})\n"
            f"dist goal : {d_goal:6.2f} m\n"
            f"predictie@2s: ({pred_end[0]:.2f}, {pred_end[1]:.2f})"
        )
        rate_avg = (sum(self._poll_rates) / len(self._poll_rates)) if self._poll_rates else 0.0
        try:
            sstate = self._sim.getSimulationState()
        except Exception:
            sstate = -1
        self.lbl_status.setText(
            f"Conectat. sim_state={sstate}  rate={rate_avg:.1f} Hz  "
            f"trail={len(self._trail)} pts"
        )

        self._redraw(robot_pose=(x, y, yaw), prediction=pred_pts)

    @staticmethod
    def _fmt_dist(d: float) -> str:
        return "inf" if math.isinf(d) else f"{d:5.3f} m"

    # ------------------------------------------------------------------
    # Desenare harta
    # ------------------------------------------------------------------
    def _draw_static(self) -> None:
        """Re-deseneaza fundalul (apelat la pornire / schimbare harta)."""
        self._redraw()

    def _redraw(self, robot_pose=None, prediction=None) -> None:
        grid = self.map_tab.current_grid
        if grid is None:
            return
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Harta de fundal
        ax.imshow(grid.cells, cmap=_CMAP, origin="lower",
                  extent=(0, grid.world_size()[0], 0, grid.world_size()[1]),
                  interpolation="nearest")
        sx_w, sy_w = grid.to_world(grid.start)
        gx_w, gy_w = grid.to_world(grid.goal)
        ax.scatter([sx_w], [sy_w], c="#2ecc71", s=140, marker="o",
                   edgecolors="black", linewidths=1.0, zorder=4, label="start")
        ax.scatter([gx_w], [gy_w], c="#e74c3c", s=180, marker="*",
                   edgecolors="black", linewidths=1.0, zorder=4, label="goal")

        # Traseu planificat (din algorithm_tab)
        if self.cb_path.isChecked():
            last = getattr(self.algo_tab, "last_result", None)
            if last is not None and last.path:
                xs = [grid.to_world(c)[0] for c in last.path]
                ys = [grid.to_world(c)[1] for c in last.path]
                ax.plot(xs, ys, color="#3498db", linewidth=2, alpha=0.6,
                        marker="o", markersize=3, label="traseu planificat",
                        zorder=3)

        # Trail
        if self.cb_trail.isChecked() and len(self._trail) > 1:
            xs = [p[0] for p in self._trail]
            ys = [p[1] for p in self._trail]
            ax.plot(xs, ys, color="#8e44ad", linewidth=1.5, alpha=0.7,
                    zorder=5, label="trail")

        # Predictie
        if prediction:
            xs = [p[0] for p in prediction]
            ys = [p[1] for p in prediction]
            ax.plot(xs, ys, color="#f39c12", linewidth=2.0, linestyle="--",
                    zorder=6, label="predictie 2s")
            ax.scatter([xs[-1]], [ys[-1]], c="#f39c12", s=60, marker="x",
                       zorder=7)

        # Robot (sageata)
        if robot_pose is None and self._trail:
            robot_pose = self._trail[-1]
        if robot_pose is not None:
            rx, ry, ryaw = robot_pose
            arrow_len = max(grid.cell_size * 0.6, 0.25)
            dx = arrow_len * math.cos(ryaw)
            dy = arrow_len * math.sin(ryaw)
            ax.arrow(rx, ry, dx, dy, head_width=0.15, head_length=0.12,
                     fc="#c0392b", ec="#c0392b", linewidth=2.0, zorder=8)
            ax.scatter([rx], [ry], c="#c0392b", s=70, zorder=8,
                       edgecolors="white", linewidths=1.5, label="robot")

        ax.set_xlabel("X (m)"); ax.set_ylabel("Y (m)")
        ax.set_aspect("equal")
        ww, wh = grid.world_size()
        ax.set_xlim(0, ww); ax.set_ylim(0, wh)
        ax.grid(True, alpha=0.2)
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0),
                   framealpha=0.85, fontsize=8)
        self.canvas.draw_idle()
