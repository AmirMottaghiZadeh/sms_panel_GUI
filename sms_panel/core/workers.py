from __future__ import annotations

from typing import Any, Callable

from PyQt6.QtCore import QObject, QRunnable, pyqtSignal


class WorkerSignals(QObject):
    finished = pyqtSignal(object, object)


class ApiWorker(QRunnable):
    def __init__(self, fn: Callable[[], Any]) -> None:
        super().__init__()
        self.fn = fn
        self.signals = WorkerSignals()

    def run(self) -> None:
        try:
            result = self.fn()
            try:
                self.signals.finished.emit(result, None)
            except RuntimeError:
                pass
        except Exception as exc:
            try:
                self.signals.finished.emit(None, exc)
            except RuntimeError:
                pass
