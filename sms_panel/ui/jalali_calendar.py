from __future__ import annotations

import jdatetime
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from sms_panel.ui.widgets import SecondaryButton

WEEKDAY_LABELS = ["ش", "ی", "د", "س", "چ", "پ", "ج"]


class JalaliCalendarDialog(QDialog):
    def __init__(self, initial_date: jdatetime.date | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("انتخاب تاریخ شمسی")
        self.setModal(True)
        self.setMinimumWidth(390)

        self._selected = initial_date or jdatetime.date.today()
        self._view_year = self._selected.year
        self._view_month = self._selected.month

        root = QVBoxLayout(self)

        header = QHBoxLayout()
        prev_button = SecondaryButton("ماه قبل")
        prev_button.clicked.connect(lambda: self._change_month(-1))

        self.month_title = QLabel("")
        self.month_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.month_title.setProperty("class", "fa-subtitle")

        next_button = SecondaryButton("ماه بعد")
        next_button.clicked.connect(lambda: self._change_month(1))

        header.addWidget(prev_button)
        header.addWidget(self.month_title, 1)
        header.addWidget(next_button)
        root.addLayout(header)

        weekdays_row = QHBoxLayout()
        for label in WEEKDAY_LABELS:
            item = QLabel(label)
            item.setAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setProperty("class", "fa-note")
            weekdays_row.addWidget(item)
        root.addLayout(weekdays_row)

        self.day_rows: list[QHBoxLayout] = []
        self.day_buttons: list[SecondaryButton] = []
        for _ in range(6):
            row = QHBoxLayout()
            row.setSpacing(4)
            self.day_rows.append(row)
            root.addLayout(row)
            for _ in range(7):
                day_button = SecondaryButton("")
                day_button.setCheckable(True)
                day_button.setMinimumHeight(34)
                day_button.clicked.connect(self._pick_day)
                self.day_buttons.append(day_button)
                row.addWidget(day_button)

        action_row = QHBoxLayout()
        today_button = SecondaryButton("امروز")
        today_button.clicked.connect(self._pick_today)
        close_button = SecondaryButton("انصراف")
        close_button.clicked.connect(self.reject)

        action_row.addWidget(today_button)
        action_row.addStretch(1)
        action_row.addWidget(close_button)
        root.addLayout(action_row)

        self._render_calendar()

    def selected_date(self) -> jdatetime.date:
        return self._selected

    def _change_month(self, step: int) -> None:
        month = self._view_month + step
        year = self._view_year
        if month > 12:
            year += 1
            month = 1
        elif month < 1:
            year -= 1
            month = 12

        self._view_year = year
        self._view_month = month
        self._render_calendar()

    def _pick_today(self) -> None:
        self._selected = jdatetime.date.today()
        self.accept()

    def _pick_day(self) -> None:
        sender = self.sender()
        if not isinstance(sender, SecondaryButton):
            return
        day = sender.property("day")
        if not isinstance(day, int):
            return

        self._selected = jdatetime.date(self._view_year, self._view_month, day)
        self.accept()

    def _month_days(self, year: int, month: int) -> int:
        if month <= 6:
            return 31
        if month <= 11:
            return 30
        return 30 if jdatetime.date(year, 1, 1).isleap() else 29

    def _render_calendar(self) -> None:
        month_name = jdatetime.date.j_months_fa[self._view_month - 1]
        self.month_title.setText(f"{month_name} {self._view_year}")

        for button in self.day_buttons:
            button.setText("")
            button.setEnabled(False)
            button.setVisible(False)
            button.setProperty("day", None)

        first_day = jdatetime.date(self._view_year, self._view_month, 1).togregorian().weekday()
        start_index = (first_day + 2) % 7
        day_count = self._month_days(self._view_year, self._view_month)

        for day in range(1, day_count + 1):
            button_index = start_index + day - 1
            if not (0 <= button_index < len(self.day_buttons)):
                continue
            button = self.day_buttons[button_index]
            button.setVisible(True)
            button.setEnabled(True)
            button.setText(str(day))
            button.setProperty("day", day)

            is_selected = (
                self._selected.year == self._view_year
                and self._selected.month == self._view_month
                and self._selected.day == day
            )
            button.setChecked(False)
            if is_selected:
                button.setChecked(True)


class JalaliDateField(QWidget):
    def __init__(self, *, placeholder_text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._selected: jdatetime.date | None = None

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        self.input = QLineEdit()
        self.input.setReadOnly(True)
        self.input.setPlaceholderText(placeholder_text or "انتخاب تاریخ شمسی")

        self.open_button = SecondaryButton("تقویم")
        self.open_button.clicked.connect(self._open_calendar)

        clear_button = SecondaryButton("پاک")
        clear_button.clicked.connect(self.clear)

        row.addWidget(self.input, 1)
        row.addWidget(self.open_button)
        row.addWidget(clear_button)

    def _open_calendar(self) -> None:
        dialog = JalaliCalendarDialog(initial_date=self._selected or jdatetime.date.today(), parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self.set_date(dialog.selected_date())

    def set_date(self, date_value: jdatetime.date) -> None:
        self._selected = date_value
        self.input.setText(self._selected.strftime("%Y/%m/%d"))

    def clear(self) -> None:
        self._selected = None
        self.input.clear()

    def jalali_text(self) -> str:
        if self._selected is None:
            return ""
        return self._selected.strftime("%Y/%m/%d")

    def gregorian_iso(self) -> str:
        if self._selected is None:
            return ""
        return self._selected.togregorian().strftime("%Y-%m-%d")
