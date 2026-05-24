"""QApplication entry point for the GUI."""

from __future__ import annotations

import sys

from PySide2.QtWidgets import QApplication

from tsp_ai.gui.main_window import MainWindow
from tsp_ai.gui.theme import apply_theme


def main() -> None:
    """Launch the GUI application."""
    app = QApplication(sys.argv)
    apply_theme(app, dark=True)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
