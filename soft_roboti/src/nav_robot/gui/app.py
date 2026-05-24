"""Entry-point GUI: instantiaza QApplication si afiseaza MainWindow."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from nav_robot.gui.main_window import MainWindow


def main(argv: list[str] | None = None) -> int:
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("nav_robot")
    app.setOrganizationName("IA-2025-2026")

    window = MainWindow()
    window.resize(1100, 750)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
