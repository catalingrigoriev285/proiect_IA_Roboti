"""Main GUI window with sidebar navigation."""

from __future__ import annotations

from pathlib import Path

from PySide2.QtCore import Qt, QUrl
from PySide2.QtGui import QDesktopServices
from PySide2.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from tsp_ai.gui.tabs.nlp_experiments_tab import NlpExperimentsTab
from tsp_ai.gui.tabs.outputs_viewer_tab import OutputsViewerTab
from tsp_ai.gui.tabs.tsp_benchmarks_tab import TspBenchmarksTab
from tsp_ai.gui.tabs.tsp_solver_tab import TspSolverTab
from tsp_ai.gui.theme import apply_theme
from tsp_ai.gui.widgets.card import CardFrame


class MainWindow(QMainWindow):
    """Main window with sidebar navigation."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("INTELIGENTA ARTIFICIALA 2025-2026")
        self.setMinimumSize(1280, 780)

        root = QWidget()
        root_layout = QHBoxLayout()
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(16)
        root.setLayout(root_layout)

        self.sidebar = CardFrame()
        self.sidebar.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(12, 16, 12, 16)
        sidebar_layout.setSpacing(10)
        self.sidebar.setLayout(sidebar_layout)

        title = QLabel("AI 2025-2026")
        title.setObjectName("Title")
        subtitle = QLabel("Optimization & NLP Lab")
        subtitle.setObjectName("SectionHeader")
        sidebar_layout.addWidget(title)
        sidebar_layout.addWidget(subtitle)

        self.btn_solver = self._nav_button("TSP Solver", QStyle.SP_ArrowRight)
        self.btn_bench = self._nav_button("TSP Benchmarks", QStyle.SP_ArrowUp)
        self.btn_nlp = self._nav_button("NLP", QStyle.SP_FileDialogInfoView)
        self.btn_outputs = self._nav_button("Outputs", QStyle.SP_DirOpenIcon)
        self.btn_settings = self._nav_button("Settings/About", QStyle.SP_FileDialogDetailedView)

        for btn in [self.btn_solver, self.btn_bench, self.btn_nlp, self.btn_outputs, self.btn_settings]:
            sidebar_layout.addWidget(btn)
        sidebar_layout.addStretch(1)

        self.stack = QStackedWidget()
        self.stack.addWidget(TspSolverTab(self))
        self.stack.addWidget(TspBenchmarksTab(self))
        self.stack.addWidget(NlpExperimentsTab(self))
        self.stack.addWidget(OutputsViewerTab(self))
        self.stack.addWidget(self._build_settings_page())

        content_layout = QVBoxLayout()
        content_layout.setSpacing(12)
        content_layout.addWidget(self._build_top_bar())
        content_layout.addWidget(self.stack)

        content = QWidget()
        content.setLayout(content_layout)

        root_layout.addWidget(self.sidebar, 1)
        root_layout.addWidget(content, 5)
        self.setCentralWidget(root)

        self._wire_nav()

    def _nav_button(self, text: str, icon: QStyle.StandardPixmap) -> QPushButton:
        btn = QPushButton(text)
        btn.setIcon(self.style().standardIcon(icon))
        btn.setCursor(Qt.PointingHandCursor)
        return btn

    def _wire_nav(self) -> None:
        self.btn_solver.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.btn_bench.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.btn_nlp.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        self.btn_outputs.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        self.btn_settings.clicked.connect(lambda: self.stack.setCurrentIndex(4))

    def _build_top_bar(self) -> QWidget:
        bar = CardFrame()
        layout = QHBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        title = QLabel("INTELIGENTA ARTIFICIALA 2025-2026")
        title.setObjectName("Title")
        layout.addWidget(title)
        layout.addStretch(1)

        self.theme_toggle = QToolButton()
        self.theme_toggle.setText("Toggle theme")
        self.theme_toggle.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.theme_toggle.clicked.connect(self._toggle_theme)
        layout.addWidget(self.theme_toggle)

        open_outputs = QPushButton("Open outputs")
        open_outputs.setObjectName("Accent")
        open_outputs.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        open_outputs.clicked.connect(self._open_outputs)
        layout.addWidget(open_outputs)

        bar.setLayout(layout)
        return bar


    def _build_settings_page(self) -> QWidget:
        card = CardFrame()
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        title = QLabel("Settings & About")
        title.setObjectName("Title")
        desc = QLabel(
            "This app supports TSP optimization and NLP experiments. "
            "Use the sidebar to navigate between modules."
        )
        desc.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addStretch(1)
        card.setLayout(layout)
        return card

    def _toggle_theme(self) -> None:
        app = QApplication.instance()
        if app is None:
            return
        dark = app.property("theme") != "light"
        apply_theme(app, dark=not dark)

    def _open_outputs(self) -> None:
        outputs = Path("outputs/runs").resolve()
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(outputs)))
