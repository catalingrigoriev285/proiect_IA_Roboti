"""Outputs Viewer tab implementation."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import pandas as pd
from PySide2.QtCore import Qt, QUrl
from PySide2.QtGui import QDesktopServices, QPixmap
from PySide2.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from tsp_ai.common.run_registry import RunRegistry
from tsp_ai.gui.widgets.card import CardFrame

logger = logging.getLogger(__name__)


class OutputsViewerTab(QWidget):
    """Tab for browsing past runs and artifacts."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setSpacing(16)

        self.run_list = QListWidget()
        self.run_list.itemSelectionChanged.connect(self._on_select)

        self.config_view = QTextEdit()
        self.config_view.setReadOnly(True)
        self.results_table = QTableWidget()
        self.results_table.setAlternatingRowColors(True)
        self.plots_container = QVBoxLayout()
        self.summary_label = QLabel("Select a run to view details.")
        self.summary_label.setWordWrap(True)

        right = QVBoxLayout()
        right.setSpacing(12)

        summary_card = CardFrame()
        summary_layout = QVBoxLayout()
        summary_layout.setContentsMargins(16, 12, 16, 12)
        summary_layout.addWidget(QLabel("Summary"))
        summary_layout.addWidget(self.summary_label)
        summary_card.setLayout(summary_layout)

        config_card = CardFrame()
        config_layout = QVBoxLayout()
        config_layout.setContentsMargins(16, 12, 16, 12)
        config_layout.addWidget(QLabel("config.json"))
        config_layout.addWidget(self.config_view)
        config_card.setLayout(config_layout)

        results_card = CardFrame()
        results_layout = QVBoxLayout()
        results_layout.setContentsMargins(16, 12, 16, 12)
        results_layout.addWidget(QLabel("results.csv"))
        results_layout.addWidget(self.results_table)
        results_card.setLayout(results_layout)

        plots_card = CardFrame()
        plots_layout = QVBoxLayout()
        plots_layout.setContentsMargins(16, 12, 16, 12)
        plots_layout.addWidget(QLabel("plots"))
        plots_widget = QWidget()
        plots_widget.setLayout(self.plots_container)
        plots_layout.addWidget(plots_widget)
        plots_card.setLayout(plots_layout)

        self.btn_open = QPushButton("Open folder")
        self.btn_open.clicked.connect(self._open_folder)

        right.addWidget(summary_card)
        right.addWidget(config_card)
        right.addWidget(results_card)
        right.addWidget(plots_card)
        right.addWidget(self.btn_open)

        layout.addWidget(self.run_list, 1)
        right_widget = QWidget()
        right_widget.setLayout(right)
        layout.addWidget(right_widget, 3)
        self.setLayout(layout)

        self._load_runs()

    def _load_runs(self) -> None:
        self.run_list.clear()
        runs = RunRegistry.list_runs(Path("outputs/runs"))
        for run in runs:
            item = QListWidgetItem(run.name)
            item.setData(Qt.UserRole, run)
            self.run_list.addItem(item)

    def _on_select(self) -> None:
        items = self.run_list.selectedItems()
        if not items:
            return
        run_dir = items[0].data(Qt.UserRole)
        config_path = Path(run_dir) / "config.json"
        results_path = Path(run_dir) / "results.csv"
        plots_dir = Path(run_dir) / "plots"
        result_path = Path(run_dir) / "result.json"

        if config_path.exists():
            self.config_view.setPlainText(config_path.read_text(encoding="utf-8"))
        if results_path.exists():
            df = pd.read_csv(results_path)
            self._populate_table(df)
        if result_path.exists():
            self._populate_summary(result_path)
        self._populate_plots(plots_dir)

    def _populate_summary(self, result_path: Path) -> None:
        try:
            data = json.loads(result_path.read_text(encoding="utf-8"))
            summary = data.get("summary", {})
            parts = [f"{k}: {v}" for k, v in summary.items()]
            self.summary_label.setText(" | ".join(parts) if parts else "No summary available.")
        except Exception:
            self.summary_label.setText("No summary available.")

    def _populate_table(self, df: pd.DataFrame) -> None:
        self.results_table.setRowCount(len(df))
        self.results_table.setColumnCount(len(df.columns))
        self.results_table.setHorizontalHeaderLabels(list(df.columns))
        for i, row in df.iterrows():
            for j, col in enumerate(df.columns):
                self.results_table.setItem(i, j, QTableWidgetItem(str(row[col])))
        self.results_table.resizeColumnsToContents()

    def _populate_plots(self, plots_dir: Path) -> None:
        for i in reversed(range(self.plots_container.count())):
            widget = self.plots_container.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        if not plots_dir.exists():
            return
        for plot in plots_dir.glob("*.png"):
            label = QLabel()
            pix = QPixmap(str(plot))
            label.setScaledContents(True)
            label.setPixmap(pix)
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.plots_container.addWidget(label)

    def _open_folder(self) -> None:
        items = self.run_list.selectedItems()
        if not items:
            return
        run_dir = items[0].data(Qt.UserRole)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(run_dir)))
