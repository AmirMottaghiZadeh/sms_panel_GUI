from __future__ import annotations
import hashlib
import json
import platform
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from PyQt6.QtCore import QByteArray, Qt, QThreadPool, QTimer
from PyQt6.QtGui import QIcon, QKeySequence, QPixmap, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from sms_panel.config import API_KEY_FILE, APP_ICON_FILE, APP_VERSION, PROJECT_ROOT
from sms_panel.core.models import ApiResult
from sms_panel.core.error_handler import ErrorHandler
from sms_panel.core.workers import ApiWorker
from sms_panel.services.contacts import dedupe_contacts, normalize_contacts
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
from sms_panel.ui.theme import build_qt_palette, build_stylesheet, palette_for
from sms_panel.ui.widgets import CardFrame, NavButton, StatusBadge, ToastNotification


class MainWindow(QMainWindow):
    def __init__(self, store: SettingsStore, settings: dict[str, Any], api_key: str) -> None:
        super().__init__()
        self.store = store
        self.settings = settings
        self.client = SmsIrClient(api_key)
        self.pool = QThreadPool.globalInstance()
        self._active_workers: set[ApiWorker] = set()

        self.panel_title = str(self.settings.get("panel_title", "")).strip() or "پنل پیامکی دسکتاپ"
        self.organization_name = str(self.settings.get("organization_name", "")).strip() or "SMS.ir REST API"

        log_file_path = str(self.settings.get("log_file_path", "")).strip()
        self.settings["log_file_path"] = log_file_path
        ErrorHandler.configure_logging(str(self.settings.get("log_level", "INFO")), log_file_path)

        self.client.update_network_options(
            int(self.settings.get("api_timeout_sec", 25) or 25),
            int(self.settings.get("api_retry_count", 1) or 1),
        )

        self._apply_window_branding()
        self.setMinimumSize(1100, 720)
        self.resize(1320, 860)

        self._build_ui()

        self.toast = ToastNotification(self)

        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self.refresh_all)

        self._add_keyboard_shortcuts()
        self._apply_runtime_settings()
        self._restore_window_geometry()
        self._enforce_app_lock()
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
        if self.settings.get("dedupe_contacts_on_save", True):
            contacts = dedupe_contacts(contacts)

        max_drafts = int(self.settings.get("max_drafts", 100) or 100)
        drafts = normalize_drafts(self.settings.get("drafts", []))[: max(10, min(max_drafts, 1000))]
        self.settings["contacts"] = contacts
        self.settings["drafts"] = drafts

        line_number = str(self.settings.get("line_number", "")).strip()

        self.dashboard_page = DashboardPage()
        self.dashboard_page.refresh_requested.connect(self.refresh_dashboard)
        self.dashboard_page.navigate_requested.connect(self.switch_page)

        self.send_page = SendPage(
            contacts=contacts,
            line_number=line_number,
            drafts=drafts,
            available_lines=[line_number] if line_number else [],
            default_category=str(self.settings.get("contacts_default_category", "عمومی")),
            mask_mobile_numbers=bool(self.settings.get("mask_mobile_numbers", False)),
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

        self.contacts_page = ContactsPage(
            contacts=contacts,
            default_category=str(self.settings.get("contacts_default_category", "عمومی")),
            mask_mobile_numbers=bool(self.settings.get("mask_mobile_numbers", False)),
        )
        self.contacts_page.contacts_changed.connect(self.save_contacts)

        self.settings_page = SettingsPage(settings=self.settings, app_version=APP_VERSION)
        self.settings_page.settings_patch_requested.connect(self.apply_settings_patch)
        self.settings_page.api_change_requested.connect(self.change_api_key)
        self.settings_page.api_test_requested.connect(self.refresh_account_data)
        self.settings_page.export_settings_requested.connect(self.export_settings_to_json)
        self.settings_page.import_settings_requested.connect(self.import_settings_from_json)
        self.settings_page.backup_data_requested.connect(self.backup_contacts_and_drafts)
        self.settings_page.restore_data_requested.connect(self.restore_contacts_and_drafts)
        self.settings_page.reset_defaults_requested.connect(self.reset_settings_to_defaults)
        self.settings_page.set_pin_requested.connect(self.set_or_change_pin)
        self.settings_page.clear_pin_requested.connect(self.clear_pin)
        self.settings_page.copy_diagnostics_requested.connect(self.copy_diagnostic_info)

        self.page_order = ["dashboard", "send", "drafts", "contacts", "reports", "credit", "settings"]
        self.page_wrappers = {
            "dashboard": self._wrap_page(self.dashboard_page),
            "send": self._wrap_page(self.send_page),
            "drafts": self._wrap_page(self.drafts_page),
            "contacts": self._wrap_page(self.contacts_page),
            "reports": self._wrap_page(self.reports_page),
            "credit": self._wrap_page(self.credit_page),
            "settings": self.settings_page,
        }
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
            self.pages.addWidget(self.page_wrappers[key])

        body.addWidget(self.pages, 1)
        root_layout.addLayout(body, 1)
        self.setCentralWidget(root)

        self.switch_page("dashboard")

    @staticmethod
    def _wrap_page(page: QWidget) -> QScrollArea:
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.Shape.NoFrame)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        area.setWidget(page)
        return area

    def _build_top_bar(self) -> QWidget:
        bar = CardFrame()
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(14, 10, 14, 10)

        self.panel_title_label = QLabel(self.panel_title)
        self.panel_title_label.setProperty("class", "fa-header")
        bar_layout.addWidget(self.panel_title_label)

        self.subtitle_label = QLabel(self.organization_name)
        self.subtitle_label.setProperty("class", "muted")
        bar_layout.addWidget(self.subtitle_label)

        self.brand_logo_label = QLabel()
        self.brand_logo_label.setFixedSize(46, 46)
        self.brand_logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.brand_logo_label.setProperty("class", "brand-logo")
        bar_layout.addWidget(self.brand_logo_label)

        bar_layout.addStretch(1)

        self.route_label = QLabel("داشبورد")
        self.route_label.setProperty("class", "fa-note")
        bar_layout.addWidget(self.route_label)

        self.status_badge = StatusBadge("در حال بررسی اتصال...")
        self.status_badge.setProperty("class", "badge-wait")
        bar_layout.addWidget(self.status_badge)

        return bar

    def _build_sidebar(self) -> QWidget:
        side = CardFrame()
        side.setMinimumWidth(198)
        side.setMaximumWidth(240)
        side.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(side)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.nav_buttons: dict[str, NavButton] = {}
        items = [
            ("dashboard", "● داشبورد"),
            ("send",      "▶ ارسال پیام"),
            ("drafts",    "◇ پیش نویس ها"),
            ("contacts",  "◎ مخاطبین"),
            ("reports",   "☰ گزارش ها"),
            ("credit",    "◆ اعتبار حساب"),
            ("settings",  "⚙ تنظیمات"),
        ]

        for key, text in items:
            btn = NavButton()
            btn.setText(text)
            btn.setCheckable(True)
            btn.setToolTip(text)
            btn.clicked.connect(lambda checked, route=key: self.switch_page(route))
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            layout.addWidget(btn)
            self.nav_buttons[key] = btn

        layout.addStretch(1)
        return side

    def switch_page(self, route: str) -> None:
        if route not in self.page_order:
            return

        self.pages.setCurrentIndex(self.page_order.index(route))
        for key, button in self.nav_buttons.items():
            button.setChecked(key == route)
            if key == route:
                self.route_label.setText(button.text())

    def _add_keyboard_shortcuts(self) -> None:
        for index, key in enumerate(self.page_order, start=1):
            shortcut = QShortcut(QKeySequence(f"Ctrl+{index}"), self)
            shortcut.activated.connect(lambda route=key: self.switch_page(route))

    def _restore_window_geometry(self) -> None:
        geo_str = str(self.settings.get("window_geometry", "")).strip()
        if geo_str:
            try:
                self.restoreGeometry(QByteArray.fromBase64(geo_str.encode("ascii")))
            except Exception:
                pass

    def _save_window_geometry(self) -> None:
        self.settings["window_geometry"] = self.saveGeometry().toBase64().data().decode("ascii")
        self.persist_settings()

    def _update_refresh_timer(self) -> None:
        interval_sec = int(self.settings.get("auto_refresh_interval_sec", 0) or 0)
        self._refresh_timer.stop()
        if interval_sec > 0:
            self._refresh_timer.start(interval_sec * 1000)

    def _update_chart_palette(self) -> None:
        theme = str(self.settings.get("theme", "light"))
        scheme = str(self.settings.get("color_scheme", "peach_eggplant"))
        self.dashboard_page.update_chart_palette(palette_for(theme, scheme))

    def resizeEvent(self, event: Any) -> None:  # noqa: ANN401
        super().resizeEvent(event)
        if hasattr(self, "toast"):
            self.toast._reposition()

    def closeEvent(self, event: Any) -> None:  # noqa: ANN401
        self._save_window_geometry()
        super().closeEvent(event)

    def run_async(self, fn: Callable[[], Any], done: Callable[[Any, Exception | None], None]) -> None:
        worker = ApiWorker(fn)
        self._active_workers.add(worker)

        def wrapped_done(result: Any, error: Exception | None) -> None:
            try:
                if error:
                    ErrorHandler.log_warning(f"Async task error: {str(error)}")
                    ErrorHandler.handle_api_error(error, "عملیات API", self)
                done(result, error)
            except Exception as e:
                ErrorHandler.show_error(
                    title="خطای غیرمنتظره",
                    message="خطایی در پردازش نتیجه رخ داد",
                    exception=e,
                    context="run_async callback",
                    parent=self,
                )
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
        line_number = line_number.strip()
        cleaned_mobiles = [item.strip() for item in mobiles if item and item.strip()]
        message = message.strip()

        if not line_number:
            QMessageBox.warning(self, "ارسال پیام", "لطفا یک شماره خط ارسال انتخاب کنید.")
            return
        if not cleaned_mobiles or not message:
            QMessageBox.warning(self, "ارسال گروهی", "حداقل یک شماره و متن پیام را وارد کنید.")
            return

        threshold = int(self.settings.get("bulk_confirm_threshold", 50) or 50)
        if self.settings.get("bulk_confirm_enabled", True) and len(cleaned_mobiles) >= threshold:
            if not self._confirm_bulk_send(len(cleaned_mobiles), threshold):
                return

        final_message = self._build_outgoing_message(message)
        self.set_status("در حال ارسال پیام...", "badge-wait")

        def task() -> ApiResult:
            return self.client.send_bulk(line_number=line_number, mobiles=cleaned_mobiles, message=final_message)

        def done(result: ApiResult | None, error: Exception | None) -> None:
            if error is not None:
                self._notify_error("خطا", str(error))
                self.set_status("ارسال با خطا", "badge-error")
                return
            if result is None:
                self.set_status("خطای نامشخص", "badge-error")
                return

            if result.ok:
                self._notify_success("ارسال پیام", "درخواست ارسال با موفقیت ثبت شد.")
                self.set_status("ارسال موفق", "badge-ok")
                self.refresh_dashboard()
            else:
                self._notify_error("ارسال پیام", result.message)
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
        ErrorHandler.log_info("Refreshing dashboard data")
        self.set_status("در حال بارگذاری داشبورد...", "badge-wait")
        today = datetime.now().date()
        # هفته جاری را با شروع شنبه محاسبه می کنیم.
        week_start = today - timedelta(days=(today.weekday() + 2) % 7)
        from_date = week_start.strftime("%Y-%m-%d")
        to_date = today.strftime("%Y-%m-%d")

        def task() -> dict[str, ApiResult]:
            return {
                "sent": self.client.report_today(page_size=120, page_number=1),
                "recv": self.client.report_today_received(page_size=120, page_number=1),
                "sent_week": self.client.report_archived(
                    from_date=from_date,
                    to_date=to_date,
                    page_size=500,
                    page_number=1,
                ),
            }

        def done(result: dict[str, ApiResult] | None, error: Exception | None) -> None:
            if error is not None or result is None:
                ErrorHandler.log_warning("Dashboard refresh failed")
                self.set_status("داشبورد در دسترس نیست", "badge-error")
                return

            sent_data = extract_items(result["sent"].data)
            recv_data = extract_items(result["recv"].data)
            weekly_data = extract_items(result["sent_week"].data)

            self.dashboard_page.update_cards(
                sent_count=len(sent_data),
                received_count=len(recv_data),
                contacts_count=len(self.settings.get("contacts", [])),
                drafts_count=len(self.settings.get("drafts", [])),
            )
            self.dashboard_page.update_sent_rows(sent_data)
            self.dashboard_page.update_received_rows(recv_data)
            self.dashboard_page.update_analytics(
                sent_data,
                recv_data,
                weekly_sent_rows=weekly_data if weekly_data else sent_data,
            )

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
                self.settings["last_api_success_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.settings_page.last_api_success_label.setText(str(self.settings["last_api_success_at"]))
                self.persist_settings()
                self.set_status("API متصل است", "badge-ok")
            else:
                self.set_status("API پاسخ خطا داد", "badge-error")

        self.run_async(task, done)

    def add_draft(self, draft: dict[str, Any]) -> None:
        current = self.settings.get("drafts", [])
        payload = [draft, *current]
        self.save_drafts(payload, notify=True)

    def save_drafts(self, drafts: list[dict[str, Any]], notify: bool = False) -> None:
        max_drafts = int(self.settings.get("max_drafts", 100) or 100)
        max_drafts = max(10, min(max_drafts, 1000))
        normalized = normalize_drafts(drafts)[:max_drafts]
        self.settings["drafts"] = normalized
        self.send_page.set_drafts(normalized)
        self.drafts_page.set_drafts(normalized)
        self.persist_settings()
        self.refresh_dashboard()
        if notify:
            self._notify_success("پیش نویس", "پیش نویس ذخیره شد.")

    def save_contacts(self, contacts: list[dict[str, str]]) -> None:
        normalized = normalize_contacts(contacts)
        if self.settings.get("dedupe_contacts_on_save", True):
            normalized = dedupe_contacts(normalized)
        self.settings["contacts"] = normalized
        self.send_page.set_contacts(normalized)
        self.contacts_page.set_contacts(normalized)
        self.persist_settings()
        self.refresh_dashboard()

    def save_line_number(self, line_number: str) -> None:
        line_number = line_number.strip()
        self.settings["line_number"] = line_number
        if line_number:
            self.send_page.set_line_number(line_number)
        self.settings_page.line_input.setText(line_number)
        self.persist_settings()

    def save_panel_title(self, panel_title: str) -> None:
        panel_title = panel_title.strip() or "پنل پیامکی دسکتاپ"
        self.panel_title = panel_title
        self.settings["panel_title"] = panel_title
        self._apply_window_branding()
        self.settings_page.panel_title_input.setText(panel_title)
        self.persist_settings()

    def handle_theme_change(self, theme_name: str) -> None:
        try:
            ErrorHandler.log_info(f"Changing theme to: {theme_name}")
            self._apply_theme_change(theme_name)
        except Exception as e:
            ErrorHandler.show_error("خطا در تغییر تم", "خطایی در تغییر تم رخ داد", e, "Theme Change", self)

    def _apply_theme_change(self, theme_name: str) -> None:
        self.apply_settings_patch({"theme": theme_name})

    def handle_color_scheme_change(self, scheme_name: str) -> None:
        try:
            ErrorHandler.log_info(f"Changing color scheme to: {scheme_name}")
            self._apply_color_scheme_change(scheme_name)
        except Exception as e:
            ErrorHandler.show_error("خطا در تغییر رنگ", "خطایی در تغییر مجموعه رنگ رخ داد", e, "Color Scheme Change", self)

    def _apply_color_scheme_change(self, scheme_name: str) -> None:
        self.apply_settings_patch({"color_scheme": scheme_name})

    def apply_theme(self, theme_name: str) -> None:
        scheme_name = str(self.settings.get("color_scheme", "peach_eggplant"))
        font_scale = str(self.settings.get("font_scale", "normal"))
        ui_density = str(self.settings.get("ui_density", "comfortable"))
        app = QApplication.instance()
        app.setPalette(build_qt_palette(theme_name, scheme_name))
        app.setStyleSheet(build_stylesheet(theme_name, scheme_name, font_scale, ui_density))

    def _resolve_logo_path(self) -> Path | None:
        custom_logo = str(self.settings.get("brand_logo_path", "")).strip()
        if custom_logo:
            custom_path = Path(custom_logo)
            if custom_path.exists():
                return custom_path
        if APP_ICON_FILE.exists():
            return APP_ICON_FILE
        return None

    def _apply_window_branding(self) -> None:
        self.panel_title = str(self.settings.get("panel_title", "")).strip() or "پنل پیامکی دسکتاپ"
        self.organization_name = str(self.settings.get("organization_name", "")).strip() or "SMS.ir REST API"

        self.setWindowTitle(f"{self.panel_title} | SMS.ir")

        if hasattr(self, "panel_title_label"):
            self.panel_title_label.setText(self.panel_title)
        if hasattr(self, "subtitle_label"):
            self.subtitle_label.setText(self.organization_name)

        logo_path = self._resolve_logo_path()
        if logo_path is None:
            if hasattr(self, "brand_logo_label"):
                self.brand_logo_label.clear()
                self.brand_logo_label.hide()
            return

        self.setWindowIcon(QIcon(str(logo_path)))
        if hasattr(self, "brand_logo_label"):
            logo = QPixmap(str(logo_path)).scaled(
                42,
                42,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.brand_logo_label.setPixmap(logo)
            self.brand_logo_label.show()

    def _apply_runtime_settings(self) -> None:
        self._apply_window_branding()
        self.client.update_network_options(
            int(self.settings.get("api_timeout_sec", 25) or 25),
            int(self.settings.get("api_retry_count", 1) or 1),
        )

        log_level = str(self.settings.get("log_level", "INFO")).upper()
        log_file_path = str(self.settings.get("log_file_path", "")).strip()
        self.settings["log_file_path"] = log_file_path
        ErrorHandler.configure_logging(log_level, log_file_path)

        self.apply_theme(str(self.settings.get("theme", "light")))
        self._update_chart_palette()
        self._update_refresh_timer()

        default_category = str(self.settings.get("contacts_default_category", "عمومی")).strip() or "عمومی"
        self.send_page.set_default_category(default_category)
        self.contacts_page.set_default_category(default_category)

        mask_numbers = bool(self.settings.get("mask_mobile_numbers", False))
        self.send_page.set_mask_mobile_numbers(mask_numbers)
        self.contacts_page.set_mask_mobile_numbers(mask_numbers)
        self.dashboard_page.set_mask_mobile_numbers(mask_numbers)
        self.reports_page.set_mask_mobile_numbers(mask_numbers)

        self.settings_page.refresh_values(self.settings)

    def apply_settings_patch(self, patch: dict[str, Any]) -> None:
        if not patch:
            return

        previous_mask = bool(self.settings.get("mask_mobile_numbers", False))

        if "panel_title" in patch:
            value = str(patch.get("panel_title", "")).strip() or "پنل پیامکی دسکتاپ"
            self.settings["panel_title"] = value
        if "organization_name" in patch:
            self.settings["organization_name"] = str(patch.get("organization_name", "")).strip()
        if "brand_logo_path" in patch:
            logo_path = str(patch.get("brand_logo_path", "")).strip()
            if logo_path and not Path(logo_path).exists():
                QMessageBox.warning(self, "لوگو", "مسیر لوگوی انتخاب شده معتبر نیست.")
                return
            self.settings["brand_logo_path"] = logo_path
        if "line_number" in patch:
            self.settings["line_number"] = str(patch.get("line_number", "")).strip()
        if "message_signature" in patch:
            self.settings["message_signature"] = str(patch.get("message_signature", "")).strip()
        if "bulk_confirm_enabled" in patch:
            self.settings["bulk_confirm_enabled"] = bool(patch.get("bulk_confirm_enabled"))
        if "bulk_confirm_threshold" in patch:
            self.settings["bulk_confirm_threshold"] = max(1, int(patch.get("bulk_confirm_threshold", 50)))

        if "contacts_default_category" in patch:
            category = str(patch.get("contacts_default_category", "")).strip() or "عمومی"
            self.settings["contacts_default_category"] = category
        if "dedupe_contacts_on_save" in patch:
            self.settings["dedupe_contacts_on_save"] = bool(patch.get("dedupe_contacts_on_save"))
        if "max_drafts" in patch:
            self.settings["max_drafts"] = max(10, min(1000, int(patch.get("max_drafts", 100))))

        for key in ("notify_on_success", "notify_on_error", "show_popup_notifications", "beep_on_error"):
            if key in patch:
                self.settings[key] = bool(patch.get(key))

        for key in ("mask_mobile_numbers", "app_lock_enabled", "require_sensitive_action_confirmation"):
            if key in patch:
                self.settings[key] = bool(patch.get(key))

        if self.settings.get("app_lock_enabled", False) and not str(self.settings.get("app_pin_hash", "")).strip():
            QMessageBox.information(
                self,
                "امنیت",
                "برای فعال شدن قفل برنامه باید ابتدا گذرواژه تنظیم شود.",
            )
            self.settings["app_lock_enabled"] = False

        if "api_timeout_sec" in patch:
            self.settings["api_timeout_sec"] = max(5, min(120, int(patch.get("api_timeout_sec", 25))))
        if "api_retry_count" in patch:
            self.settings["api_retry_count"] = max(0, min(5, int(patch.get("api_retry_count", 1))))
        if "log_level" in patch:
            self.settings["log_level"] = str(patch.get("log_level", "INFO")).upper()
        if "log_file_path" in patch:
            self.settings["log_file_path"] = str(patch.get("log_file_path", "")).strip()

        for key in ("theme", "color_scheme", "font_scale", "ui_density"):
            if key in patch:
                self.settings[key] = str(patch.get(key, "")).strip()

        if "auto_refresh_interval_sec" in patch:
            self.settings["auto_refresh_interval_sec"] = max(
                0, min(3600, int(patch.get("auto_refresh_interval_sec", 0) or 0))
            )

        self._apply_runtime_settings()
        self.persist_settings()

        if "line_number" in patch:
            self.send_page.set_line_number(str(self.settings.get("line_number", "")))

        if self.settings.get("dedupe_contacts_on_save", True):
            deduped = dedupe_contacts(normalize_contacts(self.settings.get("contacts", [])))
            if len(deduped) != len(self.settings.get("contacts", [])):
                self.save_contacts(deduped)

        max_drafts = int(self.settings.get("max_drafts", 100) or 100)
        limited = normalize_drafts(self.settings.get("drafts", []))[:max_drafts]
        if len(limited) != len(self.settings.get("drafts", [])):
            self.save_drafts(limited)

        new_mask = bool(self.settings.get("mask_mobile_numbers", False))
        if previous_mask != new_mask:
            self.refresh_dashboard()

    def _build_outgoing_message(self, message: str) -> str:
        base_message = message.strip()
        signature = str(self.settings.get("message_signature", "")).strip()
        if not signature:
            return base_message
        if base_message.endswith(signature):
            return base_message
        return f"{base_message}\n{signature}"

    def _confirm_bulk_send(self, recipients_count: int, threshold: int) -> bool:
        answer = QMessageBox.question(
            self,
            "تایید ارسال انبوه",
            f"تعداد گیرندگان {recipients_count} است (آستانه {threshold}).\nارسال انجام شود؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes

    def _notify_success(self, title: str, message: str) -> None:
        if not self.settings.get("notify_on_success", True):
            return
        ErrorHandler.log_info(f"{title}: {message}")
        if not self.settings.get("show_popup_notifications", True):
            return
        if hasattr(self, "toast"):
            self.toast.show_toast(f"{title}: {message}", level="ok")
        else:
            QMessageBox.information(self, title, message)

    def _notify_error(self, title: str, message: str) -> None:
        if self.settings.get("notify_on_error", True):
            self._notify("warning", title, message)
        if self.settings.get("beep_on_error", False):
            QApplication.beep()

    def _notify(self, level: str, title: str, message: str) -> None:
        if not self.settings.get("show_popup_notifications", True):
            ErrorHandler.log_info(f"{title}: {message}")
            return
        if level == "information":
            QMessageBox.information(self, title, message)
            return
        if level == "critical":
            QMessageBox.critical(self, title, message)
            return
        QMessageBox.warning(self, title, message)

    def _confirm_sensitive_action(self, action_name: str) -> bool:
        if not self.settings.get("require_sensitive_action_confirmation", True):
            return True

        pin_hash = str(self.settings.get("app_pin_hash", "")).strip()
        if pin_hash and self.settings.get("app_lock_enabled", False):
            pin, ok = QInputDialog.getText(
                self,
                "تایید عملیات حساس",
                f"برای ادامه عملیات «{action_name}» گذرواژه را وارد کنید:",
                QLineEdit.EchoMode.Password,
            )
            if not ok:
                return False
            is_valid = self._hash_pin(pin) == pin_hash
            if not is_valid:
                QMessageBox.warning(self, "تایید عملیات", "گذرواژه وارد شده نادرست است.")
            return is_valid

        answer = QMessageBox.question(
            self,
            "تایید عملیات حساس",
            f"آیا مطمئن هستید که می خواهید «{action_name}» انجام شود؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes

    def _enforce_app_lock(self) -> None:
        if not self.settings.get("app_lock_enabled", False):
            return

        pin_hash = str(self.settings.get("app_pin_hash", "")).strip()
        if not pin_hash:
            return

        for attempt in range(3):
            pin, ok = QInputDialog.getText(
                self,
                "قفل برنامه",
                f"گذرواژه را وارد کنید (تلاش {attempt + 1} از 3):",
                QLineEdit.EchoMode.Password,
            )
            if not ok:
                raise SystemExit(0)
            if self._hash_pin(pin) == pin_hash:
                return

        QMessageBox.critical(self, "قفل برنامه", "گذرواژه اشتباه است. برنامه بسته می شود.")
        raise SystemExit(0)

    @staticmethod
    def _hash_pin(pin: str) -> str:
        return hashlib.sha256(pin.strip().encode("utf-8")).hexdigest()

    def set_or_change_pin(self) -> None:
        if str(self.settings.get("app_pin_hash", "")).strip() and not self._confirm_sensitive_action("تغییر گذرواژه"):
            return

        new_pin, ok = QInputDialog.getText(
            self,
            "تنظیم گذرواژه",
            "گذرواژه جدید را وارد کنید (حداقل 4 رقم):",
            QLineEdit.EchoMode.Password,
        )
        if not ok:
            return
        new_pin = new_pin.strip()
        if len(new_pin) < 4 or not new_pin.isdigit():
            QMessageBox.warning(self, "گذرواژه", "گذرواژه باید حداقل 4 رقم و فقط عدد باشد.")
            return

        confirm_pin, ok = QInputDialog.getText(
            self,
            "تایید گذرواژه",
            "گذرواژه را مجددا وارد کنید:",
            QLineEdit.EchoMode.Password,
        )
        if not ok:
            return
        if confirm_pin.strip() != new_pin:
            QMessageBox.warning(self, "گذرواژه", "گذرواژه تایید با مقدار جدید یکسان نیست.")
            return

        self.settings["app_pin_hash"] = self._hash_pin(new_pin)
        self.settings["app_lock_enabled"] = True
        self.persist_settings()
        self.settings_page.refresh_values(self.settings)
        self._notify_success("گذرواژه", "گذرواژه با موفقیت تنظیم شد.")

    def clear_pin(self) -> None:
        if not str(self.settings.get("app_pin_hash", "")).strip():
            QMessageBox.information(self, "گذرواژه", "گذرواژه فعالی وجود ندارد.")
            return
        if not self._confirm_sensitive_action("حذف گذرواژه"):
            return

        self.settings["app_pin_hash"] = ""
        self.settings["app_lock_enabled"] = False
        self.persist_settings()
        self.settings_page.refresh_values(self.settings)
        self._notify_success("گذرواژه", "گذرواژه حذف شد.")

    def export_settings_to_json(self, include_api_key: bool) -> None:
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "ذخیره تنظیمات",
            str(PROJECT_ROOT / "sms_panel_settings_backup.json"),
            "JSON Files (*.json)",
        )
        if not file_name:
            return

        payload = dict(self.settings)
        payload["app_pin_hash"] = ""
        if not include_api_key:
            payload["api_key"] = ""
        try:
            Path(file_name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            QMessageBox.critical(self, "تنظیمات", f"خروجی تنظیمات انجام نشد:\n{exc}")
            return

        self._notify_success("تنظیمات", "فایل تنظیمات با موفقیت ذخیره شد.")

    def import_settings_from_json(self) -> None:
        if not self._confirm_sensitive_action("ورود تنظیمات از فایل"):
            return

        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "ورود تنظیمات",
            str(PROJECT_ROOT),
            "JSON Files (*.json)",
        )
        if not file_name:
            return

        try:
            loaded = json.loads(Path(file_name).read_text(encoding="utf-8"))
        except Exception as exc:
            QMessageBox.critical(self, "تنظیمات", f"فایل تنظیمات خوانده نشد:\n{exc}")
            return

        if not isinstance(loaded, dict):
            QMessageBox.warning(self, "تنظیمات", "ساختار فایل تنظیمات نامعتبر است.")
            return

        preserved_contacts = self.settings.get("contacts", [])
        preserved_drafts = self.settings.get("drafts", [])

        self.settings.update(loaded)
        self.settings["contacts"] = normalize_contacts(loaded.get("contacts", preserved_contacts))
        self.settings["drafts"] = normalize_drafts(loaded.get("drafts", preserved_drafts))
        self.persist_settings()
        self.settings = self.store.load()

        self._apply_runtime_settings()
        self.save_contacts(self.settings["contacts"])
        self.save_drafts(self.settings["drafts"])
        self.refresh_all()
        self._notify_success("تنظیمات", "تنظیمات از فایل بازیابی شد.")

    def backup_contacts_and_drafts(self) -> None:
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "ذخیره بکاپ مخاطبین و پیش نویس ها",
            str(PROJECT_ROOT / "contacts_drafts_backup.json"),
            "JSON Files (*.json)",
        )
        if not file_name:
            return

        payload = {
            "contacts": self.settings.get("contacts", []),
            "drafts": self.settings.get("drafts", []),
            "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        try:
            Path(file_name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            QMessageBox.critical(self, "پشتیبان گیری", f"ذخیره بکاپ انجام نشد:\n{exc}")
            return

        self._notify_success("پشتیبان گیری", "بکاپ مخاطبین و پیش نویس ها ذخیره شد.")

    def restore_contacts_and_drafts(self) -> None:
        if not self._confirm_sensitive_action("بازیابی مخاطبین و پیش نویس ها"):
            return

        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "بازیابی مخاطبین و پیش نویس ها",
            str(PROJECT_ROOT),
            "JSON Files (*.json)",
        )
        if not file_name:
            return

        try:
            payload = json.loads(Path(file_name).read_text(encoding="utf-8"))
        except Exception as exc:
            QMessageBox.critical(self, "بازیابی", f"فایل بکاپ خوانده نشد:\n{exc}")
            return

        if not isinstance(payload, dict):
            QMessageBox.warning(self, "بازیابی", "ساختار فایل بکاپ نامعتبر است.")
            return

        contacts = normalize_contacts(payload.get("contacts", []))
        drafts = normalize_drafts(payload.get("drafts", []))
        self.save_contacts(contacts)
        self.save_drafts(drafts)
        self._notify_success("بازیابی", "مخاطبین و پیش نویس ها بازیابی شد.")

    def reset_settings_to_defaults(self) -> None:
        if not self._confirm_sensitive_action("بازگشت به تنظیمات پیش فرض"):
            return

        defaults = self.store.defaults()
        defaults["api_key"] = str(self.settings.get("api_key", "")).strip()
        defaults["app_pin_hash"] = str(self.settings.get("app_pin_hash", "")).strip()
        defaults["contacts"] = self.settings.get("contacts", [])
        defaults["drafts"] = self.settings.get("drafts", [])

        self.settings = defaults
        self.client.update_api_key(defaults.get("api_key", ""))
        self._apply_runtime_settings()
        self.save_contacts(normalize_contacts(self.settings.get("contacts", [])))
        self.save_drafts(normalize_drafts(self.settings.get("drafts", [])))
        self.persist_settings()
        self.refresh_all()
        self._notify_success("تنظیمات", "تنظیمات به حالت پیش فرض بازگشت.")

    def copy_diagnostic_info(self) -> None:
        info = [
            f"App Version: {APP_VERSION}",
            f"Python: {platform.python_version()}",
            f"OS: {platform.platform()}",
            f"Theme: {self.settings.get('theme', 'light')}",
            f"Color Scheme: {self.settings.get('color_scheme', 'peach_eggplant')}",
            f"Log Level: {self.settings.get('log_level', 'INFO')}",
            f"API Timeout: {self.settings.get('api_timeout_sec', 25)}",
            f"API Retry: {self.settings.get('api_retry_count', 1)}",
            f"Last API Success: {self.settings.get('last_api_success_at', '-')}",
        ]
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setText("\n".join(info))
            self._notify_success("عیب یابی", "اطلاعات فنی در کلیپ بورد کپی شد.")

    def set_status(self, text: str, badge_class: str) -> None:
        self.status_badge.setText(text)
        self.status_badge.setProperty("class", badge_class)
        self.status_badge.style().unpolish(self.status_badge)
        self.status_badge.style().polish(self.status_badge)

    def persist_settings(self) -> None:
        try:
            ErrorHandler.log_debug("Persisting settings to disk")
            self._persist_settings_impl()
        except Exception as e:
            ErrorHandler.handle_file_error(str(self.store.path), e, self)

    def _persist_settings_impl(self) -> None:
        self.store.save(self.settings)

    def change_api_key(self) -> None:
        try:
            self._change_api_key_impl()
        except Exception as e:
            ErrorHandler.show_error(
                "خطا در تغییر API Key",
                "خطایی در تغییر کلید API رخ داد",
                e,
                "API Key Change",
                self,
            )

    def _change_api_key_impl(self) -> None:
        if not self._confirm_sensitive_action("تغییر API Key"):
            return
        dialog = ApiKeyDialog(self.settings.get("api_key", ""), self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_key = dialog.api_key()
            ErrorHandler.log_info("API Key changed successfully")
            self.settings["api_key"] = new_key
            self.persist_settings()
            API_KEY_FILE.write_text(new_key, encoding="utf-8")
            self.client.update_api_key(new_key)
            self.refresh_all()
