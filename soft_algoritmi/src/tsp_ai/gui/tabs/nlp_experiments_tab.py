"""NLP tab implementation."""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from PySide2.QtCore import QThreadPool
from PySide2.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from tsp_ai.app.services.result_schema import ExperimentResult
from tsp_ai.app.services.run_service import RunService
from tsp_ai.gui.widgets.card import CardFrame
from tsp_ai.gui.widgets.mpl_canvas import MplCanvas
from tsp_ai.gui.workers.nlp_workers import run_lab10_task
from tsp_ai.gui.workers.worker_base import CancelableWorker
from tsp_ai.nlp.lab10 import DEFAULT_CATEGORIES
from tsp_ai.nlp.plots import plot_comparison_bars, plot_confusion_matrix, plot_heatmap

logger = logging.getLogger(__name__)


class NlpExperimentsTab(QWidget):
    """Tab for NLP experiments."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.thread_pool = QThreadPool.globalInstance()
        self.current_worker: Optional[CancelableWorker] = None
        self.run_service = RunService()

        layout = QHBoxLayout()
        layout.setSpacing(16)
        layout.addWidget(self._build_controls(), 2)
        layout.addWidget(self._build_output(), 3)
        self.setLayout(layout)

    def _build_controls(self) -> QWidget:
        card = CardFrame()
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel("NLP")
        header.setObjectName("Title")
        layout.addWidget(header)

        form = QFormLayout()
        self.task = QComboBox()
        self.task_options = [
            ("Naive Bayes baseline", "task1"),
            ("Compare classifiers", "task2"),
            ("N-gram range study", "task3"),
            ("Max features study", "task4"),
            ("Grid search (n-gram x max features)", "task5"),
        ]
        self.task.addItems([label for label, _ in self.task_options])
        form.addRow("Task", self.task)

        self.stop_words = QCheckBox("Use English stop words")
        self.stop_words.setChecked(True)
        self.sublinear = QCheckBox("Sublinear TF")
        self.sublinear.setChecked(True)
        form.addRow(self.stop_words)
        form.addRow(self.sublinear)

        self.ngram_min = QSpinBox()
        self.ngram_min.setRange(1, 3)
        self.ngram_min.setValue(1)
        self.ngram_max = QSpinBox()
        self.ngram_max.setRange(1, 3)
        self.ngram_max.setValue(2)
        form.addRow("Ngram min", self.ngram_min)
        form.addRow("Ngram max", self.ngram_max)

        self.max_features = QSpinBox()
        self.max_features.setRange(100, 50000)
        self.max_features.setValue(5000)
        self.max_features_none = QCheckBox("Max features = None")
        form.addRow("Max features", self.max_features)
        form.addRow(self.max_features_none)

        layout.addLayout(form)

        preset_group = QGroupBox("Experiment presets")
        preset_layout = QHBoxLayout()
        btn_preset_compare = QPushButton("Compare classifiers")
        btn_preset_compare.clicked.connect(lambda: self._set_task_code("task2"))
        btn_preset_grid = QPushButton("Grid heatmap")
        btn_preset_grid.clicked.connect(lambda: self._set_task_code("task5"))
        preset_layout.addWidget(btn_preset_compare)
        preset_layout.addWidget(btn_preset_grid)
        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)

        cats_group = QGroupBox("Categories")
        cats_layout = QVBoxLayout()
        self.cat_checks = []
        for cat in DEFAULT_CATEGORIES:
            cb = QCheckBox(cat)
            cb.setChecked(True)
            self.cat_checks.append(cb)
            cats_layout.addWidget(cb)
        cats_group.setLayout(cats_layout)
        layout.addWidget(cats_group)

        clf_group = QGroupBox("Classifiers (Task 2)")
        clf_layout = QHBoxLayout()
        self.clf_nb = QCheckBox("nb")
        self.clf_svm = QCheckBox("svm")
        self.clf_lr = QCheckBox("lr")
        self.clf_rf = QCheckBox("rf")
        for cb in [self.clf_nb, self.clf_svm, self.clf_lr, self.clf_rf]:
            cb.setChecked(True)
            clf_layout.addWidget(cb)
        clf_group.setLayout(clf_layout)
        layout.addWidget(clf_group)

        self.progress = QProgressBar()
        self.status = QLabel("Ready")
        self.btn_run = QPushButton("Run task")
        self.btn_run.setObjectName("Accent")
        self.btn_run.clicked.connect(self._run)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self._cancel)

        layout.addWidget(self.status)
        layout.addWidget(self.progress)
        layout.addWidget(self.btn_run)
        layout.addWidget(self.btn_cancel)
        layout.addStretch(1)

        card.setLayout(layout)
        return card

    def _build_output(self) -> QWidget:
        card = CardFrame()
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel("Results")
        header.setObjectName("Title")
        self.best_label = QLabel("Best model: -")
        layout.addWidget(header)
        layout.addWidget(self.best_label)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        plots = QHBoxLayout()
        self.canvas_cm = MplCanvas()
        self.canvas_bar = MplCanvas()
        self.canvas_heat = MplCanvas()
        plots.addWidget(self.canvas_cm)
        plots.addWidget(self.canvas_bar)
        plots.addWidget(self.canvas_heat)
        layout.addLayout(plots)

        card.setLayout(layout)
        return card

    def _selected_categories(self) -> List[str]:
        selected = [cb.text() for cb in self.cat_checks if cb.isChecked()]
        return selected if selected else DEFAULT_CATEGORIES

    def _selected_classifiers(self) -> List[str]:
        selected = []
        if self.clf_nb.isChecked():
            selected.append("nb")
        if self.clf_svm.isChecked():
            selected.append("svm")
        if self.clf_lr.isChecked():
            selected.append("lr")
        if self.clf_rf.isChecked():
            selected.append("rf")
        return selected

    def _current_task_code(self) -> str:
        index = self.task.currentIndex()
        if index < 0:
            return "task1"
        return self.task_options[index][1]

    def _set_task_code(self, code: str) -> None:
        for idx, (_, value) in enumerate(self.task_options):
            if value == code:
                self.task.setCurrentIndex(idx)
                return

    def _run(self) -> None:
        if self.current_worker:
            QMessageBox.information(self, "Busy", "A task is already running.")
            return
        ngram_range = (int(self.ngram_min.value()), int(self.ngram_max.value()))
        max_features = None if self.max_features_none.isChecked() else int(self.max_features.value())
        worker = CancelableWorker(
            run_lab10_task,
            self._current_task_code(),
            self._selected_categories(),
            ngram_range,
            max_features,
            self.stop_words.isChecked(),
            self.sublinear.isChecked(),
            classifiers=self._selected_classifiers(),
        )
        worker.signals.result.connect(self._on_result)
        worker.signals.error.connect(self._on_error)
        worker.signals.progress.connect(self._on_progress)
        worker.signals.finished.connect(self._on_finished)
        self.current_worker = worker
        self.status.setText("Running...")
        self.progress.setRange(0, 0)
        self.thread_pool.start(worker)

    def _on_progress(self, current: int, total: int) -> None:
        self.progress.setRange(0, total)
        self.progress.setValue(current)

    def _on_result(self, payload: dict) -> None:
        task = payload["task"]
        if task == "task1":
            metrics = payload["metrics"]
            self._populate_table([
                {"label": "nb", "accuracy": metrics["accuracy"], "train_time": metrics["train_time"]}
            ])
            self.best_label.setText("Best model: nb")
            self.canvas_cm.figure = plot_confusion_matrix(metrics["confusion_matrix"], "Confusion Matrix", "NB")
            self.canvas_cm.sync_figure_size()
            self.canvas_cm.draw()
            self._save_run_task1(metrics)
        elif task == "task2":
            rows = payload["results"]
            self._populate_table(
                [
                    {
                        "label": r["classifier"],
                        "accuracy": r["accuracy"],
                        "train_time": r["train_time"],
                    }
                    for r in rows
                ]
            )
            best = max(rows, key=lambda r: r["accuracy"])
            self.best_label.setText(f"Best model: {best['classifier']}")
            self.canvas_bar.figure = plot_comparison_bars(
                [
                    {"label": r["classifier"], "accuracy": r["accuracy"]}
                    for r in rows
                ],
                "Classifier Comparison",
            )
            self.canvas_bar.sync_figure_size()
            self.canvas_bar.draw()
            self._save_run_task2(rows)
        elif task == "task3":
            rows = payload["results"]
            self._populate_table(
                [
                    {"label": r["ngram_range"], "accuracy": r["accuracy"], "train_time": r["train_time"]}
                    for r in rows
                ]
            )
            self.canvas_bar.figure = plot_comparison_bars(
                [
                    {"label": r["ngram_range"], "accuracy": r["accuracy"]}
                    for r in rows
                ],
                "Ngram Study",
            )
            self.canvas_bar.sync_figure_size()
            self.canvas_bar.draw()
            self._save_run_task3(rows)
        elif task == "task4":
            rows = payload["results"]
            self._populate_table(
                [
                    {"label": r["max_features"], "accuracy": r["accuracy"], "train_time": r["train_time"]}
                    for r in rows
                ]
            )
            self.canvas_bar.figure = plot_comparison_bars(
                [
                    {"label": r["max_features"], "accuracy": r["accuracy"]}
                    for r in rows
                ],
                "Max Features Study",
            )
            self.canvas_bar.sync_figure_size()
            self.canvas_bar.draw()
            self._save_run_task4(rows)
        elif task == "task5":
            result = payload["result"]
            self.best_label.setText(
                f"Best model: ngram={result['best']['ngram_range']} max_features={result['best']['max_features']}"
            )
            self.canvas_heat.figure = plot_heatmap(
                result["grid"], result["max_features"], result["ngram_ranges"], "Grid Search"
            )
            self.canvas_heat.sync_figure_size()
            self.canvas_heat.draw()
            self._save_run_task5(result)

    def _populate_table(self, rows: List[dict]) -> None:
        if not rows:
            return
        headers = list(rows[0].keys())
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        for i, row in enumerate(rows):
            for j, key in enumerate(headers):
                self.table.setItem(i, j, QTableWidgetItem(str(row[key])))
        self.table.resizeColumnsToContents()

    def _save_run_task1(self, metrics: dict) -> None:
        result = ExperimentResult(
            run_type="nlp",
            task="lab10_task1",
            metrics=[{"model": "nb", "accuracy": metrics["accuracy"], "train_time": metrics["train_time"]}],
            summary={"best_model": "nb", "accuracy": metrics["accuracy"]},
        )
        self.run_service.save_run(
            prefix="nlp_lab10_task1",
            config={"task": "task1"},
            result=result,
            figures={"confusion_matrix": self.canvas_cm.figure},
            artifacts={"confusion_matrix": metrics["confusion_matrix"].tolist()},
        )

    def _save_run_task2(self, rows: List[dict]) -> None:
        best = max(rows, key=lambda r: r["accuracy"])
        result = ExperimentResult(
            run_type="nlp",
            task="lab10_task2",
            metrics=[
                {"model": r["classifier"], "accuracy": r["accuracy"], "train_time": r["train_time"]}
                for r in rows
            ],
            summary={"best_model": best["classifier"], "accuracy": best["accuracy"]},
        )
        self.run_service.save_run(
            prefix="nlp_lab10_task2",
            config={"task": "task2"},
            result=result,
            figures={"comparison": self.canvas_bar.figure},
            artifacts={"raw": rows},
        )

    def _save_run_task3(self, rows: List[dict]) -> None:
        result = ExperimentResult(
            run_type="nlp",
            task="lab10_task3",
            metrics=[
                {"ngram_range": r["ngram_range"], "accuracy": r["accuracy"], "train_time": r["train_time"]}
                for r in rows
            ],
        )
        self.run_service.save_run(
            prefix="nlp_lab10_task3",
            config={"task": "task3"},
            result=result,
            figures={"ngram_study": self.canvas_bar.figure},
            artifacts={"raw": rows},
        )

    def _save_run_task4(self, rows: List[dict]) -> None:
        result = ExperimentResult(
            run_type="nlp",
            task="lab10_task4",
            metrics=[
                {"max_features": r["max_features"], "accuracy": r["accuracy"], "train_time": r["train_time"]}
                for r in rows
            ],
        )
        self.run_service.save_run(
            prefix="nlp_lab10_task4",
            config={"task": "task4"},
            result=result,
            figures={"max_features": self.canvas_bar.figure},
            artifacts={"raw": rows},
        )

    def _save_run_task5(self, result_data: dict) -> None:
        result = ExperimentResult(
            run_type="nlp",
            task="lab10_task5",
            metrics=[
                {
                    "ngram_range": result_data["best"]["ngram_range"],
                    "max_features": result_data["best"]["max_features"],
                    "accuracy": result_data["best_accuracy"],
                }
            ],
            summary={"best_accuracy": result_data["best_accuracy"]},
        )
        self.run_service.save_run(
            prefix="nlp_lab10_task5",
            config={"task": "task5"},
            result=result,
            figures={"grid": self.canvas_heat.figure},
            artifacts={"grid": result_data},
        )

    def _on_error(self, message: str) -> None:
        logger.error(message)
        QMessageBox.critical(self, "Error", "Task failed.")

    def _on_finished(self) -> None:
        self.progress.setRange(0, 1)
        self.progress.setValue(1)
        self.status.setText("Done")
        self.current_worker = None

    def _cancel(self) -> None:
        if self.current_worker:
            self.current_worker.cancel()
            self.status.setText("Cancellation requested...")
