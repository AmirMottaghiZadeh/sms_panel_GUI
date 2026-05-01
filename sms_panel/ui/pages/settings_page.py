from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from sms_panel.ui.widgets import CardFrame, PrimaryButton, SecondaryButton


class SettingsPage(QWidget):
    theme_changed = pyqtSignal(str)
    color_scheme_changed = pyqtSignal(str)
    api_change_requested = pyqtSignal()
    line_number_changed = pyqtSignal(str)
    panel_title_changed = pyqtSignal(str)

    def __init__(self, theme: str, line_number: str, color_scheme: str, panel_title: str) -> None:
        super().__init__()
        root = QVBoxLayout(self)

        title = QLabel("تنظیمات")
        title.setProperty("class", "fa-header")
        root.addWidget(title)

        panel = CardFrame()
        panel_layout = QVBoxLayout(panel)

        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("تم برنامه"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        self.theme_combo.setCurrentText(theme)
        self.theme_combo.currentTextChanged.connect(self.theme_changed.emit)
        theme_row.addWidget(self.theme_combo)

        scheme_row = QHBoxLayout()
        scheme_row.addWidget(QLabel("مجموعه رنگ"))
        self.scheme_combo = QComboBox()
        self.scheme_combo.addItem("هلویی + بادمجانی", "peach_eggplant")
        self.scheme_combo.addItem("قهوه ای + خردلی", "brown_mustard")
        self.scheme_combo.addItem("نارنجی + مشکی", "orange_black")
        self.scheme_combo.addItem("بژ + گرادیانت قرمز", "beige_red_gradient")
        self.scheme_combo.addItem("مدرسه ای (سرمه ای + طلایی)", "school_navy_gold")
        self._set_scheme_value(color_scheme)
        self.scheme_combo.currentIndexChanged.connect(self._emit_scheme_change)
        scheme_row.addWidget(self.scheme_combo)

        line_row = QHBoxLayout()
        line_row.addWidget(QLabel("Line Number پیش فرض"))
        self.line_input = QLineEdit(line_number)
        save_line = SecondaryButton("ذخیره خط")
        save_line.clicked.connect(lambda: self.line_number_changed.emit(self.line_input.text().strip()))
        line_row.addWidget(self.line_input)
        line_row.addWidget(save_line)

        title_row = QHBoxLayout()
        title_row.addWidget(QLabel("نام پنل"))
        self.panel_title_input = QLineEdit(panel_title)
        save_title = SecondaryButton("ذخیره نام پنل")
        save_title.clicked.connect(lambda: self.panel_title_changed.emit(self.panel_title_input.text().strip()))
        title_row.addWidget(self.panel_title_input)
        title_row.addWidget(save_title)

        api_button = PrimaryButton("تغییر API Key")
        api_button.clicked.connect(self.api_change_requested.emit)

        panel_layout.addLayout(theme_row)
        panel_layout.addLayout(scheme_row)
        panel_layout.addLayout(line_row)
        panel_layout.addLayout(title_row)
        panel_layout.addWidget(api_button)

        root.addWidget(panel)
        root.addStretch(1)

    def _emit_scheme_change(self) -> None:
        data = self.scheme_combo.currentData()
        if isinstance(data, str):
            self.color_scheme_changed.emit(data)

    def _set_scheme_value(self, scheme_key: str) -> None:
        index = self.scheme_combo.findData(scheme_key)
        if index < 0:
            index = 0
        self.scheme_combo.setCurrentIndex(index)
