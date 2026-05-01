from __future__ import annotations

from typing import Any

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from sms_panel.services.contacts import mask_mobile
from sms_panel.services.response_parser import extract_items
from sms_panel.ui.widgets import CardFrame, SecondaryButton


class ReportsPage(QWidget):
    report_request = pyqtSignal(str, dict)

    def __init__(self) -> None:
        super().__init__()
        self.mask_mobile_numbers = False
        root = QVBoxLayout(self)
        title = QLabel("گزارش ها")
        title.setProperty("class", "fa-header")
        root.addWidget(title)

        query = CardFrame()
        query_layout = QVBoxLayout(query)

        row_a = QHBoxLayout()
        self.message_id = QLineEdit()
        self.message_id.setPlaceholderText("Message ID")
        msg_button = SecondaryButton("گزارش پیام")
        msg_button.clicked.connect(lambda: self.report_request.emit("message", {"message_id": self.message_id.text().strip()}))
        row_a.addWidget(self.message_id)
        row_a.addWidget(msg_button)

        row_b = QHBoxLayout()
        self.pack_id = QLineEdit()
        self.pack_id.setPlaceholderText("Pack ID")
        pack_button = SecondaryButton("گزارش Pack")
        pack_button.clicked.connect(lambda: self.report_request.emit("pack", {"pack_id": self.pack_id.text().strip()}))
        row_b.addWidget(self.pack_id)
        row_b.addWidget(pack_button)

        row_c = QHBoxLayout()
        self.from_date = QLineEdit()
        self.from_date.setPlaceholderText("fromDate: yyyy-mm-dd")
        self.to_date = QLineEdit()
        self.to_date.setPlaceholderText("toDate: yyyy-mm-dd")
        archived_send_btn = SecondaryButton("آرشیو ارسالی")
        archived_send_btn.clicked.connect(self._emit_archived_send)
        archived_recv_btn = SecondaryButton("آرشیو دریافتی")
        archived_recv_btn.clicked.connect(self._emit_archived_recv)
        row_c.addWidget(self.from_date)
        row_c.addWidget(self.to_date)
        row_c.addWidget(archived_send_btn)
        row_c.addWidget(archived_recv_btn)

        row_d = QHBoxLayout()
        live_send_btn = SecondaryButton("گزارش ارسالی امروز")
        live_send_btn.clicked.connect(lambda: self.report_request.emit("today_send", {}))
        live_recv_btn = SecondaryButton("گزارش دریافتی امروز")
        live_recv_btn.clicked.connect(lambda: self.report_request.emit("today_recv", {}))
        latest_count = QSpinBox()
        latest_count.setRange(1, 100)
        latest_count.setValue(20)
        latest_btn = SecondaryButton("آخرین دریافتی")
        latest_btn.clicked.connect(lambda: self.report_request.emit("latest_recv", {"count": latest_count.value()}))
        row_d.addWidget(live_send_btn)
        row_d.addWidget(live_recv_btn)
        row_d.addWidget(latest_count)
        row_d.addWidget(latest_btn)

        query_layout.addLayout(row_a)
        query_layout.addLayout(row_b)
        query_layout.addLayout(row_c)
        query_layout.addLayout(row_d)
        root.addWidget(query)

        self.meta_label = QLabel("نتیجه گزارش به صورت جدول نمایش داده می شود")
        self.meta_label.setProperty("class", "fa-note")
        root.addWidget(self.meta_label)

        self.output_table = QTableWidget(0, 0)
        self.output_table.setAlternatingRowColors(True)
        self.output_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.output_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        root.addWidget(self.output_table)

    def _emit_archived_send(self) -> None:
        self.report_request.emit(
            "archived_send",
            {"from_date": self.from_date.text().strip(), "to_date": self.to_date.text().strip()},
        )

    def _emit_archived_recv(self) -> None:
        self.report_request.emit(
            "archived_recv",
            {"from_date": self.from_date.text().strip(), "to_date": self.to_date.text().strip()},
        )

    @staticmethod
    def _rows_from_payload(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            rows = [item for item in payload if isinstance(item, dict)]
            if rows:
                return rows
            return [{"value": str(item)} for item in payload]

        if isinstance(payload, dict):
            nested_rows = extract_items(payload)
            if nested_rows and not (len(nested_rows) == 1 and nested_rows[0] is payload):
                return nested_rows
            return [payload]

        if payload is None:
            return []

        return [{"value": str(payload)}]

    def show_report_table(self, payload: Any, message: str, status_code: int, ok: bool) -> None:
        rows = self._rows_from_payload(payload)

        columns: list[str] = []
        seen: set[str] = set()
        for row in rows:
            for key in row.keys():
                key_text = str(key)
                if key_text not in seen:
                    seen.add(key_text)
                    columns.append(key_text)

        self.output_table.setRowCount(len(rows))
        self.output_table.setColumnCount(len(columns))
        self.output_table.setHorizontalHeaderLabels(columns)

        for row_index, row in enumerate(rows):
            for col_index, col_name in enumerate(columns):
                value = row.get(col_name, "")
                text = str(value)
                if self.mask_mobile_numbers and self._looks_like_mobile_column(col_name):
                    text = mask_mobile(text)
                self.output_table.setItem(row_index, col_index, QTableWidgetItem(text))

        if columns:
            self.output_table.resizeColumnsToContents()

        status_text = "موفق" if ok else "خطا"
        self.meta_label.setText(f"وضعیت: {status_text} | کد: {status_code} | پیام: {message} | ردیف: {len(rows)}")

    @staticmethod
    def _looks_like_mobile_column(column_name: str) -> bool:
        key = column_name.strip().lower()
        tokens = {"mobile", "phone", "receiver", "sender", "from", "to", "number"}
        return any(token in key for token in tokens)

    def set_mask_mobile_numbers(self, enabled: bool) -> None:
        self.mask_mobile_numbers = bool(enabled)
