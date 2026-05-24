"""Widget de log + handler logging thread-safe."""

from __future__ import annotations

import logging
from datetime import datetime

from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget,
)


class _LogBridge(QObject):
    """Bridge thread-safe pentru a posta linii in QPlainTextEdit din alte thread-uri."""
    new_line = Signal(str)


_BRIDGE = _LogBridge()


class _QtSignalHandler(logging.Handler):
    """Logging handler care emite linii catre QPlainTextEdit prin signal."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            _BRIDGE.new_line.emit(msg)
        except Exception:
            self.handleError(record)


class LogWidget(QWidget):
    """Panou de log cu butoane Clear / Copy."""

    LEVEL_COLOR = {
        "DEBUG": "#888888",
        "INFO": "#dddddd",
        "WARNING": "#f1c40f",
        "ERROR": "#e74c3c",
        "CRITICAL": "#ff3030",
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._install_handler()

    def _build_ui(self) -> None:
        self.text = QPlainTextEdit(self)
        self.text.setReadOnly(True)
        font = QFont("Consolas")
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setPointSize(9)
        self.text.setFont(font)
        self.text.setStyleSheet(
            "QPlainTextEdit { background:#1e1e1e; color:#dddddd; "
            "border:1px solid #444; }"
        )

        self.btn_clear = QPushButton("Clear")
        self.btn_copy = QPushButton("Copiaza")
        self.btn_clear.clicked.connect(self.text.clear)
        self.btn_copy.clicked.connect(self._copy_all)

        bar = QHBoxLayout()
        bar.addWidget(self.btn_clear)
        bar.addWidget(self.btn_copy)
        bar.addStretch(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 4)
        layout.setSpacing(2)
        layout.addLayout(bar)
        layout.addWidget(self.text)

    def _install_handler(self) -> None:
        _BRIDGE.new_line.connect(self._append, Qt.ConnectionType.QueuedConnection)
        root = logging.getLogger()
        # Evitam dublarea daca widget-ul e re-creat
        if not any(isinstance(h, _QtSignalHandler) for h in root.handlers):
            handler = _QtSignalHandler()
            handler.setFormatter(logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%H:%M:%S",
            ))
            handler.setLevel(logging.DEBUG)
            root.addHandler(handler)
            root.setLevel(logging.INFO)

    @Slot(str)
    def _append(self, line: str) -> None:
        level = self._extract_level(line)
        color = self.LEVEL_COLOR.get(level, "#dddddd")
        safe = (line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        html = f'<span style="color:{color}">{safe}</span>'
        self.text.appendHtml(html)
        self.text.moveCursor(QTextCursor.MoveOperation.End)

    @staticmethod
    def _extract_level(line: str) -> str:
        # formatul este "HH:MM:SS [LEVEL] ..."
        try:
            start = line.index("[")
            end = line.index("]", start)
            return line[start + 1:end]
        except ValueError:
            return "INFO"

    def _copy_all(self) -> None:
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.text.toPlainText())

    # API direct (pentru cazuri unde nu vrem logger): plain text colorat ca INFO
    def write_line(self, text: str) -> None:
        line = f"{datetime.now().strftime('%H:%M:%S')} [INFO] gui: {text}"
        _BRIDGE.new_line.emit(line)
