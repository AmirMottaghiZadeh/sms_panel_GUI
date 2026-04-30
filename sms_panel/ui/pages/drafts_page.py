from __future__ import annotations

from datetime import datetime
from typing import Any

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from sms_panel.ui.widgets import CardFrame, PrimaryButton, SecondaryButton


class DraftsPage(QWidget):
    drafts_changed = pyqtSignal(list)

    def __init__(self, drafts: list[dict[str, Any]]) -> None:
        super().__init__()
        self.drafts: list[dict[str, Any]] = [dict(item) for item in drafts]
        self.editing_index: int | None = None

        root = QVBoxLayout(self)
        title = QLabel("پیش نویس ها")
        title.setProperty("class", "fa-header")
        root.addWidget(title)

        helper = QLabel("برای هر پیش نویس یک عنوان و متن ذخیره کنید. بخش ویرایش پیش نویس ها از جدول پایین فعال می شود.")
        helper.setProperty("class", "fa-note")
        helper.setWordWrap(True)
        root.addWidget(helper)

        form_card = CardFrame()
        form_layout = QVBoxLayout(form_card)

        self.mode_label = QLabel("حالت: افزودن پیش نویس جدید")
        self.mode_label.setProperty("class", "fa-note")
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("عنوان پیش نویس")
        self.message_input = QPlainTextEdit()
        self.message_input.setPlaceholderText("متن پیش نویس")
        self.message_input.setMaximumHeight(150)

        buttons_row = QHBoxLayout()
        save_button = PrimaryButton("افزودن پیش نویس")
        save_button.clicked.connect(self._add_draft)
        edit_button = SecondaryButton("ویرایش پیش نویس انتخاب شده")
        edit_button.clicked.connect(self._load_selected_for_edit)
        apply_edit_button = PrimaryButton("ثبت ویرایش")
        apply_edit_button.clicked.connect(self._apply_edit)
        cancel_edit_button = SecondaryButton("لغو ویرایش")
        cancel_edit_button.clicked.connect(self._cancel_edit)
        delete_button = SecondaryButton("حذف انتخاب شده")
        delete_button.clicked.connect(self._delete_selected)
        clear_button = SecondaryButton("پاکسازی فرم")
        clear_button.clicked.connect(self._clear_form)

        buttons_row.addWidget(save_button)
        buttons_row.addWidget(edit_button)
        buttons_row.addWidget(apply_edit_button)
        buttons_row.addWidget(cancel_edit_button)
        buttons_row.addWidget(delete_button)
        buttons_row.addWidget(clear_button)

        form_layout.addWidget(self.mode_label)
        form_layout.addWidget(self.title_input)
        form_layout.addWidget(self.message_input)
        form_layout.addLayout(buttons_row)

        root.addWidget(form_card)

        table_card = CardFrame()
        table_layout = QVBoxLayout(table_card)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["عنوان", "متن", "زمان ثبت"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.itemDoubleClicked.connect(lambda _: self._load_selected_for_edit())
        table_layout.addWidget(self.table)
        root.addWidget(table_card, 1)

        self._populate_table()

    def _selected_row(self) -> int | None:
        rows = sorted({index.row() for index in self.table.selectionModel().selectedRows()})
        if rows:
            return rows[0]
        row = self.table.currentRow()
        if row >= 0:
            return row
        return None

    def _add_draft(self) -> None:
        title = self.title_input.text().strip()
        message = self.message_input.toPlainText().strip()

        if not title:
            QMessageBox.warning(self, "پیش نویس", "عنوان پیش نویس الزامی است.")
            return
        if not message:
            QMessageBox.warning(self, "پیش نویس", "متن پیش نویس الزامی است.")
            return

        self.drafts.insert(
            0,
            {
                "title": title,
                "message": message,
                "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "generic",
                "line": "",
                "mobiles": [],
            },
        )
        self._populate_table()
        self.drafts_changed.emit([dict(item) for item in self.drafts])
        self._cancel_edit()

    def _load_selected_for_edit(self) -> None:
        row = self._selected_row()
        if row is None or not (0 <= row < len(self.drafts)):
            QMessageBox.information(self, "پیش نویس", "ابتدا یک پیش نویس را انتخاب کنید.")
            return

        draft = self.drafts[row]
        self.editing_index = row
        self.title_input.setText(str(draft.get("title", "")))
        self.message_input.setPlainText(str(draft.get("message", "")))
        self.mode_label.setText(f"حالت: ویرایش پیش نویس شماره {row + 1}")

    def _apply_edit(self) -> None:
        if self.editing_index is None:
            QMessageBox.information(self, "پیش نویس", "ابتدا یک پیش نویس را برای ویرایش انتخاب کنید.")
            return
        if not (0 <= self.editing_index < len(self.drafts)):
            self._cancel_edit()
            return

        title = self.title_input.text().strip()
        message = self.message_input.toPlainText().strip()
        if not title:
            QMessageBox.warning(self, "پیش نویس", "عنوان پیش نویس الزامی است.")
            return
        if not message:
            QMessageBox.warning(self, "پیش نویس", "متن پیش نویس الزامی است.")
            return

        current = self.drafts[self.editing_index]
        current["title"] = title
        current["message"] = message
        current["saved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self._populate_table()
        self.drafts_changed.emit([dict(item) for item in self.drafts])
        self._cancel_edit()

    def _cancel_edit(self) -> None:
        self.editing_index = None
        self.mode_label.setText("حالت: افزودن پیش نویس جدید")
        self._clear_form()

    def _delete_selected(self) -> None:
        rows = sorted({index.row() for index in self.table.selectionModel().selectedRows()}, reverse=True)
        if not rows:
            QMessageBox.information(self, "پیش نویس", "حداقل یک پیش نویس را انتخاب کنید.")
            return

        for row in rows:
            if 0 <= row < len(self.drafts):
                self.drafts.pop(row)

        self._populate_table()
        self.drafts_changed.emit([dict(item) for item in self.drafts])
        self._cancel_edit()

    def _clear_form(self) -> None:
        self.title_input.clear()
        self.message_input.clear()

    def _populate_table(self) -> None:
        self.table.setRowCount(len(self.drafts))
        for row, item in enumerate(self.drafts):
            self.table.setItem(row, 0, QTableWidgetItem(str(item.get("title", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(str(item.get("message", ""))))
            self.table.setItem(row, 2, QTableWidgetItem(str(item.get("saved_at", ""))))

    def set_drafts(self, drafts: list[dict[str, Any]]) -> None:
        self.drafts = [dict(item) for item in drafts]
        self._populate_table()
        if self.editing_index is not None and self.editing_index >= len(self.drafts):
            self._cancel_edit()
