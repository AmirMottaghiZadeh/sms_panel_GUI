from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from sms_panel.ui.widgets import PrimaryButton, SecondaryButton


class ApiKeyDialog(QDialog):
    def __init__(self, current_value: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("تنظیم API وب سرویس SMS.ir")
        self.setModal(True)
        self.resize(520, 230)

        root = QVBoxLayout(self)
        title = QLabel("کلید API پیامکی را وارد کنید")
        title.setProperty("class", "fa-title")
        root.addWidget(title)

        info = QLabel("این کلید در فایل تنظیمات ذخیره می شود و در اجرای بعدی دیگر این پنجره نمایش داده نخواهد شد.")
        info.setWordWrap(True)
        info.setProperty("class", "fa-note")
        root.addWidget(info)

        self.api_input = QLineEdit()
        self.api_input.setPlaceholderText("API Key")
        self.api_input.setText(current_value)
        self.api_input.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)
        root.addWidget(self.api_input)

        buttons = QHBoxLayout()
        self.save_button = PrimaryButton("ذخیره و ادامه")
        self.cancel_button = SecondaryButton("خروج")
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        buttons.addStretch(1)
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.save_button)
        root.addLayout(buttons)

    def api_key(self) -> str:
        return self.api_input.text().strip()

    def accept(self) -> None:
        if not self.api_key():
            QMessageBox.warning(self, "API Key", "لطفا کلید API را وارد کنید.")
            return
        super().accept()
