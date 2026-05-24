"""Worker thread generic pentru operatii lente (CoppeliaSim, generare hari mari)."""

from __future__ import annotations

import logging
import traceback
from typing import Any, Callable

from PySide6.QtCore import QObject, QThread, Signal


class Worker(QObject):
    """Ruleaza o functie sincrona in background si emite rezultatul prin signal."""

    finished = Signal(object)   # rezultatul functiei
    failed = Signal(str)        # mesaj de eroare

    def __init__(self, fn: Callable[..., Any], *args, **kwargs) -> None:
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self) -> None:
        log = logging.getLogger("gui.worker")
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            log.error("Eroare in worker: %s\n%s", e, traceback.format_exc())
            self.failed.emit(f"{type(e).__name__}: {e}")


def run_async(parent: QObject, fn: Callable[..., Any], on_done=None, on_fail=None,
              *args, **kwargs) -> tuple[QThread, Worker]:
    """Lanseaza fn(*args, **kwargs) intr-un QThread.

    Returneaza (thread, worker). Apelantul trebuie sa pastreze referintele live
    (de ex. ca atribut al unui widget) pana la `finished`/`failed`.
    """
    thread = QThread(parent)
    worker = Worker(fn, *args, **kwargs)
    worker.moveToThread(thread)

    thread.started.connect(worker.run)
    if on_done is not None:
        worker.finished.connect(on_done)
    if on_fail is not None:
        worker.failed.connect(on_fail)
    worker.finished.connect(thread.quit)
    worker.failed.connect(thread.quit)
    thread.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)

    thread.start()
    return thread, worker
