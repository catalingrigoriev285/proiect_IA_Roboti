"""Fereastra principala: taburi in stanga, configurari in dreapta, log jos."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QSplitter, QStatusBar, QTabWidget, QWidget

from nav_robot.gui.log_widget import LogWidget
from nav_robot.gui.tabs.algorithm_tab import AlgorithmTab
from nav_robot.gui.tabs.map_tab import MapTab

log = logging.getLogger("gui.main")


class MainWindow(QMainWindow):
    """Layout:

        +-----+------------------------------------+
        | T   |  Continut tab (configurari)        |
        | A   |                                    |
        | B   |                                    |
        | S   |                                    |
        +-----+------------------------------------+
        |   Panou log (intreaga latime, jos)       |
        +-----+------------------------------------+

    Tab-urile sunt afisate cu textul orientat vertical pe partea stanga
    (`QTabWidget.West`).
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("nav_robot - Planificare traseu Pioneer P3-DX")
        self._build_ui()
        log.info("GUI pornit. Selecteaza un tab pentru a incepe.")

    def _build_ui(self) -> None:
        # --- Tab-uri ---
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.West)
        self.tabs.setDocumentMode(True)

        self.tab_map = MapTab(self)
        self.tab_algo = AlgorithmTab(map_tab=self.tab_map, parent=self)

        self.tabs.addTab(self.tab_map, "1. Generare harta")
        self.tabs.addTab(self.tab_algo, "2. Algoritmi")

        # --- Log jos ---
        self.log_widget = LogWidget(self)

        # --- Splitter vertical ---
        splitter = QSplitter(Qt.Orientation.Vertical, self)
        splitter.addWidget(self.tabs)
        splitter.addWidget(self.log_widget)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([550, 200])

        self.setCentralWidget(splitter)

        bar = QStatusBar()
        bar.showMessage("Gata.")
        self.setStatusBar(bar)
