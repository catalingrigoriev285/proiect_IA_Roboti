"""Card widget helpers."""

from __future__ import annotations

from PySide2.QtWidgets import QFrame


class CardFrame(QFrame):
    """Styled QFrame acting as a card container."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Card")
