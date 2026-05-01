from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
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

from sms_panel.services.contacts import mask_mobile
from sms_panel.ui.widgets import CardFrame, SecondaryButton

TIME_PATTERNS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d %H:%M",
)

SEND_TIME_KEYS = ("sendDateTime", "sendDate", "dateTime", "createdAt", "createDate")
RECEIVE_TIME_KEYS = ("receivedDateTime", "receiveDateTime", "receiveDate", "dateTime", "createdAt")


class HourlyTrendChart(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.sent_counts: list[int] = [0] * 24
        self.received_counts: list[int] = [0] * 24
        self.setMinimumHeight(230)

    def set_series(self, sent_counts: list[int], received_counts: list[int]) -> None:
        self.sent_counts = (sent_counts + [0] * 24)[:24]
        self.received_counts = (received_counts + [0] * 24)[:24]
        self.update()

    def _series_points(self, values: list[int], plot_rect: QRectF, max_value: int) -> list[QPointF]:
        if not values:
            return []

        points: list[QPointF] = []
        x_step = plot_rect.width() / max(23, 1)
        for index, value in enumerate(values):
            x = plot_rect.left() + (x_step * index)
            y_ratio = value / max(max_value, 1)
            y = plot_rect.bottom() - (y_ratio * plot_rect.height())
            points.append(QPointF(x, y))
        return points

    def paintEvent(self, event: Any) -> None:  # noqa: ANN401
        _ = event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        text_color = self.palette().color(self.foregroundRole())
        is_dark = text_color.lightness() > 150

        grid_color = QColor(255, 255, 255, 58) if is_dark else QColor(25, 15, 32, 50)
        label_color = QColor(255, 255, 255, 150) if is_dark else QColor(50, 35, 58, 140)
        sent_color = QColor("#F07C58") if is_dark else QColor("#B63B24")
        recv_color = QColor("#52C8B0") if is_dark else QColor("#1E8977")

        outer = QRectF(self.rect()).adjusted(14, 12, -14, -12)
        plot_rect = outer.adjusted(44, 18, -16, -30)
        if plot_rect.width() <= 20 or plot_rect.height() <= 20:
            return

        max_value = max(max(self.sent_counts), max(self.received_counts), 1)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 14) if is_dark else QColor(255, 255, 255, 170))
        painter.drawRoundedRect(outer, 14, 14)

        for step in range(5):
            y = plot_rect.top() + (plot_rect.height() * step / 4)
            painter.setPen(QPen(grid_color, 1, Qt.PenStyle.DashLine))
            painter.drawLine(QPointF(plot_rect.left(), y), QPointF(plot_rect.right(), y))

            value = int(round(max_value * (4 - step) / 4))
            painter.setPen(label_color)
            painter.drawText(QRectF(outer.left() + 4, y - 10, 36, 20), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, str(value))

        tick_hours = [0, 4, 8, 12, 16, 20, 23]
        for hour in tick_hours:
            x = plot_rect.left() + (plot_rect.width() * hour / 23)
            painter.setPen(QPen(grid_color, 1))
            painter.drawLine(QPointF(x, plot_rect.bottom()), QPointF(x, plot_rect.bottom() + 5))
            painter.setPen(label_color)
            painter.drawText(QRectF(x - 14, plot_rect.bottom() + 6, 28, 16), Qt.AlignmentFlag.AlignCenter, f"{hour:02d}")

        if max(self.sent_counts) == 0 and max(self.received_counts) == 0:
            painter.setPen(label_color)
            painter.drawText(plot_rect, Qt.AlignmentFlag.AlignCenter, "هنوز داده ای برای رسم روند امروز ثبت نشده است")
            return

        self._draw_line_series(painter, self._series_points(self.sent_counts, plot_rect, max_value), sent_color)
        self._draw_line_series(painter, self._series_points(self.received_counts, plot_rect, max_value), recv_color)

    def _draw_line_series(self, painter: QPainter, points: list[QPointF], color: QColor) -> None:
        if not points:
            return

        path = QPainterPath(points[0])
        for point in points[1:]:
            path.lineTo(point)

        painter.setPen(QPen(color, 2.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        for idx, point in enumerate(points):
            if idx % 4 == 0 or idx == len(points) - 1:
                painter.drawEllipse(point, 3.4, 3.4)


class DashboardPage(QWidget):
    refresh_requested = pyqtSignal()
    navigate_requested = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.mask_mobile_numbers = False
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
        self.interaction_card = self._make_card("نرخ تعامل امروز")
        cards.addWidget(self.sent_card[0], 0, 0)
        cards.addWidget(self.received_card[0], 0, 1)
        cards.addWidget(self.contacts_card[0], 0, 2)
        cards.addWidget(self.drafts_card[0], 1, 0)
        cards.addWidget(self.unique_card[0], 1, 1)
        cards.addWidget(self.interaction_card[0], 1, 2)
        root.addLayout(cards)

        chart_card = CardFrame()
        chart_layout = QVBoxLayout(chart_card)
        chart_title = QLabel("روند ساعتی ارسال / وصول")
        chart_title.setProperty("class", "fa-subtitle")
        chart_layout.addWidget(chart_title)

        legend_row = QHBoxLayout()
        legend_row.addWidget(self._legend_dot("#B63B24", "ارسالی"))
        legend_row.addWidget(self._legend_dot("#1E8977", "دریافتی"))
        legend_row.addStretch(1)
        self.chart_note = QLabel("تحلیل توزیع پیام ها در ساعات روز جاری")
        self.chart_note.setProperty("class", "muted")
        legend_row.addWidget(self.chart_note)
        chart_layout.addLayout(legend_row)

        self.trend_chart = HourlyTrendChart()
        chart_layout.addWidget(self.trend_chart)
        root.addWidget(chart_card)

        tables_row = QHBoxLayout()
        tables_row.setSpacing(12)

        sent_box = CardFrame()
        sent_layout = QVBoxLayout(sent_box)
        sent_title = QLabel("آخرین پیام های ارسالی")
        sent_title.setProperty("class", "fa-subtitle")
        sent_layout.addWidget(sent_title)

        self.sent_table = QTableWidget(0, 4)
        self.sent_table.setHorizontalHeaderLabels(["شناسه", "شماره", "متن", "زمان"])
        self.sent_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.sent_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.sent_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.sent_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.sent_table.verticalHeader().setVisible(False)
        self.sent_table.setAlternatingRowColors(True)
        self.sent_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        sent_layout.addWidget(self.sent_table)

        recv_box = CardFrame()
        recv_layout = QVBoxLayout(recv_box)
        recv_title = QLabel("آخرین پیام های دریافتی")
        recv_title.setProperty("class", "fa-subtitle")
        recv_layout.addWidget(recv_title)

        self.recv_table = QTableWidget(0, 3)
        self.recv_table.setHorizontalHeaderLabels(["شماره", "متن", "زمان"])
        self.recv_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.recv_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.recv_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.recv_table.verticalHeader().setVisible(False)
        self.recv_table.setAlternatingRowColors(True)
        self.recv_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        recv_layout.addWidget(self.recv_table)

        tables_row.addWidget(sent_box, 2)
        tables_row.addWidget(recv_box, 1)
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
        self.sent_table.setRowCount(min(len(rows), 20))
        for row_index, row in enumerate(rows[:20]):
            mobile = str(row.get("mobile", row.get("receiver", row.get("phoneNumber", "-"))))
            values = [
                str(row.get("messageId", row.get("id", "-"))),
                mask_mobile(mobile) if self.mask_mobile_numbers else mobile,
                str(row.get("messageText", row.get("text", row.get("message", "-")))),
                str(self._pick_value(row, SEND_TIME_KEYS, "-")),
            ]
            for column, value in enumerate(values):
                self.sent_table.setItem(row_index, column, QTableWidgetItem(value))

    def update_received_rows(self, rows: list[dict[str, Any]]) -> None:
        self.recv_table.setRowCount(min(len(rows), 20))
        for row_index, row in enumerate(rows[:20]):
            mobile = str(row.get("mobile", row.get("sender", row.get("from", "-"))))
            values = [
                mask_mobile(mobile) if self.mask_mobile_numbers else mobile,
                str(row.get("messageText", row.get("text", row.get("message", "-")))),
                str(self._pick_value(row, RECEIVE_TIME_KEYS, "-")),
            ]
            for column, value in enumerate(values):
                self.recv_table.setItem(row_index, column, QTableWidgetItem(value))

    def update_analytics(self, sent_rows: list[dict[str, Any]], received_rows: list[dict[str, Any]]) -> None:
        sent_hours = self._hourly_counts(sent_rows, SEND_TIME_KEYS)
        recv_hours = self._hourly_counts(received_rows, RECEIVE_TIME_KEYS)
        self.trend_chart.set_series(sent_hours, recv_hours)

        unique_receivers = self._unique_receivers(sent_rows)
        self.unique_card[1].setText(str(unique_receivers))

        sent_count = len(sent_rows)
        recv_count = len(received_rows)
        interaction_ratio = (recv_count / sent_count * 100.0) if sent_count else 0.0
        self.interaction_card[1].setText(f"{interaction_ratio:.1f}%")

        peak_hour = max(range(24), key=lambda hour: sent_hours[hour]) if sent_hours else 0
        peak_count = sent_hours[peak_hour] if sent_hours else 0
        avg_length = self._average_message_length(sent_rows)
        self.chart_note.setText(
            f"پیک ارسال: {peak_hour:02d}:00 ({peak_count}) | میانگین طول پیام: {avg_length:.0f} کاراکتر"
        )

    def _hourly_counts(self, rows: list[dict[str, Any]], candidate_keys: tuple[str, ...]) -> list[int]:
        counts = [0] * 24
        for row in rows:
            timestamp = self._pick_value(row, candidate_keys, "")
            hour = self._extract_hour(timestamp)
            if hour is not None:
                counts[hour] += 1
        return counts

    @staticmethod
    def _pick_value(row: dict[str, Any], candidate_keys: tuple[str, ...], default: str = "") -> str:
        for key in candidate_keys:
            value = row.get(key)
            if value not in (None, ""):
                return str(value)
        return default

    @staticmethod
    def _extract_hour(value: Any) -> int | None:
        text = str(value).strip()
        if not text:
            return None

        stripped = text.replace("Z", "").replace("+00:00", "")
        for fmt in TIME_PATTERNS:
            try:
                return datetime.strptime(stripped, fmt).hour
            except ValueError:
                continue

        match = re.search(r"(\d{1,2}):(\d{2})", text)
        if match:
            hour = int(match.group(1))
            if 0 <= hour < 24:
                return hour

        return None

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
