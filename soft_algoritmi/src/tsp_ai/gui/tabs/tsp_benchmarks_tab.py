"""TSP Benchmarks tab implementation."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

import pandas as pd
from PySide2.QtCore import QThreadPool
from PySide2.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)

from tsp_ai.app.services.result_schema import ExperimentResult
from tsp_ai.app.services.run_service import RunService
from tsp_ai.gui.widgets.card import CardFrame
from tsp_ai.gui.widgets.mpl_canvas import MplCanvas
from tsp_ai.gui.workers.tsp_workers import run_tsp_benchmark_worker
from tsp_ai.gui.workers.worker_base import CancelableWorker
from tsp_ai.tsp.plots import plot_cost_vs_n, plot_gap_vs_n, plot_runtime_vs_n, plot_runtime_vs_n_log

logger = logging.getLogger(__name__)


class TspBenchmarksTab(QWidget):
    """Tab for TSP benchmark suites."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.thread_pool = QThreadPool.globalInstance()
        self.results: Optional[pd.DataFrame] = None
        self.current_worker: Optional[CancelableWorker] = None
        self.run_service = RunService()

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.addWidget(self._build_controls())
        layout.addWidget(self._build_table())
        layout.addWidget(self._build_plots())
        self.setLayout(layout)

    def _build_controls(self) -> QGroupBox:
        group = CardFrame()
        layout = QFormLayout()

        self.suite = QComboBox()
        self.suite.addItems(["small", "medium", "large", "custom"])
        self.alg_nn = QCheckBox("nn")
        self.alg_hc = QCheckBox("hc")
        self.alg_sa = QCheckBox("sa")
        self.alg_ga = QCheckBox("ga")
        self.alg_nn.setChecked(True)
        self.alg_hc.setChecked(True)
        self.alg_sa.setChecked(True)
        self.alg_ga.setChecked(True)

        alg_row = QHBoxLayout()
        alg_row.addWidget(self.alg_nn)
        alg_row.addWidget(self.alg_hc)
        alg_row.addWidget(self.alg_sa)
        alg_row.addWidget(self.alg_ga)

        self.seed = QSpinBox()
        self.seed.setRange(0, 10_000)
        self.seed.setValue(42)
        self.repeats = QSpinBox()
        self.repeats.setRange(1, 20)
        self.repeats.setValue(1)
        self.custom_sizes = QLineEdit()
        self.custom_sizes.setPlaceholderText("e.g., 12,15,18")

        btn_run = QPushButton("Run benchmark")
        btn_run.setObjectName("Accent")
        btn_run.clicked.connect(self._run)
        btn_export = QPushButton("Export CSV")
        btn_export.clicked.connect(self._export_csv)
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self._cancel)

        layout.addRow("Suite", self.suite)
        layout.addRow("Algorithms", alg_row)
        layout.addRow("Seed", self.seed)
        layout.addRow("Repeats", self.repeats)
        layout.addRow("Custom sizes", self.custom_sizes)
        layout.addRow(btn_run, btn_export)
        layout.addRow("Progress", self.progress)
        layout.addRow(self.btn_cancel)
        group.setLayout(layout)
        return group

    def _build_table(self) -> QGroupBox:
        group = CardFrame()
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        group.setLayout(layout)
        return group

    def _build_plots(self) -> QGroupBox:
        group = CardFrame()
        layout = QHBoxLayout()
        self.canvas_runtime = MplCanvas()
        self.canvas_cost = MplCanvas()
        self.canvas_gap = MplCanvas()
        layout.addWidget(self.canvas_runtime)
        layout.addWidget(self.canvas_cost)
        layout.addWidget(self.canvas_gap)
        group.setLayout(layout)
        return group

    def _get_algorithms(self) -> List[str]:
        algs = []
        if self.alg_nn.isChecked():
            algs.append("nn")
        if self.alg_hc.isChecked():
            algs.append("hc")
        if self.alg_sa.isChecked():
            algs.append("sa")
        if self.alg_ga.isChecked():
            algs.append("ga")
        return algs

    def _run(self) -> None:
        if self.current_worker:
            QMessageBox.information(self, "Busy", "A benchmark is already running.")
            return
        algs = self._get_algorithms()
        sizes = None
        if self.suite.currentText() == "custom":
            sizes = [int(x.strip()) for x in self.custom_sizes.text().split(",") if x.strip()]
        worker = CancelableWorker(
            run_tsp_benchmark_worker,
            self.suite.currentText(),
            algs,
            int(self.seed.value()),
            int(self.repeats.value()),
            sizes,
            None,
        )
        worker.signals.result.connect(self._on_result)
        worker.signals.error.connect(self._on_error)
        worker.signals.progress.connect(self._on_progress)
        worker.signals.finished.connect(self._on_finished)
        self.current_worker = worker
        self.progress.setRange(0, 0)
        self.thread_pool.start(worker)

    def _on_result(self, df: pd.DataFrame) -> None:
        self.results = df
        self._update_table(df)
        self._update_plots(df)
        self._auto_save(df)
    def _on_progress(self, current: int, total: int) -> None:
        self.progress.setRange(0, total)
        self.progress.setValue(current)

    def _on_finished(self) -> None:
        self.progress.setRange(0, 1)
        self.progress.setValue(1)
        self.current_worker = None


    def _update_table(self, df: pd.DataFrame) -> None:
        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(list(df.columns))
        for i, row in df.iterrows():
            for j, col in enumerate(df.columns):
                item = QTableWidgetItem(str(row[col]))
                self.table.setItem(i, j, item)
        self.table.resizeColumnsToContents()

    def _update_plots(self, df: pd.DataFrame) -> None:
        self.canvas_runtime.figure = plot_runtime_vs_n(df)
        self.canvas_runtime.sync_figure_size()
        self.canvas_runtime.draw()
        self.canvas_cost.figure = plot_cost_vs_n(df)
        self.canvas_cost.sync_figure_size()
        self.canvas_cost.draw()
        if "gap_pct" in df.columns:
            self.canvas_gap.figure = plot_gap_vs_n(df)
            self.canvas_gap.sync_figure_size()
            self.canvas_gap.draw()

    def _auto_save(self, df: pd.DataFrame) -> None:
        figures = {
            "runtime_vs_n": plot_runtime_vs_n(df),
            "runtime_vs_n_log": plot_runtime_vs_n_log(df),
            "cost_vs_n": plot_cost_vs_n(df),
        }
        if df["gap_pct"].notna().any():
            figures["gap_vs_n"] = plot_gap_vs_n(df)
        result = ExperimentResult(
            run_type="tsp",
            task="benchmark",
            metrics=df.to_dict(orient="records"),
            summary={"suite": self.suite.currentText(), "rows": len(df)},
        )
        self.run_service.save_run(
            prefix=f"tsp_bench_{self.suite.currentText()}",
            config={
                "suite": self.suite.currentText(),
                "algorithms": self._get_algorithms(),
                "seed": int(self.seed.value()),
                "repeats": int(self.repeats.value()),
            },
            result=result,
            figures=figures,
        )

    def _export_csv(self) -> None:
        if self.results is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "results.csv", "CSV Files (*.csv)")
        if path:
            self.results.to_csv(path, index=False)

    def _on_error(self, message: str) -> None:
        logger.error(message)
        QMessageBox.critical(self, "Error", "Benchmark failed.")

    def _cancel(self) -> None:
        if self.current_worker:
            self.current_worker.cancel()
