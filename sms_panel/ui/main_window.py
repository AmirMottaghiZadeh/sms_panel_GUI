from __future__ import annotations
from typing import Any, Callable

from PyQt6.QtCore import QThreadPool
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from sms_panel.config import API_KEY_FILE, APP_ICON_FILE
from sms_panel.core.models import ApiResult
from sms_panel.core.workers import ApiWorker
from sms_panel.services.contacts import normalize_contacts
from sms_panel.services.drafts import normalize_drafts
from sms_panel.services.response_parser import extract_items, extract_line_numbers
from sms_panel.services.settings_store import SettingsStore
from sms_panel.services.sms_ir_client import SmsIrClient
from sms_panel.ui.dialogs.api_key_dialog import ApiKeyDialog
from sms_panel.ui.pages.contacts_page import ContactsPage
from sms_panel.ui.pages.credit_page import CreditPage
from sms_panel.ui.pages.dashboard_page import DashboardPage
from sms_panel.ui.pages.drafts_page import DraftsPage
from sms_panel.ui.pages.reports_page import ReportsPage
from sms_panel.ui.pages.send_page import SendPage
from sms_panel.ui.pages.settings_page import SettingsPage
from sms_panel.ui.theme import build_stylesheet
from sms_panel.ui.widgets import CardFrame, NavButton, StatusBadge


class MainWindow(QMainWindow):
    def __init__(self, store: SettingsStore, settings: dict[str, Any], api_key: str) -> None:
        super().__init__()
        self.store = store
        self.settings = settings
        self.client = SmsIrClient(api_key)
        self.pool = QThreadPool.globalInstance()
        self._active_workers: set[ApiWorker] = set()

        self.panel_title = str(self.settings.get("panel_title", "")).strip() or "پنل پیامکی دسکتاپ"
        self.setWindowTitle(f"{self.panel_title} | SMS.ir")
        if APP_ICON_FILE.exists():
            self.setWindowIcon(QIcon(str(APP_ICON_FILE)))
        self.resize(1320, 860)

        self._build_ui()
        self.apply_theme(self.settings.get("theme", "light"))
        self.refresh_account_data()
        self.refresh_dashboard()

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(12)

        root_layout.addWidget(self._build_top_bar())

        body = QHBoxLayout()
        body.setSpacing(12)
        self.sidebar = self._build_sidebar()
        body.addWidget(self.sidebar)

        self.pages = QStackedWidget()

        contacts = normalize_contacts(self.settings.get("contacts", []))
        drafts = normalize_drafts(self.settings.get("drafts", []))
        self.settings["contacts"] = contacts
        self.settings["drafts"] = drafts

        line_number = str(self.settings.get("line_number", "")).strip()
        color_scheme = self.settings.get("color_scheme", "peach_eggplant")

        self.dashboard_page = DashboardPage()
        self.dashboard_page.refresh_requested.connect(self.refresh_dashboard)

        self.send_page = SendPage(
            contacts=contacts,
            line_number=line_number,
            drafts=drafts,
            available_lines=[line_number] if line_number else [],
        )
        self.send_page.send_single_requested.connect(self.handle_send_single)
        self.send_page.send_group_requested.connect(self.handle_send_group)
        self.send_page.send_contacts_requested.connect(self.handle_send_contacts)
        self.send_page.draft_saved.connect(self.add_draft)
        self.send_page.contacts_changed.connect(self.save_contacts)
        self.send_page.line_number_changed.connect(self.save_line_number)

        self.drafts_page = DraftsPage(drafts=drafts)
        self.drafts_page.drafts_changed.connect(self.save_drafts)

        self.reports_page = ReportsPage()
        self.reports_page.report_request.connect(self.handle_report_request)

        self.credit_page = CreditPage()
        self.credit_page.refresh_requested.connect(self.refresh_account_data)

        self.contacts_page = ContactsPage(contacts=contacts)
        self.contacts_page.contacts_changed.connect(self.save_contacts)

        self.settings_page = SettingsPage(
            theme=self.settings.get("theme", "light"),
            line_number=line_number,
            color_scheme=color_scheme,
            panel_title=self.panel_title,
        )
        self.settings_page.theme_changed.connect(self.handle_theme_change)
        self.settings_page.color_scheme_changed.connect(self.handle_color_scheme_change)
        self.settings_page.api_change_requested.connect(self.change_api_key)
        self.settings_page.line_number_changed.connect(self.save_line_number)
        self.settings_page.panel_title_changed.connect(self.save_panel_title)

        self.page_order = ["dashboard", "send", "drafts", "contacts", "reports", "credit", "settings"]
        self.page_map = {
            "dashboard": self.dashboard_page,
            "send": self.send_page,
            "drafts": self.drafts_page,
            "contacts": self.contacts_page,
            "reports": self.reports_page,
            "credit": self.credit_page,
            "settings": self.settings_page,
        }

        for key in self.page_order:
            self.pages.addWidget(self.page_map[key])

        body.addWidget(self.pages, 1)
        root_layout.addLayout(body, 1)
        self.setCentralWidget(root)

        self.switch_page("dashboard")

    def _build_top_bar(self) -> QWidget:
        bar = CardFrame()
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(14, 10, 14, 10)

        self.panel_title_label = QLabel(self.panel_title)
        self.panel_title_label.setProperty("class", "fa-header")
        bar_layout.addWidget(self.panel_title_label)

        subtitle = QLabel("SMS.ir REST API")
        subtitle.setProperty("class", "muted")
        bar_layout.addWidget(subtitle)

        bar_layout.addStretch(1)

        self.status_badge = StatusBadge("در حال بررسی اتصال...")
        self.status_badge.setProperty("class", "badge-wait")
        bar_layout.addWidget(self.status_badge)

        return bar

    def _build_sidebar(self) -> QWidget:
        side = CardFrame()
        side.setFixedWidth(210)
        layout = QVBoxLayout(side)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.nav_buttons: dict[str, NavButton] = {}
        items = [
            ("dashboard", "داشبورد"),
            ("send", "ارسال پیام"),
            ("drafts", "پیش نویس ها"),
            ("contacts", "لیست مخاطبین"),
            ("reports", "گزارش ها"),
            ("credit", "اعتبار حساب"),
            ("settings", "تنظیمات"),
        ]

        for key, text in items:
            btn = NavButton()
            btn.setText(text)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, route=key: self.switch_page(route))
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            layout.addWidget(btn)
            self.nav_buttons[key] = btn

        layout.addStretch(1)

        fusion_hint = QLabel("Style Engine: Fusion")
        fusion_hint.setProperty("class", "muted")
        layout.addWidget(fusion_hint)
        return side

    def switch_page(self, route: str) -> None:
        if route not in self.page_order:
            return

        self.pages.setCurrentIndex(self.page_order.index(route))
        for key, button in self.nav_buttons.items():
            button.setChecked(key == route)

    def run_async(self, fn: Callable[[], Any], done: Callable[[Any, Exception | None], None]) -> None:
        worker = ApiWorker(fn)
        self._active_workers.add(worker)

        def wrapped_done(result: Any, error: Exception | None) -> None:
            try:
                done(result, error)
            finally:
                self._active_workers.discard(worker)

        worker.signals.finished.connect(wrapped_done)
        self.pool.start(worker)

    def handle_send_single(self, line_number: str, mobile: str, message: str) -> None:
        if not mobile or not message:
            QMessageBox.warning(self, "ارسال تکی", "شماره موبایل و متن پیام الزامی است.")
            return
        self.handle_send_group(line_number, [mobile], message)

    def handle_send_group(self, line_number: str, mobiles: list[str], message: str) -> None:
        if not line_number:
            QMessageBox.warning(self, "ارسال پیام", "لطفا یک شماره خط ارسال انتخاب کنید.")
            return
        if not mobiles or not message:
            QMessageBox.warning(self, "ارسال گروهی", "حداقل یک شماره و متن پیام را وارد کنید.")
            return

        self.set_status("در حال ارسال پیام...", "badge-wait")

        def task() -> ApiResult:
            return self.client.send_bulk(line_number=line_number, mobiles=mobiles, message=message)

        def done(result: ApiResult | None, error: Exception | None) -> None:
            if error is not None:
                QMessageBox.critical(self, "خطا", str(error))
                self.set_status("ارسال با خطا", "badge-error")
                return
            if result is None:
                self.set_status("خطای نامشخص", "badge-error")
                return

            if result.ok:
                QMessageBox.information(self, "ارسال پیام", "درخواست ارسال با موفقیت ثبت شد.")
                self.set_status("ارسال موفق", "badge-ok")
                self.refresh_dashboard()
            else:
                QMessageBox.warning(self, "ارسال پیام", result.message)
                self.set_status("ارسال ناموفق", "badge-error")

        self.run_async(task, done)

    def handle_send_contacts(self, line_number: str, mobiles: list[str], message: str) -> None:
        self.handle_send_group(line_number, mobiles, message)

    def handle_report_request(self, report_type: str, payload: dict[str, Any]) -> None:
        if report_type == "message" and not str(payload.get("message_id", "")).strip().isdigit():
            QMessageBox.warning(self, "گزارش پیام", "Message ID معتبر وارد کنید.")
            return
        if report_type == "pack" and not str(payload.get("pack_id", "")).strip().isdigit():
            QMessageBox.warning(self, "گزارش Pack", "Pack ID معتبر وارد کنید.")
            return

        self.set_status("در حال دریافت گزارش...", "badge-wait")

        def task() -> ApiResult:
            if report_type == "message":
                return self.client.report_message(int(payload["message_id"]))
            if report_type == "pack":
                return self.client.report_pack(int(payload["pack_id"]))
            if report_type == "archived_send":
                return self.client.report_archived(payload.get("from_date", ""), payload.get("to_date", ""))
            if report_type == "archived_recv":
                return self.client.report_archived_received(payload.get("from_date", ""), payload.get("to_date", ""))
            if report_type == "today_recv":
                return self.client.report_today_received()
            if report_type == "latest_recv":
                return self.client.report_latest_received(int(payload.get("count", 20)))
            return self.client.report_today()

        def done(result: ApiResult | None, error: Exception | None) -> None:
            if error is not None:
                QMessageBox.critical(self, "خطا", str(error))
                self.set_status("گزارش با خطا", "badge-error")
                return
            if result is None:
                self.set_status("گزارش ناموفق", "badge-error")
                return

            table_payload = result.data if result.data is not None else result.raw
            self.reports_page.show_report_table(
                payload=table_payload,
                message=result.message,
                status_code=result.status_code,
                ok=result.ok,
            )
            self.set_status("گزارش بروزرسانی شد", "badge-ok" if result.ok else "badge-error")

        self.run_async(task, done)

    def refresh_all(self) -> None:
        self.refresh_dashboard()
        self.refresh_account_data()

    def refresh_dashboard(self) -> None:
        self.set_status("در حال بارگذاری داشبورد...", "badge-wait")

        def task() -> dict[str, ApiResult]:
            return {
                "sent": self.client.report_today(page_size=25, page_number=1),
                "recv": self.client.report_today_received(page_size=25, page_number=1),
            }

        def done(result: dict[str, ApiResult] | None, error: Exception | None) -> None:
            if error is not None or result is None:
                self.set_status("داشبورد در دسترس نیست", "badge-error")
                return

            sent_data = extract_items(result["sent"].data)
            recv_data = extract_items(result["recv"].data)

            self.dashboard_page.update_cards(
                sent_count=len(sent_data),
                received_count=len(recv_data),
                contacts_count=len(self.settings.get("contacts", [])),
                drafts_count=len(self.settings.get("drafts", [])),
            )
            self.dashboard_page.update_sent_rows(sent_data[:20])

            if result["sent"].ok and result["recv"].ok:
                self.set_status("داشبورد آماده است", "badge-ok")
            else:
                self.set_status("بخشی از داشبورد خطا دارد", "badge-error")

        self.run_async(task, done)

    def refresh_account_data(self) -> None:
        self.set_status("در حال بررسی اعتبار...", "badge-wait")

        def task() -> dict[str, ApiResult]:
            return {
                "financial_credit": self.client.get_financial_credit(),
                "lines": self.client.get_line_numbers(),
            }

        def done(result: dict[str, ApiResult] | None, error: Exception | None) -> None:
            if error is not None or result is None:
                self.set_status("اتصال به API برقرار نشد", "badge-error")
                return

            credit_result = result["financial_credit"]
            credit_value: Any = credit_result.data
            if credit_value in (None, "") and isinstance(credit_result.raw, dict):
                credit_value = credit_result.raw.get("data", "-")
            if isinstance(credit_value, dict):
                credit_value = (
                    credit_value.get("returnedCreditCount")
                    or credit_value.get("credit")
                    or credit_value.get("creditAmount")
                    or "-"
                )
            lines = extract_line_numbers(result["lines"].data)

            self.credit_page.update_credit_details(credit_value)
            self.credit_page.update_lines(lines)

            preferred_line = str(self.settings.get("line_number", "")).strip()
            if lines:
                selected_line = preferred_line if preferred_line in lines else lines[0]
                self.send_page.set_available_lines(lines, selected_line)
                if selected_line != preferred_line:
                    self.save_line_number(selected_line)
            else:
                self.send_page.set_available_lines([], preferred_line)

            if result["financial_credit"].ok:
                self.set_status("API متصل است", "badge-ok")
            else:
                self.set_status("API پاسخ خطا داد", "badge-error")

        self.run_async(task, done)

    def add_draft(self, draft: dict[str, Any]) -> None:
        current = self.settings.get("drafts", [])
        payload = [draft, *current]
        self.save_drafts(payload, notify=True)

    def save_drafts(self, drafts: list[dict[str, Any]], notify: bool = False) -> None:
        normalized = normalize_drafts(drafts)[:100]
        self.settings["drafts"] = normalized
        self.send_page.set_drafts(normalized)
        self.drafts_page.set_drafts(normalized)
        self.persist_settings()
        self.refresh_dashboard()
        if notify:
            QMessageBox.information(self, "پیش نویس", "پیش نویس ذخیره شد.")

    def save_contacts(self, contacts: list[dict[str, str]]) -> None:
        normalized = normalize_contacts(contacts)
        self.settings["contacts"] = normalized
        self.send_page.set_contacts(normalized)
        self.contacts_page.set_contacts(normalized)
        self.persist_settings()
        self.refresh_dashboard()

    def save_line_number(self, line_number: str) -> None:
        line_number = line_number.strip()
        if not line_number:
            return
        self.settings["line_number"] = line_number
        self.send_page.set_line_number(line_number)
        self.settings_page.line_input.setText(line_number)
        self.persist_settings()

    def save_panel_title(self, panel_title: str) -> None:
        panel_title = panel_title.strip() or "پنل پیامکی دسکتاپ"
        self.panel_title = panel_title
        self.settings["panel_title"] = panel_title
        self.panel_title_label.setText(panel_title)
        self.settings_page.panel_title_input.setText(panel_title)
        self.setWindowTitle(f"{panel_title} | SMS.ir")
        self.persist_settings()

    def handle_theme_change(self, theme_name: str) -> None:
        self.settings["theme"] = theme_name
        self.settings_page.theme_combo.blockSignals(True)
        self.settings_page.theme_combo.setCurrentText(theme_name)
        self.settings_page.theme_combo.blockSignals(False)
        self.apply_theme(theme_name)
        self.persist_settings()

    def handle_color_scheme_change(self, scheme_name: str) -> None:
        self.settings["color_scheme"] = scheme_name
        self.settings_page.scheme_combo.blockSignals(True)
        index = self.settings_page.scheme_combo.findData(scheme_name)
        self.settings_page.scheme_combo.setCurrentIndex(max(index, 0))
        self.settings_page.scheme_combo.blockSignals(False)
        self.apply_theme(self.settings.get("theme", "light"))
        self.persist_settings()

    def apply_theme(self, theme_name: str) -> None:
        scheme_name = str(self.settings.get("color_scheme", "peach_eggplant"))
        QApplication.instance().setStyleSheet(build_stylesheet(theme_name, scheme_name))

    def set_status(self, text: str, badge_class: str) -> None:
        self.status_badge.setText(text)
        self.status_badge.setProperty("class", badge_class)
        self.status_badge.style().unpolish(self.status_badge)
        self.status_badge.style().polish(self.status_badge)

    def persist_settings(self) -> None:
        self.store.save(self.settings)

    def change_api_key(self) -> None:
        dialog = ApiKeyDialog(self.settings.get("api_key", ""), self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_key = dialog.api_key()
            self.settings["api_key"] = new_key
            self.persist_settings()
            API_KEY_FILE.write_text(new_key, encoding="utf-8")
            self.client.update_api_key(new_key)
            self.refresh_all()
