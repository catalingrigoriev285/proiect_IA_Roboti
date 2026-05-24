"""Matplotlib canvas wrapper for Qt."""

from __future__ import annotations

from typing import Optional

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide2.QtWidgets import QSizePolicy


class MplCanvas(FigureCanvas):
    """Simple matplotlib canvas for embedding in Qt widgets."""

    def __init__(self, fig: Optional[Figure] = None) -> None:
        if fig is None:
            fig = Figure(constrained_layout=True)
        self.figure = fig
        super().__init__(self.figure)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.updateGeometry()

    def resizeEvent(self, event) -> None:
        if self.figure is not None:
            dpi = self.figure.get_dpi() or 100
            self.figure.set_size_inches(self.width() / dpi, self.height() / dpi, forward=False)
        super().resizeEvent(event)
        self.draw_idle()

    def sync_figure_size(self) -> None:
        if self.figure is None:
            return
        dpi = self.figure.get_dpi() or 100
        width = max(self.width(), 1)
        height = max(self.height(), 1)
        self.figure.set_size_inches(width / dpi, height / dpi, forward=False)
