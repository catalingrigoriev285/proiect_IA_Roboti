"""Worker thread generic pentru operatii lente (CoppeliaSim, planificare).

Important - thread safety:
    Cand un signal Qt este conectat la o functie Python obisnuita (nu un slot
    al unui QObject), Qt nu poate determina thread-ul receptorului si foloseste
    DirectConnection - callable-ul ruleaza in thread-ul emitatorului (= thread-ul
    worker-ului). Daca acel callable atinge widget-uri, apare "Cannot create
    children for a parent that is in a different thread".

    Solutia este sa creezi un QObject "relay" parintele caruia este in thread-ul
    GUI; conectezi worker.finished la metoda relay-ului cu QueuedConnection.
    Slotul relay-ului ruleaza in thread-ul parintelui (GUI) si poate chema in
    siguranta callable-ul Python care atinge UI.
"""

from __future__ import annotations

import logging
import traceback
from typing import Any, Callable

from PySide6.QtCore import QObject, Qt, QThread, Signal, Slot


class Worker(QObject):
    """Ruleaza o functie sincrona in background si emite rezultatul prin signal."""

    finished = Signal(object)   # rezultatul functiei
    failed = Signal(str)        # mesaj de eroare

    def __init__(self, fn: Callable[..., Any], *args, **kwargs) -> None:
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    @Slot()
    def run(self) -> None:
        log = logging.getLogger("gui.worker")
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            log.error("Eroare in worker: %s\n%s", e, traceback.format_exc())
            self.failed.emit(f"{type(e).__name__}: {e}")


class _Relay(QObject):
    """Trampolina QObject pentru a forta executia callback-ului in thread-ul GUI."""

    def __init__(self, parent: QObject, fn: Callable[[Any], None]) -> None:
        super().__init__(parent)
        self._fn = fn

    @Slot(object)
    def call(self, arg: Any) -> None:
        try:
            self._fn(arg)
        except Exception:
            logging.getLogger("gui.relay").exception("Eroare in callback GUI:")


def run_async(parent: QObject, fn: Callable[..., Any],
              on_done: Callable[[Any], None] | None = None,
              on_fail: Callable[[str], None] | None = None,
              *args, **kwargs) -> tuple[QThread, Worker]:
    """Lanseaza fn(*args, **kwargs) intr-un QThread.

    on_done si on_fail SUNT INVOCATE IN THREAD-UL parent-ului (GUI), gratie
    relay-urilor cu QueuedConnection.
    """
    thread = QThread(parent)
    worker = Worker(fn, *args, **kwargs)
    worker.moveToThread(thread)

    thread.started.connect(worker.run)

    # Relay-uri: traiesc in thread-ul parent-ului, deci slotul lor ruleaza acolo
    relays: list[_Relay] = []
    if on_done is not None:
        r = _Relay(parent, on_done)
        relays.append(r)
        worker.finished.connect(r.call, Qt.ConnectionType.QueuedConnection)
    if on_fail is not None:
        r = _Relay(parent, on_fail)
        relays.append(r)
        worker.failed.connect(r.call, Qt.ConnectionType.QueuedConnection)

    # Lifecycle: cand worker termina, opreste thread-ul, apoi curata
    worker.finished.connect(thread.quit)
    worker.failed.connect(thread.quit)
    thread.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    # Pastreaza referintele la relay-uri pana se distruge thread-ul
    thread.finished.connect(lambda: [r.deleteLater() for r in relays])

    thread.start()
    return thread, worker
