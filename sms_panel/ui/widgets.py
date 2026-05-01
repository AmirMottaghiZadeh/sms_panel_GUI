from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QCursor
from PyQt6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QLabel, QPushButton, QToolButton


class CardFrame(QFrame):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setFrameShape(QFrame.Shape.NoFrame)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(26)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 36))
        self.setGraphicsEffect(shadow)


class NavButton(QToolButton):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(42)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)


class PrimaryButton(QPushButton):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(38)


class SecondaryButton(QPushButton):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(36)


class StatusBadge(QLabel):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(30)
