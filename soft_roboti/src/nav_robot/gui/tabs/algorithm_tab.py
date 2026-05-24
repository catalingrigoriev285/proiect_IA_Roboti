"""Tab 2: selectarea si rularea algoritmilor de planificare."""

from __future__ import annotations

import logging

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup, QComboBox, QDoubleSpinBox, QFormLayout, QFrame, QGroupBox,
    QLabel, QMessageBox, QPushButton, QRadioButton, QScrollArea, QSpinBox,
    QSplitter, QTextEdit, QVBoxLayout, QWidget,
)

from nav_robot.gui.worker import run_async
from nav_robot.map.visualization import plot_map, plot_path
from nav_robot.planners import PLANNER_NAMES, PlanResult, get_planner

log = logging.getLogger("gui.algo")


PLANNERS_LABEL = {
    "A* (Manhattan/Euclidean/Octile)": "astar",
    "Dijkstra (uniform cost)": "dijkstra",
    "BFS (pasi minimi)": "bfs",
    "RRT / RRT* (sampling)": "rrt",
}

REACTIVE_LABEL = {
    "Bug2 (fara harta, tinta cunoscuta)": "bug2",
    "Politica RL antrenata (din tab-ul RL)": "rl_policy",
}


class AlgorithmTab(QWidget):
    """Stanga: configurare + butoane. Dreapta: rezultat text + harta cu traseu."""

    def __init__(self, map_tab, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.map_tab = map_tab
        self.last_result: PlanResult | None = None
        self._thread = None
        self._worker = None
        self._stop_requested = False
        self._build_ui()
        self._on_mode_changed(True)

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        config = self._wrap_scroll(self._build_config())
        info = self._build_info()

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(config)
        splitter.addWidget(info)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([400, 700])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(splitter)

    def _wrap_scroll(self, widget: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        return scroll

    def _build_config(self) -> QWidget:
        wrap = QFrame()
        v = QVBoxLayout(wrap)
        v.setSpacing(8)
        v.setContentsMargins(4, 4, 4, 4)

        # --- Mod ---
        gb_mode = QGroupBox("Mod de navigare")
        v_mode = QVBoxLayout(gb_mode)
        self.rb_with = QRadioButton("Cu harta - planificare globala")
        self.rb_without = QRadioButton("Fara harta - reactiv")
        self.rb_with.setChecked(True)
        group = QButtonGroup(self)
        group.addButton(self.rb_with)
        group.addButton(self.rb_without)
        self.rb_with.toggled.connect(self._on_mode_changed)
        v_mode.addWidget(self.rb_with)
        v_mode.addWidget(self.rb_without)

        # --- Selectie algoritm ---
        gb_algo = QGroupBox("Algoritm")
        f = QFormLayout(gb_algo)
        self.cb_algo = QComboBox()
        self.cb_heuristic = QComboBox()
        self.cb_heuristic.addItems(["manhattan", "euclidean", "octile"])
        self.cb_diagonal = QComboBox()
        self.cb_diagonal.addItems(["4-connectivity", "8-connectivity"])
        f.addRow("Algoritm:", self.cb_algo)
        f.addRow("Euristica (A*):", self.cb_heuristic)
        f.addRow("Conectivitate:", self.cb_diagonal)

        # --- Parametri RRT ---
        gb_rrt = QGroupBox("Parametri RRT")
        f2 = QFormLayout(gb_rrt)
        self.sp_rrt_iter = QSpinBox(); self.sp_rrt_iter.setRange(100, 200_000); self.sp_rrt_iter.setValue(5000)
        self.sp_rrt_step = QDoubleSpinBox(); self.sp_rrt_step.setRange(0.5, 50.0); self.sp_rrt_step.setSingleStep(0.5); self.sp_rrt_step.setValue(3.0)
        self.sp_rrt_bias = QDoubleSpinBox(); self.sp_rrt_bias.setRange(0.0, 0.9); self.sp_rrt_bias.setSingleStep(0.05); self.sp_rrt_bias.setValue(0.1)
        self.sp_rrt_seed = QSpinBox(); self.sp_rrt_seed.setRange(0, 1_000_000); self.sp_rrt_seed.setValue(42)
        self.cb_rrt_star = QComboBox(); self.cb_rrt_star.addItems(["RRT", "RRT*"])
        f2.addRow("Iteratii max:", self.sp_rrt_iter)
        f2.addRow("Step size (celule):", self.sp_rrt_step)
        f2.addRow("Goal bias:", self.sp_rrt_bias)
        f2.addRow("Varianta:", self.cb_rrt_star)
        f2.addRow("Seed RRT:", self.sp_rrt_seed)

        # --- Butoane ---
        gb_actions = QGroupBox("Actiuni")
        v_act = QVBoxLayout(gb_actions)
        self.btn_plan = QPushButton("1. Planifica traseu")
        self.btn_compare = QPushButton("Compara toti algoritmii")
        self.btn_run = QPushButton("2. Ruleaza in CoppeliaSim")
        self.btn_stop = QPushButton("Stop")
        self.btn_plan.clicked.connect(self._on_plan)
        self.btn_compare.clicked.connect(self._on_compare)
        self.btn_run.clicked.connect(self._on_run)
        self.btn_stop.clicked.connect(self._on_stop)
        for b in (self.btn_plan, self.btn_compare, self.btn_run, self.btn_stop):
            v_act.addWidget(b)

        v.addWidget(gb_mode)
        v.addWidget(gb_algo)
        v.addWidget(gb_rrt)
        v.addWidget(gb_actions)
        v.addStretch(1)
        return wrap

    def _build_info(self) -> QWidget:
        wrap = QFrame()
        wrap.setFrameShape(QFrame.Shape.StyledPanel)
        v = QVBoxLayout(wrap)
        v.setContentsMargins(4, 4, 4, 4)

        title = QLabel("Rezultate planificare")
        title.setStyleSheet("font-weight:bold;")
        v.addWidget(title)

        self.txt_result = QTextEdit()
        self.txt_result.setReadOnly(True)
        self.txt_result.setMaximumHeight(140)
        self.txt_result.setStyleSheet(
            "QTextEdit { background:#fafafa; color:#202020; "
            "font-family:Consolas,monospace; font-size:10pt; }"
        )
        v.addWidget(self.txt_result)

        self.figure = Figure(figsize=(6, 5), tight_layout=True)
        self.canvas = FigureCanvasQTAgg(self.figure)
        v.addWidget(self.canvas, stretch=1)
        return wrap

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------
    def _on_mode_changed(self, checked: bool) -> None:
        self.cb_algo.clear()
        with_map = self.rb_with.isChecked()
        if with_map:
            self.cb_algo.addItems(list(PLANNERS_LABEL.keys()))
        else:
            self.cb_algo.addItems(list(REACTIVE_LABEL.keys()))
        self.btn_plan.setEnabled(with_map)
        self.btn_compare.setEnabled(with_map)
        # Run-ul ramane mereu activ - executa fie un plan, fie Bug2 reactiv.

    def _selected_algo_id(self) -> str:
        label = self.cb_algo.currentText()
        return (PLANNERS_LABEL | REACTIVE_LABEL).get(label, "?")

    def _build_planner(self, algo_id: str):
        diagonal = self.cb_diagonal.currentText().startswith("8")
        if algo_id == "astar":
            return get_planner("astar", diagonal=diagonal,
                               heuristic=self.cb_heuristic.currentText())
        if algo_id in ("dijkstra", "bfs"):
            return get_planner(algo_id, diagonal=diagonal)
        if algo_id == "rrt":
            return get_planner(
                "rrt",
                max_iter=self.sp_rrt_iter.value(),
                step_size=self.sp_rrt_step.value(),
                goal_bias=self.sp_rrt_bias.value(),
                star=(self.cb_rrt_star.currentText() == "RRT*"),
                seed=self.sp_rrt_seed.value(),
            )
        raise ValueError(algo_id)

    def _on_plan(self) -> None:
        grid = self.map_tab.current_grid
        if grid is None:
            QMessageBox.warning(self, "Nicio harta",
                                "Genereaza o harta in tab-ul Generare harta.")
            return
        algo_id = self._selected_algo_id()
        if algo_id not in PLANNER_NAMES:
            QMessageBox.information(self, "Stub",
                                    f"Algoritmul reactiv '{algo_id}' nu e inca implementat.")
            return

        log.info("Planificare cu %s ...", algo_id)
        planner = self._build_planner(algo_id)
        self.btn_plan.setEnabled(False)

        def task():
            return planner.plan(grid, grid.start, grid.goal)

        def done(res: PlanResult):
            self.btn_plan.setEnabled(True)
            self.last_result = res
            self._show_result(algo_id, res, grid)

        def fail(err):
            self.btn_plan.setEnabled(True)
            log.error("Planificare esuata: %s", err)
            QMessageBox.critical(self, "Eroare planificare", err)

        self._thread, self._worker = run_async(self, task, on_done=done, on_fail=fail)

    def _on_compare(self) -> None:
        grid = self.map_tab.current_grid
        if grid is None:
            QMessageBox.warning(self, "Nicio harta",
                                "Genereaza o harta in tab-ul Generare harta.")
            return

        diagonal = self.cb_diagonal.currentText().startswith("8")
        configs = [
            ("astar", dict(diagonal=diagonal, heuristic=self.cb_heuristic.currentText())),
            ("dijkstra", dict(diagonal=diagonal)),
            ("bfs", dict(diagonal=diagonal)),
            ("rrt", dict(
                max_iter=self.sp_rrt_iter.value(),
                step_size=self.sp_rrt_step.value(),
                goal_bias=self.sp_rrt_bias.value(),
                star=(self.cb_rrt_star.currentText() == "RRT*"),
                seed=self.sp_rrt_seed.value(),
            )),
        ]
        log.info("Comparare 4 algoritmi pe aceeasi harta ...")
        self.btn_compare.setEnabled(False)

        def task():
            out = []
            for name, kw in configs:
                planner = get_planner(name, **kw)
                res = planner.plan(grid, grid.start, grid.goal)
                out.append((name, res))
            return out

        def done(results: list[tuple[str, PlanResult]]):
            self.btn_compare.setEnabled(True)
            self._show_comparison(results, grid)

        def fail(err):
            self.btn_compare.setEnabled(True)
            log.error("Comparare esuata: %s", err)
            QMessageBox.critical(self, "Eroare", err)

        self._thread, self._worker = run_async(self, task, on_done=done, on_fail=fail)

    def _on_run(self) -> None:
        grid = self.map_tab.current_grid
        if grid is None:
            QMessageBox.warning(self, "Nicio harta",
                                "Genereaza intai o harta in tab-ul Generare harta.")
            return

        if not self.rb_with.isChecked():
            self._run_blind(grid)
            return

        if self.last_result is None or self.last_result.path is None:
            QMessageBox.warning(
                self, "Nicio planificare",
                "Apasa intai 'Planifica traseu'. Robotul are nevoie de waypoint-uri.",
            )
            return

        path = self.last_result.path
        log.info("Pornesc executia traseului (%d waypoints) in CoppeliaSim.", len(path))
        self._stop_requested = False
        self.btn_run.setEnabled(False)

        def task():
            from nav_robot.controller.runner import (
                path_cells_to_world, run_path_in_coppelia,
            )
            from nav_robot.coppelia.client import connect, ensure_simulation_running
            from nav_robot.coppelia.robot import PioneerP3DX
            _, sim = connect()
            # IMPORTANT: pornim simularea PRIMA, apoi instantiem robotul, ca sa
            # putem dezactiva scriptul builtin DUPA ce a fost initializat
            # (altfel se reactiveaza la startSimulation).
            if not ensure_simulation_running(sim):
                log.warning("Simularea nu a ajuns in stare 'running' in 3s.")
            else:
                log.info("Simularea CoppeliaSim ruleaza.")
            robot = PioneerP3DX(sim)

            waypoints = path_cells_to_world(grid, path)

            def progress(idx, total, pose):
                log.info("Waypoint %d/%d  pose=(%.2f, %.2f, yaw=%.2f rad)",
                         idx, total, *pose)

            return run_path_in_coppelia(
                sim, robot, waypoints,
                should_stop=lambda: self._stop_requested,
                on_progress=progress,
            )

        def done(report):
            self.btn_run.setEnabled(True)
            if report.success:
                log.info("Traseu COMPLETAT in %.2fs (%d/%d waypoints).",
                         report.elapsed_s, report.waypoints_reached,
                         report.waypoints_total)
            elif report.aborted:
                log.warning("Traseu ABORTAT (%d/%d waypoints, %.2fs).",
                            report.waypoints_reached, report.waypoints_total,
                            report.elapsed_s)
            else:
                log.warning("Traseu NEINCHEIAT (timeout).")

        def fail(err):
            self.btn_run.setEnabled(True)
            log.error("Executie esuata: %s", err)
            QMessageBox.critical(self, "Eroare executie", err)

        self._thread, self._worker = run_async(self, task, on_done=done, on_fail=fail)

    def _on_stop(self) -> None:
        self._stop_requested = True
        log.info("Stop solicitat - astept iesirea din bucla de control...")

    def _run_blind(self, grid) -> None:
        """Ruleaza navigare fara harta (Bug2 sau politica RL)."""
        algo_id = self._selected_algo_id()
        if algo_id == "rl_policy":
            QMessageBox.information(
                self, "Politica RL nedisponibila",
                "Antreneaza intai o politica in tab-ul Reinforcement Learning, "
                "apoi foloseste butonul 'Run in CoppeliaSim' de acolo.",
            )
            return

        if algo_id != "bug2":
            QMessageBox.warning(self, "Algoritm necunoscut",
                                f"Modul reactiv pentru '{algo_id}' nu este implementat.")
            return

        log.info("Pornesc Bug2 fara harta. Goal=%s (din celula goal a hartii).",
                 grid.to_world(grid.goal))
        self._stop_requested = False
        self.btn_run.setEnabled(False)

        def task():
            from nav_robot.coppelia.client import connect, ensure_simulation_running
            from nav_robot.coppelia.robot import PioneerP3DX
            from nav_robot.reactive.bug2 import bug2_navigate
            _, sim = connect()
            if not ensure_simulation_running(sim):
                log.warning("Simularea nu a ajuns in stare 'running' in 3s.")
            robot = PioneerP3DX(sim)
            goal_world = grid.to_world(grid.goal)

            def progress(state, pose, dist):
                log.info("[%s] pose=(%.2f, %.2f, %.2f rad)  dist_goal=%.2f m",
                         state, pose[0], pose[1], pose[2], dist)

            return bug2_navigate(
                sim, robot, goal_world,
                should_stop=lambda: self._stop_requested,
                on_progress=progress,
            )

        def done(report):
            self.btn_run.setEnabled(True)
            if report.success:
                log.info("Bug2 SUCCES in %.2fs (%d pasi). Dist final=%.2fm.",
                         report.elapsed_s, report.steps, report.final_distance_to_goal)
            elif report.aborted:
                log.warning("Bug2 ABORTAT (%d pasi, %.2fs).", report.steps,
                            report.elapsed_s)
            else:
                log.warning("Bug2 NEINCHEIAT - timeout (%.2fs).", report.elapsed_s)

        def fail(err):
            self.btn_run.setEnabled(True)
            log.error("Bug2 esuat: %s", err)
            QMessageBox.critical(self, "Eroare Bug2", err)

        self._thread, self._worker = run_async(self, task, on_done=done, on_fail=fail)

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------
    def _show_result(self, algo_id: str, res: PlanResult, grid) -> None:
        if res.path is None:
            html = (
                f"<b>{algo_id}</b>: NICIO SOLUTIE.<br>"
                f"Noduri expandate: {res.expanded_nodes}<br>"
                f"Timp: {res.elapsed_s*1000:.2f} ms"
            )
            log.warning("Algoritmul %s nu a gasit drum.", algo_id)
        else:
            cells = len(res.path)
            meters = res.cost * grid.cell_size
            html = (
                f"<b>{algo_id}</b><br>"
                f"Traseu: {cells} celule | cost = {res.cost:.3f} celule "
                f"({meters:.2f} m)<br>"
                f"Noduri expandate: {res.expanded_nodes}<br>"
                f"Timp: {res.elapsed_s*1000:.2f} ms"
            )
            log.info("[%s] %d celule, cost %.3f, expandate %d, %.2f ms",
                     algo_id, cells, res.cost, res.expanded_nodes, res.elapsed_s*1000)
        self.txt_result.setHtml(html)
        self._draw(grid, [(algo_id, res)])

    def _show_comparison(self, results, grid) -> None:
        rows = ["<b>Comparatie algoritmi:</b><br>",
                "<table cellpadding='4' cellspacing='0' "
                "style='border-collapse:collapse;'>",
                "<tr><th>Algoritm</th><th>Celule</th><th>Cost</th>"
                "<th>Expandate</th><th>Timp (ms)</th></tr>"]
        for name, res in results:
            if res.path is None:
                rows.append(f"<tr><td>{name}</td><td colspan='4'>NICIO SOLUTIE</td></tr>")
                log.warning("%s nu a gasit drum.", name)
            else:
                rows.append(
                    f"<tr><td>{name}</td>"
                    f"<td align='right'>{len(res.path)}</td>"
                    f"<td align='right'>{res.cost:.3f}</td>"
                    f"<td align='right'>{res.expanded_nodes}</td>"
                    f"<td align='right'>{res.elapsed_s*1000:.2f}</td></tr>"
                )
                log.info("[cmp %s] %d celule, cost %.3f, exp %d, %.2f ms",
                         name, len(res.path), res.cost, res.expanded_nodes,
                         res.elapsed_s*1000)
        rows.append("</table>")
        self.txt_result.setHtml("".join(rows))
        self._draw(grid, results)

    def _draw(self, grid, results: list[tuple[str, PlanResult]]) -> None:
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        plot_map(grid, ax=ax)
        colors = ["#3498db", "#e67e22", "#9b59b6", "#27ae60"]
        for (name, res), col in zip(results, colors):
            if res.path:
                plot_path(grid, res.path, ax=ax, color=col, label=name)
        self.canvas.draw_idle()
