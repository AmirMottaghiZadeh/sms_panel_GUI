from __future__ import annotations

import math

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QIntValidator
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QToolButton,
    QWidget,
)

_GSM7 = frozenset(
    "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ\x1bÆæßÉ "
    "!\"#¤%&'()*+,-./0123456789:;<=>?"
    "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜabcdefghijklmnopqrstuvwxyzäöñüà§¿"
)


class CardFrame(QFrame):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setFrameShape(QFrame.Shape.NoFrame)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(26)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 36))
        self.setGraphicsEffect(shadow)


class ClickableCardFrame(CardFrame):
    clicked = pyqtSignal()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def mousePressEvent(self, event) -> None:  # noqa: ANN001
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


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


class SelectComboBox(QComboBox):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        hand_cursor = QCursor(Qt.CursorShape.PointingHandCursor)
        self.setCursor(hand_cursor)
        self.setMaxVisibleItems(12)
        self.view().setCursor(hand_cursor)

    def mousePressEvent(self, event) -> None:  # noqa: ANN001
        if event.button() == Qt.MouseButton.LeftButton:
            self.showPopup()
            event.accept()
            return
        super().mousePressEvent(event)

    def wheelEvent(self, event) -> None:  # noqa: ANN001
        event.ignore()


class NumericLineEdit(QLineEdit):
    def __init__(self, min_value: int, max_value: int, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._min_value = min_value
        self._max_value = max_value
        self.setValidator(QIntValidator(min_value, max_value, self))
        self.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def numeric_value(self, fallback: int) -> int:
        text = self.text().strip()
        if not text:
            return fallback
        try:
            value = int(text)
        except ValueError:
            return fallback
        return max(self._min_value, min(self._max_value, value))

    def set_numeric_value(self, value: int) -> None:
        bounded = max(self._min_value, min(self._max_value, int(value)))
        self.setText(str(bounded))


class SmsCharCounter(QLabel):
    def __init__(self, editor: QPlainTextEdit, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._editor = editor
        editor.textChanged.connect(self._refresh)
        self.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.setProperty("class", "sms-counter")
        self._refresh()

    def _refresh(self) -> None:
        text = self._editor.toPlainText()
        length = len(text)
        is_unicode = any(c not in _GSM7 for c in text)
        single = 70 if is_unicode else 160
        multi = 67 if is_unicode else 153
        encoding = "Unicode" if is_unicode else "GSM-7"

        if length == 0:
            self.setText(f"۰ کاراکتر | {encoding}")
            return

        if length <= single:
            parts = 1
            remaining = single - length
        else:
            parts = math.ceil(length / multi)
            remaining = parts * multi - length

        self.setText(f"{length} کاراکتر | {remaining} باقیمانده | {parts} پیامک | {encoding}")


class ToastNotification(QLabel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._begin_fade)

        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        self._effect.setOpacity(1.0)

        self._anim = QPropertyAnimation(self._effect, b"opacity", self)
        self._anim.setDuration(450)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.finished.connect(self.hide)

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hide()

    def show_toast(self, message: str, level: str = "ok", duration_ms: int = 2800) -> None:
        self._timer.stop()
        self._anim.stop()
        self._effect.setOpacity(1.0)
        self.setText(message)
        self.setProperty("class", f"toast-{level}")
        self.style().unpolish(self)
        self.style().polish(self)
        self.adjustSize()
        self._reposition()
        self.show()
        self.raise_()
        self._timer.start(duration_ms)

    def _begin_fade(self) -> None:
        self._anim.start()

    def _reposition(self) -> None:
        p = self.parent()
        if p is None:
            return
        self.adjustSize()
        x = (p.width() - self.width()) // 2
        y = p.height() - self.height() - 32
        self.move(x, y)


def autosize_table_columns(
    table: QTableWidget,
    *,
    min_width: int = 90,
    max_width: int = 420,
    stretch_columns: tuple[int, ...] = (),
) -> None:
    header = table.horizontalHeader()
    if header is None:
        return

    for column in range(table.columnCount()):
        header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)

    table.resizeColumnsToContents()

    for column in range(table.columnCount()):
        width = max(min_width, min(max_width, header.sectionSize(column)))
        header.setSectionResizeMode(column, QHeaderView.ResizeMode.Interactive)
        header.resizeSection(column, width)

    for column in stretch_columns:
        if 0 <= column < table.columnCount():
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Stretch)
