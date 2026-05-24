"""Worker base classes for background execution."""

from __future__ import annotations

import traceback
from typing import Any, Callable

from PySide2.QtCore import QObject, QRunnable, Signal


class WorkerSignals(QObject):
    """Signals available from a running worker."""

    result = Signal(object)
    error = Signal(str)
    progress = Signal(int, int)
    status = Signal(str)
    finished = Signal()


class Worker(QRunnable):
    """QRunnable that executes a callable and emits signals."""

    def __init__(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self) -> None:
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.result.emit(result)
        except Exception:
            self.signals.error.emit(traceback.format_exc())
        finally:
            self.signals.finished.emit()


class CancelableWorker(QRunnable):
    """QRunnable with cancellation and progress callbacks."""

    def __init__(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self._cancelled = False

    def cancel(self) -> None:
        """Request cancellation of the worker."""
        self._cancelled = True

    def _cancel_cb(self) -> bool:
        return self._cancelled

    def _progress_cb(self, current: int, total: int) -> None:
        self.signals.progress.emit(current, total)

    def run(self) -> None:
        try:
            result = self.fn(*self.args, progress_cb=self._progress_cb, cancel_cb=self._cancel_cb, **self.kwargs)
            self.signals.result.emit(result)
        except Exception:
            self.signals.error.emit(traceback.format_exc())
        finally:
            self.signals.finished.emit()
