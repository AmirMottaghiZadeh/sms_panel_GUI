from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from sms_panel.services.contacts import mask_mobile
from sms_panel.services.response_parser import extract_items
from sms_panel.ui.jalali_calendar import JalaliDateField
from sms_panel.config import PROJECT_ROOT
from sms_panel.ui.widgets import CardFrame, NumericLineEdit, SecondaryButton, autosize_table_columns


class ReportsPage(QWidget):
    report_request = pyqtSignal(str, dict)
    DELIVERY_STATE_COLUMN_TOKENS = ("delivery", "deliverystate", "deliverystatus", "deliveryresult")
    DELIVERY_STATE_CODE_MAP = {
        -1: "نامشخص",
        0: "در صف ارسال",
        1: "ارسال شده",
        2: "تحویل شده",
        3: "ناموفق",
        4: "منقضی شده",
        5: "رد شده",
        6: "در لیست سیاه",
        7: "شماره نامعتبر",
        8: "مسدود شده",
        9: "لغو شده",
    }
    DELIVERY_STATE_TEXT_MAP = {
        "delivered": "تحویل شده",
        "sent": "ارسال شده",
        "submitted": "ارسال شده",
        "accepted": "پذیرفته شده",
        "queued": "در صف ارسال",
        "pending": "در انتظار ارسال",
        "failed": "ناموفق",
        "undelivered": "تحویل نشده",
        "notdelivered": "تحویل نشده",
        "rejected": "رد شده",
        "blocked": "مسدود شده",
        "blacklist": "در لیست سیاه",
        "expired": "منقضی شده",
        "canceled": "لغو شده",
        "cancelled": "لغو شده",
        "unknown": "نامشخص",
    }

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
        self.from_date = JalaliDateField(placeholder_text="از تاریخ (هجری شمسی)")
        self.to_date = JalaliDateField(placeholder_text="تا تاریخ (هجری شمسی)")
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
        latest_count = NumericLineEdit(1, 100)
        latest_count.set_numeric_value(20)
        latest_count.setPlaceholderText("تعداد")
        latest_btn = SecondaryButton("آخرین دریافتی")
        latest_btn.clicked.connect(lambda: self.report_request.emit("latest_recv", {"count": latest_count.numeric_value(20)}))
        row_d.addWidget(live_send_btn)
        row_d.addWidget(live_recv_btn)
        row_d.addWidget(latest_count)
        row_d.addWidget(latest_btn)

        query_layout.addLayout(row_a)
        query_layout.addLayout(row_b)
        query_layout.addLayout(row_c)
        query_layout.addLayout(row_d)
        root.addWidget(query)

        meta_row = QHBoxLayout()
        self.meta_label = QLabel("نتیجه گزارش به صورت جدول نمایش داده می شود")
        self.meta_label.setProperty("class", "fa-note")
        meta_row.addWidget(self.meta_label, 1)

        self.export_csv_btn = SecondaryButton("دانلود CSV")
        self.export_csv_btn.clicked.connect(self._export_csv)
        self.export_csv_btn.setEnabled(False)
        meta_row.addWidget(self.export_csv_btn)
        root.addLayout(meta_row)

        self.output_table = QTableWidget(0, 0)
        self.output_table.setAlternatingRowColors(True)
        self.output_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.output_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        root.addWidget(self.output_table)

    def _emit_archived_send(self) -> None:
        self.report_request.emit(
            "archived_send",
            {
                "from_date": self.from_date.gregorian_iso(),
                "to_date": self.to_date.gregorian_iso(),
                "from_date_jalali": self.from_date.jalali_text(),
                "to_date_jalali": self.to_date.jalali_text(),
            },
        )

    def _emit_archived_recv(self) -> None:
        self.report_request.emit(
            "archived_recv",
            {
                "from_date": self.from_date.gregorian_iso(),
                "to_date": self.to_date.gregorian_iso(),
                "from_date_jalali": self.from_date.jalali_text(),
                "to_date_jalali": self.to_date.jalali_text(),
            },
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
                if self._looks_like_delivery_state_column(col_name):
                    text = self._format_delivery_state(text)
                if self.mask_mobile_numbers and self._looks_like_mobile_column(col_name):
                    text = mask_mobile(text)
                self.output_table.setItem(row_index, col_index, QTableWidgetItem(text))

        if columns:
            autosize_table_columns(self.output_table, max_width=460)

        status_text = "موفق" if ok else "خطا"
        self.meta_label.setText(f"وضعیت: {status_text} | کد: {status_code} | پیام: {message} | ردیف: {len(rows)}")
        self.export_csv_btn.setEnabled(len(rows) > 0 and len(columns) > 0)

    @staticmethod
    def _looks_like_mobile_column(column_name: str) -> bool:
        key = column_name.strip().lower()
        tokens = {"mobile", "phone", "receiver", "sender", "from", "to", "number"}
        return any(token in key for token in tokens)

    @classmethod
    def _looks_like_delivery_state_column(cls, column_name: str) -> bool:
        key = re.sub(r"[^a-z0-9]+", "", column_name.strip().lower())
        return any(token in key for token in cls.DELIVERY_STATE_COLUMN_TOKENS)

    @classmethod
    def _format_delivery_state(cls, raw_value: str) -> str:
        source = raw_value.strip()
        if not source:
            return source

        normalized = source.lower().replace("_", "").replace("-", "").replace(" ", "")
        if normalized in cls.DELIVERY_STATE_TEXT_MAP:
            label = cls.DELIVERY_STATE_TEXT_MAP[normalized]
            return label if source == label else f"{label} ({source})"

        try:
            code = int(float(source))
        except ValueError:
            return source

        label = cls.DELIVERY_STATE_CODE_MAP.get(code)
        if label is None:
            return f"وضعیت نامشخص (کد {code})"
        return f"{label} (کد {code})"

    def _export_csv(self) -> None:
        if self.output_table.columnCount() == 0 or self.output_table.rowCount() == 0:
            QMessageBox.information(self, "خروجی CSV", "جدولی برای دانلود وجود ندارد.")
            return

        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "ذخیره گزارش CSV",
            str(PROJECT_ROOT / "report.csv"),
            "CSV Files (*.csv)",
        )
        if not file_name:
            return

        try:
            with Path(file_name).open("w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                headers = [
                    self.output_table.horizontalHeaderItem(col).text()
                    for col in range(self.output_table.columnCount())
                ]
                writer.writerow(headers)
                for row in range(self.output_table.rowCount()):
                    row_data = []
                    for col in range(self.output_table.columnCount()):
                        item = self.output_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            QMessageBox.information(self, "خروجی CSV", "فایل CSV با موفقیت ذخیره شد.")
        except Exception as exc:
            QMessageBox.critical(self, "خروجی CSV", f"خطا در ذخیره فایل:\n{exc}")

    def set_mask_mobile_numbers(self, enabled: bool) -> None:
        self.mask_mobile_numbers = bool(enabled)
