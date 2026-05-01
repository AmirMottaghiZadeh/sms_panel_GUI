from __future__ import annotations

import traceback
from datetime import datetime
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


class ErrorLogDialog(QDialog):
    """دیالوگ حرفه‌ای برای نمایش خطاها و لاگ‌ها"""

    def __init__(
        self,
        error_title: str,
        error_message: str,
        exception: Optional[Exception] = None,
        context: Optional[str] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("گزارش خطا")
        self.setModal(True)
        self.resize(700, 500)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # عنوان خطا
        title_label = QLabel(error_title)
        title_label.setProperty("class", "fa-title")
        title_label.setStyleSheet("color: #C0392B; font-weight: bold;")
        layout.addWidget(title_label)

        # پیام خطا
        message_label = QLabel(error_message)
        message_label.setProperty("class", "fa-note")
        message_label.setWordWrap(True)
        layout.addWidget(message_label)

        # زمان وقوع خطا
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time_label = QLabel(f"زمان: {timestamp}")
        time_label.setProperty("class", "muted")
        layout.addWidget(time_label)

        # جزئیات فنی
        details_label = QLabel("جزئیات فنی:")
        details_label.setProperty("class", "fa-subtitle")
        layout.addWidget(details_label)

        # ناحیه متن لاگ
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(
            """
            QTextEdit {
                font-family: 'Courier New', monospace;
                font-size: 11px;
                background-color: #2b2b2b;
                color: #f8f8f2;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px;
            }
            """
        )

        # ساخت محتوای لاگ
        log_content = self._build_log_content(error_message, exception, context)
        self.log_text.setPlainText(log_content)

        layout.addWidget(self.log_text, 1)

        # دکمه‌ها
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        copy_btn = QPushButton("کپی لاگ")
        copy_btn.clicked.connect(self._copy_log)
        copy_btn.setMinimumWidth(100)
        button_layout.addWidget(copy_btn)

        close_btn = QPushButton("بستن")
        close_btn.clicked.connect(self.accept)
        close_btn.setMinimumWidth(100)
        close_btn.setDefault(True)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def _build_log_content(
        self, error_message: str, exception: Optional[Exception], context: Optional[str]
    ) -> str:
        """ساخت محتوای کامل لاگ"""
        lines = []
        lines.append("=" * 70)
        lines.append("گزارش خطا - SMS Panel")
        lines.append("=" * 70)
        lines.append(f"زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        if context:
            lines.append(f"محل وقوع: {context}")
            lines.append("")

        lines.append("پیام خطا:")
        lines.append(error_message)
        lines.append("")

        if exception:
            lines.append("نوع خطا:")
            lines.append(f"{type(exception).__name__}: {str(exception)}")
            lines.append("")

            lines.append("Stack Trace:")
            tb_lines = traceback.format_exception(type(exception), exception, exception.__traceback__)
            lines.extend("".join(tb_lines).split("\n"))

        lines.append("")
        lines.append("=" * 70)

        return "\n".join(lines)

    def _copy_log(self) -> None:
        """کپی کردن لاگ به کلیپ‌بورد"""
        from PyQt6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(self.log_text.toPlainText())

            # نمایش پیام موفقیت
            self.log_text.setStyleSheet(
                self.log_text.styleSheet() + "\nQTextEdit { border: 2px solid #2ecc71; }"
            )
            # بازگشت به حالت عادی بعد از 1 ثانیه
            from PyQt6.QtCore import QTimer

            QTimer.singleShot(1000, self._reset_log_style)

    def _reset_log_style(self) -> None:
        """بازگشت استایل لاگ به حالت عادی"""
        self.log_text.setStyleSheet(
            """
            QTextEdit {
                font-family: 'Courier New', monospace;
                font-size: 11px;
                background-color: #2b2b2b;
                color: #f8f8f2;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px;
            }
            """
        )
