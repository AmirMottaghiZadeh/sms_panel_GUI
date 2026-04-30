from __future__ import annotations

from typing import Any

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from sms_panel.ui.widgets import CardFrame, SecondaryButton


class CreditPage(QWidget):
    refresh_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        root = QVBoxLayout(self)
        header_row = QHBoxLayout()
        title = QLabel("اعتبار حساب")
        title.setProperty("class", "fa-header")
        header_row.addWidget(title)
        header_row.addStretch(1)

        refresh = SecondaryButton("بروزرسانی")
        refresh.clicked.connect(self.refresh_requested.emit)
        header_row.addWidget(refresh)
        root.addLayout(header_row)

        credit_card = CardFrame()
        credit_layout = QVBoxLayout(credit_card)
        self.remaining_credit_label = QLabel("اعتبار باقی مانده - پیام")
        self.remaining_credit_label.setProperty("class", "kpi-value")
        credit_layout.addWidget(self.remaining_credit_label)
        root.addWidget(credit_card)

        self.lines_table = QTableWidget(0, 1)
        self.lines_table.setHorizontalHeaderLabels(["شماره خطوط ارسال"])
        self.lines_table.horizontalHeader().setStretchLastSection(True)
        self.lines_table.verticalHeader().setVisible(False)
        self.lines_table.setAlternatingRowColors(True)
        self.lines_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        root.addWidget(self.lines_table)

    def update_credit_details(self, remaining_messages: Any) -> None:
        text_value = str(remaining_messages).strip()
        if not text_value:
            text_value = "-"
        self.remaining_credit_label.setText(f"اعتبار باقی مانده {text_value} پیام")

    def update_lines(self, lines: list[str]) -> None:
        self.lines_table.setRowCount(len(lines))
        for row, line in enumerate(lines):
            self.lines_table.setItem(row, 0, QTableWidgetItem(str(line)))
