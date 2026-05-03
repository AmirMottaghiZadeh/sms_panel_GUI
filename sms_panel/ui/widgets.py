from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QCursor, QIntValidator
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QToolButton,
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


def autosize_table_columns(
    table: QTableWidget,
    *,
    min_width: int = 90,
    max_width: int = 420,
    stretch_columns: tuple[int, ...] = (),
) -> None:
    """Resize table columns by header/content length and keep long text readable."""
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
