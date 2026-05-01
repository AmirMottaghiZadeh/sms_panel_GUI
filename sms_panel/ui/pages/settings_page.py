from __future__ import annotations

from typing import Any

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from sms_panel.config import PROJECT_ROOT
from sms_panel.ui.widgets import CardFrame, PrimaryButton, SecondaryButton


class SettingsPage(QWidget):
    settings_patch_requested = pyqtSignal(dict)
    api_change_requested = pyqtSignal()
    api_test_requested = pyqtSignal()
    export_settings_requested = pyqtSignal(bool)
    import_settings_requested = pyqtSignal()
    backup_data_requested = pyqtSignal()
    restore_data_requested = pyqtSignal()
    reset_defaults_requested = pyqtSignal()
    set_pin_requested = pyqtSignal()
    clear_pin_requested = pyqtSignal()
    copy_diagnostics_requested = pyqtSignal()

    def __init__(self, settings: dict[str, Any], app_version: str) -> None:
        super().__init__()
        self.app_version = app_version

        root = QVBoxLayout(self)
        title = QLabel("تنظیمات")
        title.setProperty("class", "fa-header")
        root.addWidget(title)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        root.addWidget(self.scroll, 1)

        content = QWidget()
        self.scroll.setWidget(content)
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setSpacing(12)

        self._build_identity_section()
        self._build_api_section()
        self._build_send_defaults_section()
        self._build_data_section()
        self._build_contacts_drafts_section()
        self._build_notifications_section()
        self._build_appearance_section()
        self._build_security_section()
        self._build_advanced_section()
        self._build_about_section()
        self.content_layout.addStretch(1)

        self.refresh_values(settings)

    def _section_card(self, title: str, note: str) -> tuple[CardFrame, QVBoxLayout]:
        card = CardFrame()
        layout = QVBoxLayout(card)

        section_title = QLabel(title)
        section_title.setProperty("class", "fa-subtitle")
        layout.addWidget(section_title)

        if note:
            helper = QLabel(note)
            helper.setProperty("class", "fa-note")
            helper.setWordWrap(True)
            layout.addWidget(helper)

        self.content_layout.addWidget(card)
        return card, layout

    def _build_identity_section(self) -> None:
        _, layout = self._section_card(
            "1) هویت پنل",
            "نام پنل، سازمان و لوگوی برند را تنظیم کنید.",
        )

        form = QFormLayout()
        self.panel_title_input = QLineEdit()
        self.organization_name_input = QLineEdit()
        self.logo_path_input = QLineEdit()
        self.logo_path_input.setPlaceholderText("مسیر فایل png/jpg")

        form.addRow("نام پنل", self.panel_title_input)
        form.addRow("نام سازمان", self.organization_name_input)
        form.addRow("لوگو/آیکون", self.logo_path_input)
        layout.addLayout(form)

        logo_actions = QHBoxLayout()
        browse_logo_btn = SecondaryButton("انتخاب فایل لوگو")
        browse_logo_btn.clicked.connect(self._browse_logo)
        clear_logo_btn = SecondaryButton("حذف لوگو سفارشی")
        clear_logo_btn.clicked.connect(lambda: self.logo_path_input.setText(""))
        save_identity_btn = PrimaryButton("ذخیره هویت پنل")
        save_identity_btn.clicked.connect(self._save_identity)

        logo_actions.addWidget(browse_logo_btn)
        logo_actions.addWidget(clear_logo_btn)
        logo_actions.addStretch(1)
        logo_actions.addWidget(save_identity_btn)
        layout.addLayout(logo_actions)

    def _build_api_section(self) -> None:
        _, layout = self._section_card(
            "2) حساب و اتصال API",
            "کلید API، تست اتصال، Timeout و Retry را مدیریت کنید.",
        )

        form = QFormLayout()
        self.api_timeout_spin = QSpinBox()
        self.api_timeout_spin.setRange(5, 120)
        self.api_timeout_spin.setSuffix(" ثانیه")

        self.api_retry_spin = QSpinBox()
        self.api_retry_spin.setRange(0, 5)
        self.api_retry_spin.setSuffix(" بار")

        self.last_api_success_label = QLabel("-")
        self.last_api_success_label.setProperty("class", "fa-note")

        form.addRow("Timeout", self.api_timeout_spin)
        form.addRow("Retry", self.api_retry_spin)
        form.addRow("آخرین اتصال موفق", self.last_api_success_label)
        layout.addLayout(form)

        row = QHBoxLayout()
        api_key_button = PrimaryButton("تغییر API Key")
        api_key_button.clicked.connect(self.api_change_requested.emit)
        test_button = SecondaryButton("تست اتصال API")
        test_button.clicked.connect(self.api_test_requested.emit)
        save_api_btn = SecondaryButton("ذخیره تنظیمات شبکه")
        save_api_btn.clicked.connect(self._save_api)

        row.addWidget(api_key_button)
        row.addWidget(test_button)
        row.addStretch(1)
        row.addWidget(save_api_btn)
        layout.addLayout(row)

    def _build_send_defaults_section(self) -> None:
        _, layout = self._section_card(
            "3) پیش فرض های ارسال",
            "خط پیش فرض، امضا و تایید ارسال انبوه را تعیین کنید.",
        )

        form = QFormLayout()
        self.line_input = QLineEdit()
        self.signature_input = QLineEdit()
        self.signature_input.setPlaceholderText("مثال: دبیرستان دارالفنون")

        self.bulk_confirm_enabled_check = QCheckBox("قبل از ارسال انبوه تایید بگیر")
        self.bulk_confirm_threshold_spin = QSpinBox()
        self.bulk_confirm_threshold_spin.setRange(1, 100000)
        self.bulk_confirm_threshold_spin.setSuffix(" مخاطب")

        form.addRow("Line Number پیش فرض", self.line_input)
        form.addRow("امضای انتهای پیام", self.signature_input)
        form.addRow("سیاست تایید", self.bulk_confirm_enabled_check)
        form.addRow("حد آستانه تایید", self.bulk_confirm_threshold_spin)
        layout.addLayout(form)

        save_btn = PrimaryButton("ذخیره پیش فرض های ارسال")
        save_btn.clicked.connect(self._save_send_defaults)
        layout.addWidget(save_btn)

    def _build_data_section(self) -> None:
        _, layout = self._section_card(
            "4) داده و پشتیبان گیری",
            "ورود/خروجی تنظیمات، بکاپ مخاطبین و پیش نویس ها و ریست امن.",
        )

        self.include_api_check = QCheckBox("در خروجی تنظیمات، API Key هم ذخیره شود")
        layout.addWidget(self.include_api_check)

        row_a = QHBoxLayout()
        export_settings_btn = SecondaryButton("خروجی تنظیمات JSON")
        export_settings_btn.clicked.connect(lambda: self.export_settings_requested.emit(self.include_api_check.isChecked()))
        import_settings_btn = SecondaryButton("ورود تنظیمات JSON")
        import_settings_btn.clicked.connect(self.import_settings_requested.emit)
        row_a.addWidget(export_settings_btn)
        row_a.addWidget(import_settings_btn)
        layout.addLayout(row_a)

        row_b = QHBoxLayout()
        backup_btn = SecondaryButton("بکاپ مخاطبین + پیش نویس ها")
        backup_btn.clicked.connect(self.backup_data_requested.emit)
        restore_btn = SecondaryButton("بازیابی مخاطبین + پیش نویس ها")
        restore_btn.clicked.connect(self.restore_data_requested.emit)
        row_b.addWidget(backup_btn)
        row_b.addWidget(restore_btn)
        layout.addLayout(row_b)

        reset_btn = PrimaryButton("بازگشت به تنظیمات پیش فرض")
        reset_btn.clicked.connect(self.reset_defaults_requested.emit)
        layout.addWidget(reset_btn)

    def _build_contacts_drafts_section(self) -> None:
        _, layout = self._section_card(
            "5) مخاطبین و پیش نویس ها",
            "مدیریت تکراری ها، سقف پیش نویس و دسته بندی پیش فرض واردسازی.",
        )

        form = QFormLayout()
        self.contacts_default_category_input = QLineEdit()
        self.dedupe_contacts_check = QCheckBox("شماره تکراری خودکار حذف شود")
        self.max_drafts_spin = QSpinBox()
        self.max_drafts_spin.setRange(10, 1000)
        self.max_drafts_spin.setSuffix(" پیش نویس")

        form.addRow("دسته بندی پیش فرض مخاطبین", self.contacts_default_category_input)
        form.addRow("پاکسازی تکراری", self.dedupe_contacts_check)
        form.addRow("حداکثر پیش نویس", self.max_drafts_spin)
        layout.addLayout(form)

        save_btn = PrimaryButton("ذخیره تنظیمات مخاطبین/پیش نویس")
        save_btn.clicked.connect(self._save_contacts_drafts)
        layout.addWidget(save_btn)

    def _build_notifications_section(self) -> None:
        _, layout = self._section_card(
            "6) اعلان ها",
            "نوع پیام ها بعد از ارسال و خطاها را کنترل کنید.",
        )

        self.notify_success_check = QCheckBox("اعلان موفقیت ارسال نمایش داده شود")
        self.notify_error_check = QCheckBox("اعلان خطای ارسال نمایش داده شود")
        self.popup_notifications_check = QCheckBox("پیام های Popup فعال باشد")
        self.beep_on_error_check = QCheckBox("در خطا صدای هشدار پخش شود")

        layout.addWidget(self.notify_success_check)
        layout.addWidget(self.notify_error_check)
        layout.addWidget(self.popup_notifications_check)
        layout.addWidget(self.beep_on_error_check)

        save_btn = PrimaryButton("ذخیره تنظیمات اعلان")
        save_btn.clicked.connect(self._save_notifications)
        layout.addWidget(save_btn)

    def _build_appearance_section(self) -> None:
        _, layout = self._section_card(
            "7) ظاهر و تجربه کاربری",
            "تم، پالت رنگ، اندازه فونت و تراکم نمایش.",
        )

        form = QFormLayout()

        self.theme_combo = QComboBox()
        self.theme_combo.addItem("روشن", "light")
        self.theme_combo.addItem("تیره", "dark")

        self.scheme_combo = QComboBox()
        self.scheme_combo.addItem("هلویی - بادمجانی", "peach_eggplant")
        self.scheme_combo.addItem("قهوه ای - خردلی", "brown_mustard")
        self.scheme_combo.addItem("نارنجی - مشکی", "orange_black")
        self.scheme_combo.addItem("بژ - قرمز گرادیانت", "beige_red_gradient")
        self.scheme_combo.addItem("سرمه ای - طلایی", "school_navy_gold")

        self.font_scale_combo = QComboBox()
        self.font_scale_combo.addItem("کوچک", "small")
        self.font_scale_combo.addItem("نرمال", "normal")
        self.font_scale_combo.addItem("بزرگ", "large")

        self.ui_density_combo = QComboBox()
        self.ui_density_combo.addItem("فشرده", "compact")
        self.ui_density_combo.addItem("راحت", "comfortable")

        form.addRow("تم برنامه", self.theme_combo)
        form.addRow("مجموعه رنگ", self.scheme_combo)
        form.addRow("اندازه فونت", self.font_scale_combo)
        form.addRow("تراکم نمایش", self.ui_density_combo)
        layout.addLayout(form)

        self.theme_combo.currentIndexChanged.connect(self._save_appearance)
        self.scheme_combo.currentIndexChanged.connect(self._save_appearance)
        self.font_scale_combo.currentIndexChanged.connect(self._save_appearance)
        self.ui_density_combo.currentIndexChanged.connect(self._save_appearance)

    def _build_security_section(self) -> None:
        _, layout = self._section_card(
            "8) امنیت و حریم خصوصی",
            "قفل برنامه، ماسک شماره ها و تایید دو مرحله ای برای عملیات حساس.",
        )

        self.app_lock_check = QCheckBox("قفل برنامه با PIN فعال باشد")
        self.mask_numbers_check = QCheckBox("شماره ها در جداول ماسک شوند")
        self.sensitive_confirm_check = QCheckBox("برای عملیات حساس تایید اضافه گرفته شود")
        self.pin_status_label = QLabel("وضعیت PIN: تعریف نشده")
        self.pin_status_label.setProperty("class", "fa-note")

        layout.addWidget(self.app_lock_check)
        layout.addWidget(self.mask_numbers_check)
        layout.addWidget(self.sensitive_confirm_check)
        layout.addWidget(self.pin_status_label)

        pin_row = QHBoxLayout()
        set_pin_btn = SecondaryButton("تنظیم/تغییر PIN")
        set_pin_btn.clicked.connect(self.set_pin_requested.emit)
        clear_pin_btn = SecondaryButton("حذف PIN")
        clear_pin_btn.clicked.connect(self.clear_pin_requested.emit)
        save_btn = PrimaryButton("ذخیره تنظیمات امنیت")
        save_btn.clicked.connect(self._save_security)

        pin_row.addWidget(set_pin_btn)
        pin_row.addWidget(clear_pin_btn)
        pin_row.addStretch(1)
        pin_row.addWidget(save_btn)
        layout.addLayout(pin_row)

    def _build_advanced_section(self) -> None:
        _, layout = self._section_card(
            "9) پیشرفته و عیب یابی",
            "سطح لاگ، مسیر فایل لاگ و کپی اطلاعات فنی.",
        )

        form = QFormLayout()
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_file_path_input = QLineEdit()
        self.log_file_path_input.setPlaceholderText("مثال: /home/user/sms_panel.log")
        form.addRow("سطح لاگ", self.log_level_combo)
        form.addRow("مسیر لاگ", self.log_file_path_input)
        layout.addLayout(form)

        row = QHBoxLayout()
        browse_log_btn = SecondaryButton("انتخاب مسیر لاگ")
        browse_log_btn.clicked.connect(self._browse_log_path)
        clear_log_btn = SecondaryButton("حذف مسیر لاگ")
        clear_log_btn.clicked.connect(lambda: self.log_file_path_input.setText(""))
        copy_diag_btn = SecondaryButton("کپی اطلاعات فنی")
        copy_diag_btn.clicked.connect(self.copy_diagnostics_requested.emit)
        save_btn = PrimaryButton("ذخیره تنظیمات لاگ")
        save_btn.clicked.connect(self._save_advanced)

        row.addWidget(browse_log_btn)
        row.addWidget(clear_log_btn)
        row.addWidget(copy_diag_btn)
        row.addStretch(1)
        row.addWidget(save_btn)
        layout.addLayout(row)

    def _build_about_section(self) -> None:
        _, layout = self._section_card(
            "10) درباره برنامه",
            "اطلاعات نسخه، مستندات و راه های پشتیبانی.",
        )

        version_label = QLabel(f"نسخه برنامه: {self.app_version}")
        version_label.setProperty("class", "fa-note")

        docs_label = QLabel("مستندات: README.md | پشتیبانی: Issues پروژه")
        docs_label.setProperty("class", "fa-note")

        layout.addWidget(version_label)
        layout.addWidget(docs_label)

    def refresh_values(self, settings: dict[str, Any]) -> None:
        self._set_line_text(self.panel_title_input, settings.get("panel_title", ""))
        self._set_line_text(self.organization_name_input, settings.get("organization_name", ""))
        self._set_line_text(self.logo_path_input, settings.get("brand_logo_path", ""))

        self._set_combo_data(self.theme_combo, str(settings.get("theme", "light")))
        self._set_combo_data(self.scheme_combo, str(settings.get("color_scheme", "peach_eggplant")))
        self._set_combo_data(self.font_scale_combo, str(settings.get("font_scale", "normal")))
        self._set_combo_data(self.ui_density_combo, str(settings.get("ui_density", "comfortable")))

        self._set_line_text(self.line_input, settings.get("line_number", ""))
        self._set_line_text(self.signature_input, settings.get("message_signature", ""))
        self.bulk_confirm_enabled_check.setChecked(bool(settings.get("bulk_confirm_enabled", True)))
        self.bulk_confirm_threshold_spin.setValue(self._safe_int(settings.get("bulk_confirm_threshold"), 50))

        self.api_timeout_spin.setValue(self._safe_int(settings.get("api_timeout_sec"), 25))
        self.api_retry_spin.setValue(self._safe_int(settings.get("api_retry_count"), 1))
        last_ok = str(settings.get("last_api_success_at", "")).strip() or "ثبت نشده"
        self.last_api_success_label.setText(last_ok)

        self._set_line_text(
            self.contacts_default_category_input,
            settings.get("contacts_default_category", "عمومی"),
        )
        self.dedupe_contacts_check.setChecked(bool(settings.get("dedupe_contacts_on_save", True)))
        self.max_drafts_spin.setValue(self._safe_int(settings.get("max_drafts"), 100))

        self.notify_success_check.setChecked(bool(settings.get("notify_on_success", True)))
        self.notify_error_check.setChecked(bool(settings.get("notify_on_error", True)))
        self.popup_notifications_check.setChecked(bool(settings.get("show_popup_notifications", True)))
        self.beep_on_error_check.setChecked(bool(settings.get("beep_on_error", False)))

        self.mask_numbers_check.setChecked(bool(settings.get("mask_mobile_numbers", False)))
        self.app_lock_check.setChecked(bool(settings.get("app_lock_enabled", False)))
        self.sensitive_confirm_check.setChecked(bool(settings.get("require_sensitive_action_confirmation", True)))

        pin_hash = str(settings.get("app_pin_hash", "")).strip()
        self.pin_status_label.setText("وضعیت PIN: تنظیم شده" if pin_hash else "وضعیت PIN: تعریف نشده")

        self._set_combo_text(self.log_level_combo, str(settings.get("log_level", "INFO")).upper())
        self._set_line_text(self.log_file_path_input, settings.get("log_file_path", ""))

    def _browse_logo(self) -> None:
        filters = "Image Files (*.png *.jpg *.jpeg *.bmp *.webp)"
        file_name, _ = QFileDialog.getOpenFileName(self, "انتخاب لوگو", str(PROJECT_ROOT), filters)
        if file_name:
            self.logo_path_input.setText(file_name)

    def _browse_log_path(self) -> None:
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "انتخاب مسیر فایل لاگ",
            str(PROJECT_ROOT / "sms_panel.log"),
            "Log Files (*.log);;All Files (*)",
        )
        if file_name:
            self.log_file_path_input.setText(file_name)

    def _save_identity(self) -> None:
        self.settings_patch_requested.emit(
            {
                "panel_title": self.panel_title_input.text().strip(),
                "organization_name": self.organization_name_input.text().strip(),
                "brand_logo_path": self.logo_path_input.text().strip(),
            }
        )

    def _save_api(self) -> None:
        self.settings_patch_requested.emit(
            {
                "api_timeout_sec": self.api_timeout_spin.value(),
                "api_retry_count": self.api_retry_spin.value(),
            }
        )

    def _save_send_defaults(self) -> None:
        self.settings_patch_requested.emit(
            {
                "line_number": self.line_input.text().strip(),
                "message_signature": self.signature_input.text().strip(),
                "bulk_confirm_enabled": self.bulk_confirm_enabled_check.isChecked(),
                "bulk_confirm_threshold": self.bulk_confirm_threshold_spin.value(),
            }
        )

    def _save_contacts_drafts(self) -> None:
        self.settings_patch_requested.emit(
            {
                "contacts_default_category": self.contacts_default_category_input.text().strip() or "عمومی",
                "dedupe_contacts_on_save": self.dedupe_contacts_check.isChecked(),
                "max_drafts": self.max_drafts_spin.value(),
            }
        )

    def _save_notifications(self) -> None:
        self.settings_patch_requested.emit(
            {
                "notify_on_success": self.notify_success_check.isChecked(),
                "notify_on_error": self.notify_error_check.isChecked(),
                "show_popup_notifications": self.popup_notifications_check.isChecked(),
                "beep_on_error": self.beep_on_error_check.isChecked(),
            }
        )

    def _save_appearance(self) -> None:
        self.settings_patch_requested.emit(
            {
                "theme": str(self.theme_combo.currentData() or "light"),
                "color_scheme": str(self.scheme_combo.currentData() or "peach_eggplant"),
                "font_scale": str(self.font_scale_combo.currentData() or "normal"),
                "ui_density": str(self.ui_density_combo.currentData() or "comfortable"),
            }
        )

    def _save_security(self) -> None:
        self.settings_patch_requested.emit(
            {
                "app_lock_enabled": self.app_lock_check.isChecked(),
                "mask_mobile_numbers": self.mask_numbers_check.isChecked(),
                "require_sensitive_action_confirmation": self.sensitive_confirm_check.isChecked(),
            }
        )

    def _save_advanced(self) -> None:
        self.settings_patch_requested.emit(
            {
                "log_level": self.log_level_combo.currentText().strip().upper(),
                "log_file_path": self.log_file_path_input.text().strip(),
            }
        )

    @staticmethod
    def _set_line_text(widget: QLineEdit, value: Any) -> None:
        widget.blockSignals(True)
        widget.setText(str(value or ""))
        widget.blockSignals(False)

    @staticmethod
    def _set_combo_data(widget: QComboBox, value: str) -> None:
        index = widget.findData(value)
        widget.blockSignals(True)
        widget.setCurrentIndex(index if index >= 0 else 0)
        widget.blockSignals(False)

    @staticmethod
    def _set_combo_text(widget: QComboBox, value: str) -> None:
        index = widget.findText(value)
        widget.blockSignals(True)
        widget.setCurrentIndex(index if index >= 0 else 0)
        widget.blockSignals(False)

    @staticmethod
    def _safe_int(value: Any, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
