"""Tab 2: selectarea si pornirea algoritmilor de planificare / navigare."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup, QComboBox, QDoubleSpinBox, QFormLayout, QFrame, QGroupBox,
    QHBoxLayout, QLabel, QMessageBox, QPushButton, QRadioButton, QSpinBox,
    QSplitter, QTextEdit, QVBoxLayout, QWidget,
)

log = logging.getLogger("gui.algo")


PLANNERS = {
    "A* (cu harta)": "astar",
    "Dijkstra (cu harta)": "dijkstra",
    "BFS (cu harta)": "bfs",
    "RRT / RRT* (cu harta, continuu)": "rrt",
}

REACTIVE = {
    "Bug2 (fara harta, tinta cunoscuta)": "bug2",
    "Wall-following pur (lab 06)": "wall",
}


class AlgorithmTab(QWidget):
    """Selectia + lansarea algoritmilor de planificare si navigare."""

    def __init__(self, map_tab, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.map_tab = map_tab  # referinta pentru a accesa harta curenta
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        config = self._build_config()
        info = self._build_info()

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(config)
        splitter.addWidget(info)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([420, 600])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(splitter)

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
        self.cb_algo.addItems(list(PLANNERS.keys()))
        self.cb_heuristic = QComboBox()
        self.cb_heuristic.addItems(["manhattan", "euclidean", "octile"])
        self.cb_diagonal = QComboBox()
        self.cb_diagonal.addItems(["4-connectivity", "8-connectivity"])
        f.addRow("Algoritm:", self.cb_algo)
        f.addRow("Euristica (A*):", self.cb_heuristic)
        f.addRow("Conectivitate:", self.cb_diagonal)

        # --- Parametri RRT ---
        gb_rrt = QGroupBox("Parametri RRT (cand e cazul)")
        f2 = QFormLayout(gb_rrt)
        self.sp_rrt_iter = QSpinBox(); self.sp_rrt_iter.setRange(100, 100_000); self.sp_rrt_iter.setValue(5000)
        self.sp_rrt_step = QDoubleSpinBox(); self.sp_rrt_step.setRange(0.05, 5.0); self.sp_rrt_step.setSingleStep(0.05); self.sp_rrt_step.setValue(0.5); self.sp_rrt_step.setSuffix(" m")
        self.sp_rrt_bias = QDoubleSpinBox(); self.sp_rrt_bias.setRange(0.0, 0.9); self.sp_rrt_bias.setSingleStep(0.05); self.sp_rrt_bias.setValue(0.1)
        f2.addRow("Iteratii max:", self.sp_rrt_iter)
        f2.addRow("Step size:", self.sp_rrt_step)
        f2.addRow("Goal bias:", self.sp_rrt_bias)

        # --- Butoane ---
        gb_actions = QGroupBox("Actiuni")
        v_act = QVBoxLayout(gb_actions)
        self.btn_plan = QPushButton("1. Planifica traseu")
        self.btn_run = QPushButton("2. Ruleaza in CoppeliaSim")
        self.btn_stop = QPushButton("Stop")
        self.btn_plan.clicked.connect(self._on_plan)
        self.btn_run.clicked.connect(self._on_run)
        self.btn_stop.clicked.connect(self._on_stop)
        for b in (self.btn_plan, self.btn_run, self.btn_stop):
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

        title = QLabel("Rezultate planificare / executie")
        title.setStyleSheet("font-weight:bold;")
        v.addWidget(title)

        self.txt_result = QTextEdit()
        self.txt_result.setReadOnly(True)
        self.txt_result.setStyleSheet(
            "QTextEdit { background:#fafafa; color:#202020; "
            "font-family:Consolas,monospace; font-size:10pt; }"
        )
        v.addWidget(self.txt_result, stretch=1)

        self.lbl_status = QLabel("Astept...")
        self.lbl_status.setStyleSheet("color:#888;")
        v.addWidget(self.lbl_status)
        return wrap

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------
    def _on_mode_changed(self, checked: bool) -> None:
        # `checked` se refera la rb_with
        self.cb_algo.clear()
        if self.rb_with.isChecked():
            self.cb_algo.addItems(list(PLANNERS.keys()))
        else:
            self.cb_algo.addItems(list(REACTIVE.keys()))

    def _selected_algo_id(self) -> str:
        label = self.cb_algo.currentText()
        return (PLANNERS | REACTIVE).get(label, "?")

    def _on_plan(self) -> None:
        grid = self.map_tab.current_grid
        if grid is None:
            QMessageBox.warning(self, "Nicio harta",
                                "Genereaza intai o harta in tab-ul Harta.")
            return
        algo_id = self._selected_algo_id()
        log.info("Planificare cu algoritm: %s (mod=%s)",
                 algo_id, "harta" if self.rb_with.isChecked() else "reactiv")
        self.lbl_status.setText(f"Planificare cu {algo_id}...")
        self.txt_result.append(f">>> plan {algo_id}: nu este inca implementat (faza 2).")
        log.warning("Planificarea efectiva pentru '%s' nu este inca implementata (stub).",
                    algo_id)

    def _on_run(self) -> None:
        algo_id = self._selected_algo_id()
        log.info("Run CoppeliaSim cu %s (stub)", algo_id)
        self.txt_result.append(f">>> run {algo_id}: nu este inca implementat (faza 3+).")
        self.lbl_status.setText(f"Run {algo_id} - stub")

    def _on_stop(self) -> None:
        log.info("Stop solicitat de utilizator.")
        self.lbl_status.setText("Stop solicitat.")
