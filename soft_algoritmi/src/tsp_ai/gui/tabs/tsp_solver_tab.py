"""TSP Solver tab implementation."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

import pandas as pd

from PySide2.QtCore import Qt, QThreadPool
from PySide2.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QProgressBar,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)

from tsp_ai.app.services.result_schema import ExperimentResult
from tsp_ai.app.services.run_service import RunService
from tsp_ai.gui.widgets.card import CardFrame
from tsp_ai.gui.widgets.mpl_canvas import MplCanvas
from tsp_ai.gui.workers.tsp_workers import run_tsp_solver_worker
from tsp_ai.gui.workers.worker_base import Worker
from tsp_ai.tsp.io_utils import coords_to_distance_matrix, random_distance_matrix, read_coordinates_csv, read_matrix_file
from tsp_ai.common.plotting import create_placeholder_figure
from tsp_ai.tsp.plots import plot_cost_history, plot_route
from tsp_ai.tsp.utils import format_tour_route, validate_distance_matrix

logger = logging.getLogger(__name__)


class TspSolverTab(QWidget):
    """Tab for solving a single TSP instance."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.thread_pool = QThreadPool.globalInstance()
        self.matrix: Optional[List[List[int]]] = None
        self.coords = None
        self.last_result = None
        self.last_run_dir = None
        self.run_service = RunService()

        layout = QHBoxLayout()
        layout.setSpacing(16)
        layout.addWidget(self._build_left_panel(), 2)
        layout.addWidget(self._build_output_group(), 3)
        self.setLayout(layout)

    def _build_left_panel(self) -> QWidget:
        card = CardFrame()
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addWidget(self._build_input_group())
        layout.addWidget(self._build_algo_group())
        layout.addStretch(1)
        card.setLayout(layout)
        return card

    def _build_input_group(self) -> QGroupBox:
        group = QGroupBox("Input")
        layout = QFormLayout()

        self.matrix_path = QLineEdit()
        btn_matrix = QPushButton("Load matrix file")
        btn_matrix.clicked.connect(self._load_matrix)
        row = QHBoxLayout()
        row.addWidget(self.matrix_path)
        row.addWidget(btn_matrix)
        layout.addRow("Matrix:", row)

        self.coords_path = QLineEdit()
        btn_coords = QPushButton("Load coords CSV")
        btn_coords.clicked.connect(self._load_coords)
        row2 = QHBoxLayout()
        row2.addWidget(self.coords_path)
        row2.addWidget(btn_coords)
        layout.addRow("Coords:", row2)

        self.rand_n = QSpinBox()
        self.rand_n.setRange(5, 200)
        self.rand_seed = QSpinBox()
        self.rand_seed.setRange(0, 10_000)
        self.rand_seed.setValue(42)
        self.rand_low = QSpinBox()
        self.rand_low.setRange(1, 1000)
        self.rand_low.setValue(1)
        self.rand_high = QSpinBox()
        self.rand_high.setRange(2, 2000)
        self.rand_high.setValue(100)
        btn_rand = QPushButton("Generate random")
        btn_rand.clicked.connect(self._generate_random)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("N"))
        row3.addWidget(self.rand_n)
        row3.addWidget(QLabel("Seed"))
        row3.addWidget(self.rand_seed)
        row3.addWidget(QLabel("Low"))
        row3.addWidget(self.rand_low)
        row3.addWidget(QLabel("High"))
        row3.addWidget(self.rand_high)
        row3.addWidget(btn_rand)
        layout.addRow("Random:", row3)

        group.setLayout(layout)
        return group

    def _build_algo_group(self) -> QGroupBox:
        group = QGroupBox("Algorithm")
        layout = QVBoxLayout()

        self.algo_combo = QComboBox()
        self.algo_options = [
            ("Backtracking", "bkt"),
            ("Nearest Neighbor", "nn"),
            ("Hill Climbing", "hc"),
            ("Simulated Annealing", "sa"),
            ("Genetic Algorithm", "ga"),
        ]
        self.algo_combo.addItems([label for label, _ in self.algo_options])
        self.algo_combo.currentIndexChanged.connect(self._algo_changed)

        self.param_stack = QStackedWidget()
        self.param_stack.addWidget(self._build_bkt_params())
        self.param_stack.addWidget(self._build_nn_params())
        self.param_stack.addWidget(self._build_hc_params())
        self.param_stack.addWidget(self._build_sa_params())
        self.param_stack.addWidget(self._build_ga_params())

        btn_run = QPushButton("Run")
        btn_run.setObjectName("Accent")
        btn_run.clicked.connect(self._run)

        layout.addWidget(self.algo_combo)
        layout.addWidget(self.param_stack)
        layout.addWidget(btn_run)
        group.setLayout(layout)
        return group

    def _current_algo_code(self) -> str:
        index = self.algo_combo.currentIndex()
        if index < 0:
            return "bkt"
        return self.algo_options[index][1]

    def _build_bkt_params(self) -> QWidget:
        w = QWidget()
        layout = QFormLayout()
        self.bkt_mode = QComboBox()
        self.bkt_mode.addItems(["prima", "toate", "timp", "y_solutii"])
        self.bkt_time = QSpinBox()
        self.bkt_time.setRange(1, 3600)
        self.bkt_time.setValue(10)
        self.bkt_y = QSpinBox()
        self.bkt_y.setRange(1, 1000)
        self.bkt_y.setValue(10)
        layout.addRow("Mode", self.bkt_mode)
        layout.addRow("Time limit (s)", self.bkt_time)
        layout.addRow("Y solutions", self.bkt_y)
        w.setLayout(layout)
        return w

    def _build_nn_params(self) -> QWidget:
        w = QWidget()
        layout = QFormLayout()
        self.nn_start = QSpinBox()
        self.nn_start.setRange(0, 1000)
        self.nn_multistart = QComboBox()
        self.nn_multistart.addItems(["no", "yes"])
        layout.addRow("Start city", self.nn_start)
        layout.addRow("Multistart", self.nn_multistart)
        w.setLayout(layout)
        return w

    def _build_hc_params(self) -> QWidget:
        w = QWidget()
        layout = QFormLayout()
        self.hc_restarts = QSpinBox()
        self.hc_restarts.setRange(1, 200)
        self.hc_restarts.setValue(10)
        self.hc_iters = QSpinBox()
        self.hc_iters.setRange(10, 10000)
        self.hc_iters.setValue(200)
        self.hc_neighbor = QComboBox()
        self.hc_neighbor.addItems(["2-opt", "swap", "mixed"])
        layout.addRow("Restarts", self.hc_restarts)
        layout.addRow("Iterations", self.hc_iters)
        layout.addRow("Neighbor", self.hc_neighbor)
        w.setLayout(layout)
        return w

    def _build_sa_params(self) -> QWidget:
        w = QWidget()
        layout = QFormLayout()
        self.sa_init = QComboBox()
        self.sa_init.addItems(["random", "nn", "nn-multistart-best"])
        self.sa_schedule = QComboBox()
        self.sa_schedule.addItems(["geometric", "linear", "logarithmic"])
        self.sa_tmax = QSpinBox()
        self.sa_tmax.setRange(1, 100000)
        self.sa_tmax.setValue(1000)
        self.sa_tmin = QSpinBox()
        self.sa_tmin.setRange(1, 100000)
        self.sa_tmin.setValue(1)
        self.sa_alpha = QLineEdit("0.995")
        self.sa_iters = QSpinBox()
        self.sa_iters.setRange(100, 200000)
        self.sa_iters.setValue(2000)
        self.sa_prob_swap = QLineEdit("0.34")
        self.sa_prob_2opt = QLineEdit("0.33")
        self.sa_prob_or = QLineEdit("0.33")
        layout.addRow("Init", self.sa_init)
        layout.addRow("Schedule", self.sa_schedule)
        layout.addRow("Tmax", self.sa_tmax)
        layout.addRow("Tmin", self.sa_tmin)
        layout.addRow("Alpha", self.sa_alpha)
        layout.addRow("Iterations", self.sa_iters)
        layout.addRow("P(swap)", self.sa_prob_swap)
        layout.addRow("P(2-opt)", self.sa_prob_2opt)
        layout.addRow("P(or-opt)", self.sa_prob_or)
        w.setLayout(layout)
        return w

    def _build_ga_params(self) -> QWidget:
        w = QWidget()
        layout = QFormLayout()
        self.ga_pop = QSpinBox()
        self.ga_pop.setRange(10, 1000)
        self.ga_pop.setValue(100)
        self.ga_gen = QSpinBox()
        self.ga_gen.setRange(10, 2000)
        self.ga_gen.setValue(200)
        self.ga_mut = QLineEdit("0.2")
        self.ga_sel = QComboBox()
        self.ga_sel.addItems(["tournament", "rws", "rank", "sus"])
        self.ga_elite = QSpinBox()
        self.ga_elite.setRange(0, 50)
        self.ga_elite.setValue(2)
        self.ga_k = QSpinBox()
        self.ga_k.setRange(2, 10)
        self.ga_k.setValue(3)
        layout.addRow("Population", self.ga_pop)
        layout.addRow("Generations", self.ga_gen)
        layout.addRow("Mutation rate", self.ga_mut)
        layout.addRow("Selection", self.ga_sel)
        layout.addRow("Elitism", self.ga_elite)
        layout.addRow("Tournament k", self.ga_k)
        w.setLayout(layout)
        return w

    def _build_output_group(self) -> QGroupBox:
        group = CardFrame()
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        self.output_label = QLabel("Ready")
        self.route_label = QLabel("")
        self.route_label.setWordWrap(True)
        self.data_view = QPlainTextEdit()
        self.data_view.setReadOnly(True)
        self.data_view.setPlaceholderText("Load or generate data to view city values.")
        self.canvas_route = MplCanvas(create_placeholder_figure())
        self.canvas_history = MplCanvas(create_placeholder_figure())
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        layout.addWidget(self.output_label)
        layout.addWidget(self.route_label)
        layout.addWidget(self.progress)
        layout.addWidget(QLabel("Data values"))
        layout.addWidget(self.data_view)
        layout.addWidget(self.canvas_route)
        layout.addWidget(self.canvas_history)
        group.setLayout(layout)
        return group

    def _update_data_view(self) -> None:
        if self.coords:
            lines = ["Coordinates (index, x, y):"]
            for idx, (x, y) in enumerate(self.coords):
                lines.append(f"{idx}: {x}, {y}")
            self.data_view.setPlainText("\n".join(lines))
            return
        if self.matrix:
            n = len(self.matrix)
            lines = [f"Matrix ({n}x{n}):"]
            max_width = max(len(str(value)) for row in self.matrix for value in row)
            for row in self.matrix:
                lines.append(" ".join(f"{value:>{max_width}}" for value in row))
            self.data_view.setPlainText("\n".join(lines))
            return
        self.data_view.setPlainText("No data loaded.")

    def _algo_changed(self) -> None:
        self.param_stack.setCurrentIndex(self.algo_combo.currentIndex())

    def _load_matrix(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Load matrix file", "", "Text Files (*.txt)")
        if path:
            try:
                self.matrix_path.setText(path)
                self.matrix = read_matrix_file(path)
                validate_distance_matrix(self.matrix)
                self.coords = None
                self._update_data_view()
                logger.info("Loaded matrix file.")
            except Exception as exc:
                QMessageBox.critical(self, "Invalid matrix", str(exc))

    def _load_coords(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Load coordinates CSV", "", "CSV Files (*.csv)")
        if path:
            try:
                self.coords_path.setText(path)
                self.coords = read_coordinates_csv(path)
                self.matrix = coords_to_distance_matrix(self.coords)
                validate_distance_matrix(self.matrix)
                self._update_data_view()
                logger.info("Loaded coordinates file.")
            except Exception as exc:
                QMessageBox.critical(self, "Invalid coordinates", str(exc))

    def _generate_random(self) -> None:
        self.matrix = random_distance_matrix(
            self.rand_n.value(),
            self.rand_low.value(),
            self.rand_high.value(),
            seed=self.rand_seed.value(),
        )
        self.coords = None
        self._update_data_view()
        logger.info("Generated random matrix.")

    def _collect_params(self) -> Dict:
        algo = self._current_algo_code()
        if algo == "bkt":
            return {
                "mode": self.bkt_mode.currentText(),
                "time_limit": float(self.bkt_time.value()),
                "y_solutions": int(self.bkt_y.value()),
            }
        if algo == "nn":
            return {
                "start_city": int(self.nn_start.value()),
                "multistart": self.nn_multistart.currentText() == "yes",
            }
        if algo == "hc":
            return {
                "restarts": int(self.hc_restarts.value()),
                "iterations": int(self.hc_iters.value()),
                "neighbor": self.hc_neighbor.currentText(),
                "seed": int(self.rand_seed.value()),
            }
        if algo == "sa":
            return {
                "init_mode": self.sa_init.currentText(),
                "schedule": self.sa_schedule.currentText(),
                "t_max": float(self.sa_tmax.value()),
                "t_min": float(self.sa_tmin.value()),
                "alpha": float(self.sa_alpha.text()),
                "iterations": int(self.sa_iters.value()),
                "neighbor_probs": {
                    "swap": float(self.sa_prob_swap.text()),
                    "2-opt": float(self.sa_prob_2opt.text()),
                    "or-opt": float(self.sa_prob_or.text()),
                },
                "seed": int(self.rand_seed.value()),
            }
        return {
            "pop_size": int(self.ga_pop.value()),
            "generations": int(self.ga_gen.value()),
            "mutation_rate": float(self.ga_mut.text()),
            "selection_type": self.ga_sel.currentText(),
            "elitism": int(self.ga_elite.value()),
            "tournament_k": int(self.ga_k.value()),
            "seed": int(self.rand_seed.value()),
        }

    def _run(self) -> None:
        if not self.matrix:
            QMessageBox.information(self, "Missing input", "Please load or generate a matrix.")
            return
        algo = self._current_algo_code()
        params = self._collect_params()
        worker = Worker(run_tsp_solver_worker, algo, self.matrix, params)
        worker.signals.result.connect(self._on_result)
        worker.signals.error.connect(self._on_error)
        self.output_label.setText("Running...")
        self.progress.setRange(0, 0)
        self.thread_pool.start(worker)

    def _on_result(self, result) -> None:
        self.last_result = result
        self.output_label.setText(
            f"Cost: {result.cost:.3f} | Elapsed: {result.elapsed_sec:.3f}s | Tour length: {len(result.tour)}"
        )
        self.route_label.setText(f"Route: {format_tour_route(result.tour)}")
        self._update_plot(result)
        self._auto_save(result)
        self.progress.setRange(0, 1)
        self.progress.setValue(1)

    def _update_plot(self, result) -> None:
        route_fig = plot_route(self.coords, result.tour, self.matrix)
        self.canvas_route.figure = route_fig
        self.canvas_route.sync_figure_size()
        self.canvas_route.draw()
        if result.history:
            hist_fig = plot_cost_history(result.history, "Cost History")
        else:
            hist_fig = create_placeholder_figure()
        self.canvas_history.figure = hist_fig
        self.canvas_history.sync_figure_size()
        self.canvas_history.draw()

    def _auto_save(self, result) -> None:
        metrics = [
            {
                "algorithm": result.algorithm,
                "cost": result.cost,
                "elapsed_sec": result.elapsed_sec,
            }
        ]
        exp_result = ExperimentResult(
            run_type="tsp",
            task="solve",
            metrics=metrics,
            summary={"algorithm": result.algorithm, "cost": result.cost},
        )
        figures = {
            "route": plot_route(self.coords, result.tour, self.matrix),
        }
        if result.history:
            figures["cost_history"] = plot_cost_history(result.history, "Cost History")
        run_dir = self.run_service.save_run(
            prefix=f"tsp_{result.algorithm}",
            config={"algorithm": result.algorithm, "params": result.params},
            result=exp_result,
            figures=figures,
            artifacts={"history": result.history or {}},
        )
        self.last_run_dir = run_dir

    def _on_error(self, message: str) -> None:
        logger.error(message)
        QMessageBox.critical(self, "Error", "Solver failed.")
        self.output_label.setText("Error.")
        self.route_label.setText("")
