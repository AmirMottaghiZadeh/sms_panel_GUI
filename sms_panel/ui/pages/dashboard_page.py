from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from sms_panel.services.contacts import mask_mobile
from sms_panel.ui.widgets import CardFrame, SecondaryButton, autosize_table_columns

TIME_PATTERNS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d %H:%M",
    "%Y-%m-%d",
    "%Y/%m/%d",
)

SEND_TIME_KEYS = ("sendDateTime", "sendDate", "dateTime", "createdAt", "createDate")
RECEIVE_TIME_KEYS = ("receivedDateTime", "receiveDateTime", "receiveDate", "dateTime", "createdAt")
WEEKDAY_LABELS = ["شنبه", "یکشنبه", "دوشنبه", "سه شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]


class WeeklySentBarChart(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.day_counts: list[int] = [0] * 7
        self.setMinimumHeight(230)

    def set_counts(self, counts: list[int]) -> None:
        self.day_counts = (counts + [0] * 7)[:7]
        self.update()

    def paintEvent(self, event: Any) -> None:  # noqa: ANN401
        _ = event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        text_color = self.palette().color(self.foregroundRole())
        is_dark = text_color.lightness() > 150

        grid_color = QColor(255, 255, 255, 58) if is_dark else QColor(25, 15, 32, 50)
        label_color = QColor(255, 255, 255, 150) if is_dark else QColor(50, 35, 58, 140)
        bar_color = QColor("#F07C58") if is_dark else QColor("#B63B24")
        peak_color = QColor("#F4C95D") if is_dark else QColor("#4A274F")

        outer = QRectF(self.rect()).adjusted(14, 12, -14, -12)
        plot_rect = outer.adjusted(44, 18, -16, -40)
        if plot_rect.width() <= 20 or plot_rect.height() <= 20:
            return

        max_value = max(self.day_counts) if self.day_counts else 0

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 14) if is_dark else QColor(255, 255, 255, 170))
        painter.drawRoundedRect(outer, 14, 14)

        for step in range(5):
            y = plot_rect.top() + (plot_rect.height() * step / 4)
            painter.setPen(QPen(grid_color, 1, Qt.PenStyle.DashLine))
            painter.drawLine(QPointF(plot_rect.left(), y), QPointF(plot_rect.right(), y))

            value = int(round(max(max_value, 1) * (4 - step) / 4))
            painter.setPen(label_color)
            painter.drawText(
                QRectF(outer.left() + 4, y - 10, 36, 20),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                str(value),
            )

        if max_value == 0:
            painter.setPen(label_color)
            painter.drawText(plot_rect, Qt.AlignmentFlag.AlignCenter, "برای این هفته داده ارسالی ثبت نشده است")
            return

        bar_count = len(self.day_counts)
        slot_width = plot_rect.width() / max(bar_count, 1)
        bar_width = min(44.0, slot_width * 0.62)
        peak_value = max(self.day_counts)

        for index, count in enumerate(self.day_counts):
            bar_height = (count / max_value) * plot_rect.height()
            x = plot_rect.left() + (slot_width * index) + ((slot_width - bar_width) / 2)
            y = plot_rect.bottom() - bar_height
            rect = QRectF(x, y, bar_width, max(3.0, bar_height))

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(peak_color if count == peak_value and count > 0 else bar_color)
            painter.drawRoundedRect(rect, 6, 6)

            painter.setPen(label_color)
            painter.drawText(
                QRectF(x - 8, plot_rect.bottom() - bar_height - 20, bar_width + 16, 16),
                Qt.AlignmentFlag.AlignCenter,
                str(count),
            )
            painter.drawText(
                QRectF(x - 12, plot_rect.bottom() + 8, bar_width + 24, 18),
                Qt.AlignmentFlag.AlignCenter,
                WEEKDAY_LABELS[index],
            )


class DashboardPage(QWidget):
    refresh_requested = pyqtSignal()
    navigate_requested = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.mask_mobile_numbers = False
        self._display_limit = 60

        root = QVBoxLayout(self)
        root.setSpacing(12)

        top_row = QHBoxLayout()
        title = QLabel("داشبورد")
        title.setProperty("class", "fa-header")
        top_row.addWidget(title)
        top_row.addStretch(1)
        self.refresh_button = SecondaryButton("بروزرسانی داشبورد")
        self.refresh_button.clicked.connect(self.refresh_requested.emit)
        top_row.addWidget(self.refresh_button)
        root.addLayout(top_row)

        quick_actions = CardFrame()
        quick_layout = QVBoxLayout(quick_actions)
        quick_title = QLabel("دسترسی سریع")
        quick_title.setProperty("class", "fa-subtitle")
        quick_layout.addWidget(quick_title)

        quick_row = QHBoxLayout()
        for text, route in (
            ("ارسال سریع پیام", "send"),
            ("گزارش های پیامک", "reports"),
            ("مدیریت مخاطبین", "contacts"),
            ("اعتبار حساب", "credit"),
        ):
            button = SecondaryButton(text)
            button.clicked.connect(lambda _checked=False, page=route: self.navigate_requested.emit(page))
            quick_row.addWidget(button)
        quick_layout.addLayout(quick_row)
        root.addWidget(quick_actions)

        cards = QGridLayout()
        cards.setHorizontalSpacing(12)
        cards.setVerticalSpacing(12)
        self.sent_card = self._make_card("پیام های ارسالی امروز")
        self.received_card = self._make_card("پیام های دریافتی امروز")
        self.contacts_card = self._make_card("تعداد مخاطبین")
        self.drafts_card = self._make_card("پیش نویس ها")
        self.unique_card = self._make_card("گیرنده یکتا در امروز")
        self.interaction_card = self._make_card("درصد موفقیت ارسال امروز")
        cards.addWidget(self.sent_card[0], 0, 0)
        cards.addWidget(self.received_card[0], 0, 1)
        cards.addWidget(self.contacts_card[0], 0, 2)
        cards.addWidget(self.drafts_card[0], 1, 0)
        cards.addWidget(self.unique_card[0], 1, 1)
        cards.addWidget(self.interaction_card[0], 1, 2)
        root.addLayout(cards)

        chart_card = CardFrame()
        chart_layout = QVBoxLayout(chart_card)
        chart_title = QLabel("نمودار روزانه ارسالی هفته جاری")
        chart_title.setProperty("class", "fa-subtitle")
        chart_layout.addWidget(chart_title)

        legend_row = QHBoxLayout()
        legend_row.addWidget(self._legend_dot("#B63B24", "ارسالی"))
        legend_row.addWidget(self._legend_dot("#4A274F", "بیشترین روز"))
        legend_row.addStretch(1)
        self.chart_note = QLabel("تعداد پیام های ارسالی برای هر روز هفته")
        self.chart_note.setProperty("class", "muted")
        legend_row.addWidget(self.chart_note)
        chart_layout.addLayout(legend_row)

        self.weekly_chart = WeeklySentBarChart()
        chart_layout.addWidget(self.weekly_chart)
        root.addWidget(chart_card)

        tables_row = QHBoxLayout()
        tables_row.setSpacing(12)

        self.sent_box = CardFrame()
        sent_layout = QVBoxLayout(self.sent_box)
        sent_title = QLabel("آخرین پیام های ارسالی")
        sent_title.setProperty("class", "fa-subtitle")
        sent_layout.addWidget(sent_title)

        self.sent_table = QTableWidget(0, 4)
        self.sent_table.setHorizontalHeaderLabels(["شناسه", "شماره", "متن", "زمان"])
        self.sent_table.verticalHeader().setVisible(False)
        self.sent_table.setAlternatingRowColors(True)
        self.sent_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.sent_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        sent_layout.addWidget(self.sent_table)

        self.recv_box = CardFrame()
        recv_layout = QVBoxLayout(self.recv_box)
        recv_title = QLabel("آخرین پیام های دریافتی")
        recv_title.setProperty("class", "fa-subtitle")
        recv_layout.addWidget(recv_title)

        self.recv_table = QTableWidget(0, 3)
        self.recv_table.setHorizontalHeaderLabels(["شماره", "متن", "زمان"])
        self.recv_table.verticalHeader().setVisible(False)
        self.recv_table.setAlternatingRowColors(True)
        self.recv_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.recv_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        recv_layout.addWidget(self.recv_table)

        tables_row.addWidget(self.sent_box, 2)
        tables_row.addWidget(self.recv_box, 1)
        root.addLayout(tables_row, 1)

    @staticmethod
    def _legend_dot(color: str, text: str) -> QLabel:
        label = QLabel(f"● {text}")
        label.setStyleSheet(f"color: {color}; font-weight: 700;")
        return label

    def _make_card(self, title: str) -> tuple[CardFrame, QLabel]:
        frame = CardFrame()
        frame.setProperty("class", "kpi-card")
        layout = QVBoxLayout(frame)
        title_label = QLabel(title)
        title_label.setProperty("class", "fa-note")
        value = QLabel("-")
        value.setProperty("class", "kpi-value")
        value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(title_label)
        layout.addWidget(value)
        return frame, value

    def update_cards(self, sent_count: int, received_count: int, contacts_count: int, drafts_count: int) -> None:
        self.sent_card[1].setText(str(sent_count))
        self.received_card[1].setText(str(received_count))
        self.contacts_card[1].setText(str(contacts_count))
        self.drafts_card[1].setText(str(drafts_count))

    def update_sent_rows(self, rows: list[dict[str, Any]]) -> None:
        shown_rows = rows[: self._display_limit]
        self.sent_table.setRowCount(len(shown_rows))
        for row_index, row in enumerate(shown_rows):
            mobile = str(row.get("mobile", row.get("receiver", row.get("phoneNumber", "-"))))
            values = [
                str(row.get("messageId", row.get("id", "-"))),
                mask_mobile(mobile) if self.mask_mobile_numbers else mobile,
                str(row.get("messageText", row.get("text", row.get("message", "-")))),
                str(self._pick_value(row, SEND_TIME_KEYS, "-")),
            ]
            for column, value in enumerate(values):
                self.sent_table.setItem(row_index, column, QTableWidgetItem(value))

        autosize_table_columns(self.sent_table, stretch_columns=(2,), max_width=360)
        self._adjust_activity_panels(self.sent_table.rowCount(), self.recv_table.rowCount())

    def update_received_rows(self, rows: list[dict[str, Any]]) -> None:
        shown_rows = rows[: self._display_limit]
        self.recv_table.setRowCount(len(shown_rows))
        for row_index, row in enumerate(shown_rows):
            mobile = str(row.get("mobile", row.get("sender", row.get("from", "-"))))
            values = [
                mask_mobile(mobile) if self.mask_mobile_numbers else mobile,
                str(row.get("messageText", row.get("text", row.get("message", "-")))),
                str(self._pick_value(row, RECEIVE_TIME_KEYS, "-")),
            ]
            for column, value in enumerate(values):
                self.recv_table.setItem(row_index, column, QTableWidgetItem(value))

        autosize_table_columns(self.recv_table, stretch_columns=(1,), max_width=360)
        self._adjust_activity_panels(self.sent_table.rowCount(), self.recv_table.rowCount())

    def update_analytics(
        self,
        sent_rows: list[dict[str, Any]],
        received_rows: list[dict[str, Any]],
        weekly_sent_rows: list[dict[str, Any]] | None = None,
    ) -> None:
        weekly_source = weekly_sent_rows if weekly_sent_rows is not None else sent_rows
        weekly_counts = self._weekday_counts(weekly_source, SEND_TIME_KEYS)
        self.weekly_chart.set_counts(weekly_counts)

        unique_receivers = self._unique_receivers(sent_rows)
        self.unique_card[1].setText(str(unique_receivers))

        sent_count = len(sent_rows)
        failed_count = self._count_failed_messages(sent_rows)
        success_count = max(sent_count - failed_count, 0)
        success_rate = (success_count / sent_count * 100.0) if sent_count else 0.0
        self.interaction_card[1].setText(f"{success_rate:.1f}% | خطا: {failed_count}")

        peak_day_index = max(range(7), key=lambda day: weekly_counts[day]) if weekly_counts else 0
        peak_day_count = weekly_counts[peak_day_index] if weekly_counts else 0
        avg_length = self._average_message_length(sent_rows)
        self.chart_note.setText(
            f"بیشترین ارسال: {WEEKDAY_LABELS[peak_day_index]} ({peak_day_count}) | میانگین طول پیام: {avg_length:.0f}"
        )

    def _adjust_activity_panels(self, sent_rows: int, recv_rows: int) -> None:
        sent_height = self._table_height(self.sent_table, sent_rows)
        recv_height = self._table_height(self.recv_table, recv_rows)
        self.sent_table.setMinimumHeight(sent_height)
        self.recv_table.setMinimumHeight(recv_height)
        self.sent_box.setMinimumHeight(sent_height + 56)
        self.recv_box.setMinimumHeight(recv_height + 56)

    @staticmethod
    def _table_height(table: QTableWidget, row_count: int) -> int:
        row_height = max(24, table.verticalHeader().defaultSectionSize())
        header_height = max(28, table.horizontalHeader().height())
        rows = max(4, min(22, row_count))
        return min(680, header_height + (rows * row_height) + 24)

    def _weekday_counts(self, rows: list[dict[str, Any]], candidate_keys: tuple[str, ...]) -> list[int]:
        counts = [0] * 7
        for row in rows:
            timestamp = self._pick_value(row, candidate_keys, "")
            parsed = self._extract_datetime(timestamp)
            if parsed is None:
                continue
            # Python weekday: Monday=0 ... Sunday=6 -> Saturday-first index
            index = (parsed.weekday() + 2) % 7
            counts[index] += 1
        return counts

    @staticmethod
    def _pick_value(row: dict[str, Any], candidate_keys: tuple[str, ...], default: str = "") -> str:
        for key in candidate_keys:
            value = row.get(key)
            if value not in (None, ""):
                return str(value)
        return default

    @staticmethod
    def _extract_datetime(value: Any) -> datetime | None:
        text = str(value).strip()
        if not text:
            return None

        # برخی خروجی های API زمان را به صورت unix timestamp برمی گردانند.
        if re.fullmatch(r"\d{10,13}", text):
            try:
                raw_value = int(text)
                if len(text) == 13:
                    raw_value //= 1000
                return datetime.fromtimestamp(raw_value)
            except (ValueError, OSError):
                return None

        normalized = text.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            pass

        for fmt in TIME_PATTERNS:
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue

        match = re.search(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})(?:[ T](\d{1,2}:\d{2}(?::\d{2})?))?", text)
        if not match:
            return None

        raw_date = match.group(1).replace("/", "-")
        raw_time = match.group(2) or "00:00:00"
        if raw_time.count(":") == 1:
            raw_time = f"{raw_time}:00"
        try:
            return datetime.strptime(f"{raw_date} {raw_time}", "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None

    def _count_failed_messages(self, rows: list[dict[str, Any]]) -> int:
        return sum(1 for row in rows if self._row_has_failure_status(row))

    def _row_has_failure_status(self, row: dict[str, Any]) -> bool:
        failure_tokens = {
            "0",
            "-1",
            "failed",
            "error",
            "undelivered",
            "notdelivered",
            "rejected",
            "reject",
            "blacklist",
            "invalid",
            "timeout",
            "cancel",
            "canceled",
            "cancelled",
            "ناموفق",
            "خطا",
            "ارسال نشده",
            "برگشت",
        }

        candidate_keys = (
            "deliveryState",
            "deliveryStatus",
            "deliveryResult",
            "status",
            "state",
            "statusText",
            "statusName",
            "result",
            "resultCode",
            "errorCode",
            "error",
        )

        for key, value in row.items():
            key_text = str(key).lower()
            if not any(token in key_text for token in ("status", "state", "delivery", "result", "error")):
                if key not in candidate_keys:
                    continue

            text = str(value).strip().lower()
            if not text:
                continue
            normalized = text.replace("_", "").replace("-", "").replace(" ", "")
            if text in failure_tokens or normalized in failure_tokens:
                return True
            if text.isdigit() and int(text) < 0:
                return True

        return False

    @staticmethod
    def _unique_receivers(rows: list[dict[str, Any]]) -> int:
        seen: set[str] = set()
        for row in rows:
            raw = row.get("mobile") or row.get("receiver") or row.get("phoneNumber")
            if raw in (None, ""):
                continue
            seen.add(str(raw).strip())
        return len(seen)

    @staticmethod
    def _average_message_length(rows: list[dict[str, Any]]) -> float:
        lengths = [
            len(str(row.get("messageText") or row.get("text") or row.get("message") or "").strip())
            for row in rows
        ]
        valid = [item for item in lengths if item > 0]
        return sum(valid) / len(valid) if valid else 0.0

    def set_mask_mobile_numbers(self, enabled: bool) -> None:
        self.mask_mobile_numbers = bool(enabled)
