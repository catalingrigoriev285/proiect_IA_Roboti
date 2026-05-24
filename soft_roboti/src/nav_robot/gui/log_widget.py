"""Widget de log + handler logging thread-safe."""

from __future__ import annotations

import logging
from datetime import datetime

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget,
)


class _SignalEmitterHandler(logging.Handler):
    """Logging handler care emite linia formatata pe semnalul widget-ului.

    Conexiunea este `QueuedConnection`, deci postarea poate veni din orice thread
    iar slotul este invocat in thread-ul de UI (cel care detine widget-ul).
    """

    def __init__(self, target_widget: "LogWidget") -> None:
        super().__init__()
        self._target = target_widget

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
        except Exception:
            self.handleError(record)
            return
        # signal.emit este thread-safe; cu QueuedConnection apelarea slotului
        # este re-postata in thread-ul widget-ului.
        try:
            self._target.line_logged.emit(msg)
        except RuntimeError:
            # Widget-ul a fost distrus inainte ca handler-ul sa fie scos.
            pass


class LogWidget(QWidget):
    """Panou de log cu butoane Clear / Copy."""

    line_logged = Signal(str)

    LEVEL_COLOR = {
        "DEBUG": "#888888",
        "INFO": "#dddddd",
        "WARNING": "#f1c40f",
        "ERROR": "#e74c3c",
        "CRITICAL": "#ff3030",
    }

    _handlers_by_widget: dict[int, _SignalEmitterHandler] = {}

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        # IMPORTANT: queued connection -> slotul ruleaza in thread-ul widget-ului
        self.line_logged.connect(self._append, Qt.ConnectionType.QueuedConnection)
        self._install_handler()

    # ------------------------------------------------------------------
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
        # Evitam dublarea daca widget-ul e recreat
        root = logging.getLogger()
        wid = id(self)
        if wid in LogWidget._handlers_by_widget:
            return
        handler = _SignalEmitterHandler(self)
        handler.setFormatter(logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        ))
        handler.setLevel(logging.DEBUG)
        root.addHandler(handler)
        if root.level > logging.INFO or root.level == 0:
            root.setLevel(logging.INFO)
        LogWidget._handlers_by_widget[wid] = handler

    # ------------------------------------------------------------------
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
        try:
            start = line.index("[")
            end = line.index("]", start)
            return line[start + 1:end]
        except ValueError:
            return "INFO"

    def _copy_all(self) -> None:
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.text.toPlainText())

    def write_line(self, text: str) -> None:
        line = f"{datetime.now().strftime('%H:%M:%S')} [INFO] gui: {text}"
        self.line_logged.emit(line)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        # La distrugere, scoate handler-ul ca sa nu emita catre obiect zombie
        handler = LogWidget._handlers_by_widget.pop(id(self), None)
        if handler is not None:
            logging.getLogger().removeHandler(handler)
        super().closeEvent(event)
