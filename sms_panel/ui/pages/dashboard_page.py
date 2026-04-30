from __future__ import annotations

from typing import Any

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from sms_panel.ui.widgets import CardFrame, SecondaryButton


class DashboardPage(QWidget):
    refresh_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        root = QVBoxLayout(self)

        top_row = QHBoxLayout()
        title = QLabel("داشبورد")
        title.setProperty("class", "fa-header")
        top_row.addWidget(title)
        top_row.addStretch(1)
        self.refresh_button = SecondaryButton("بروزرسانی داشبورد")
        self.refresh_button.clicked.connect(self.refresh_requested.emit)
        top_row.addWidget(self.refresh_button)
        root.addLayout(top_row)

        cards = QGridLayout()
        self.sent_card = self._make_card("پیام های ارسالی امروز")
        self.received_card = self._make_card("پیام های دریافتی امروز")
        self.contacts_card = self._make_card("تعداد مخاطبین")
        self.drafts_card = self._make_card("پیش نویس ها")
        cards.addWidget(self.sent_card[0], 0, 0)
        cards.addWidget(self.received_card[0], 0, 1)
        cards.addWidget(self.contacts_card[0], 1, 0)
        cards.addWidget(self.drafts_card[0], 1, 1)
        root.addLayout(cards)

        table_box = CardFrame()
        box_layout = QVBoxLayout(table_box)
        box_title = QLabel("آخرین پیام های ارسالی")
        box_title.setProperty("class", "fa-subtitle")
        box_layout.addWidget(box_title)

        self.sent_table = QTableWidget(0, 4)
        self.sent_table.setHorizontalHeaderLabels(["شناسه", "شماره", "متن", "زمان"])
        self.sent_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.sent_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.sent_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.sent_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.sent_table.verticalHeader().setVisible(False)
        self.sent_table.setAlternatingRowColors(True)
        self.sent_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        box_layout.addWidget(self.sent_table)
        root.addWidget(table_box)

    def _make_card(self, title: str) -> tuple[CardFrame, QLabel]:
        frame = CardFrame()
        layout = QVBoxLayout(frame)
        title_label = QLabel(title)
        title_label.setProperty("class", "fa-note")
        value = QLabel("-")
        value.setProperty("class", "kpi-value")
        layout.addWidget(title_label)
        layout.addWidget(value)
        return frame, value

    def update_cards(self, sent_count: int, received_count: int, contacts_count: int, drafts_count: int) -> None:
        self.sent_card[1].setText(str(sent_count))
        self.received_card[1].setText(str(received_count))
        self.contacts_card[1].setText(str(contacts_count))
        self.drafts_card[1].setText(str(drafts_count))

    def update_sent_rows(self, rows: list[dict[str, Any]]) -> None:
        self.sent_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = [
                str(row.get("messageId", row.get("id", "-"))),
                str(row.get("mobile", row.get("receiver", "-"))),
                str(row.get("messageText", row.get("text", "-"))),
                str(row.get("sendDateTime", row.get("sendDate", "-"))),
            ]
            for column, value in enumerate(values):
                self.sent_table.setItem(row_index, column, QTableWidgetItem(value))
