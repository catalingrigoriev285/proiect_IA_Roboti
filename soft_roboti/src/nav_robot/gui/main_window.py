"""Fereastra principala: taburi in stanga, configurari in dreapta, log jos."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QSplitter, QStatusBar, QTabWidget, QWidget

from nav_robot.gui.log_widget import LogWidget
from nav_robot.gui.tabs.algorithm_tab import AlgorithmTab
from nav_robot.gui.tabs.map_tab import MapTab
from nav_robot.gui.tabs.rl_tab import RLTab

log = logging.getLogger("gui.main")


class MainWindow(QMainWindow):
    """Layout:

        +------+------+----------------------------+
        | Tab1 | Tab2 |                            |
        +------+------+----------------------------+
        |                                          |
        |        Continut tab (configurari)        |
        |                                          |
        +------------------------------------------+
        |     Panou log (intreaga latime, jos)     |
        +------------------------------------------+
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("nav_robot - Planificare traseu Pioneer P3-DX")
        self.resize(1280, 800)
        self.setMinimumSize(800, 500)
        self._build_ui()
        log.info("GUI pornit. Selecteaza un tab pentru a incepe.")

    def _build_ui(self) -> None:
        # --- Tab-uri ---
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.setDocumentMode(True)
        self.tabs.setStyleSheet(
            "QTabBar::tab { padding: 8px 18px; font-weight: 500; }"
            "QTabBar::tab:selected { background:#3498db; color:white; }"
        )

        self.tab_map = MapTab(self)
        self.tab_algo = AlgorithmTab(map_tab=self.tab_map, parent=self)
        self.tab_rl = RLTab(map_tab=self.tab_map, parent=self)

        self.tabs.addTab(self.tab_map, "1. Generare harta")
        self.tabs.addTab(self.tab_algo, "2. Algoritmi")
        self.tabs.addTab(self.tab_rl, "3. Reinforcement Learning")

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
