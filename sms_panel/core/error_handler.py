from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QWidget

logger = logging.getLogger("sms_panel")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(stream_handler)


class ErrorHandler:
    """کلاس مدیریت خطاها در سراسر برنامه"""

    @staticmethod
    def configure_logging(level_name: str = "INFO", log_file_path: str = "") -> None:
        level = getattr(logging, str(level_name).upper(), logging.INFO)
        logger.setLevel(level)

        for handler in list(logger.handlers):
            if isinstance(handler, logging.FileHandler):
                logger.removeHandler(handler)
                handler.close()

        path_text = str(log_file_path or "").strip()
        if not path_text:
            return

        try:
            path = Path(path_text)
            path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(path, encoding="utf-8")
            file_handler.setLevel(level)
            file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
            logger.addHandler(file_handler)
        except Exception as exc:
            logger.warning(f"Log file configuration failed: {exc}")

    @staticmethod
    def show_error(
        title: str,
        message: str,
        exception: Optional[Exception] = None,
        context: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        """نمایش دیالوگ خطا به کاربر"""
        from sms_panel.ui.dialogs.error_log_dialog import ErrorLogDialog

        if exception:
            logger.error(f"{context or 'Error'}: {message}", exc_info=exception)
        else:
            logger.error(f"{context or 'Error'}: {message}")

        dialog = ErrorLogDialog(
            error_title=title,
            error_message=message,
            exception=exception,
            context=context,
            parent=parent,
        )
        dialog.exec()

    @staticmethod
    def handle_api_error(
        error: Exception, operation: str, parent: Optional[QWidget] = None
    ) -> None:
        """مدیریت خطاهای API"""
        error_messages = {
            "ConnectionError": "خطا در برقراری ارتباط با سرور. لطفاً اتصال اینترنت خود را بررسی کنید.",
            "Timeout": "زمان اتصال به سرور به پایان رسید. لطفاً دوباره تلاش کنید.",
            "HTTPError": "خطا در دریافت پاسخ از سرور. کد وضعیت نامعتبر است.",
            "JSONDecodeError": "خطا در تجزیه پاسخ سرور. فرمت داده‌ها نامعتبر است.",
            "KeyError": "داده‌های دریافتی از سرور ناقص است.",
            "ValueError": "مقدار ورودی نامعتبر است.",
        }

        error_type = type(error).__name__
        user_message = error_messages.get(error_type, f"خطای غیرمنتظره: {str(error)}")

        ErrorHandler.show_error(
            title=f"خطا در {operation}",
            message=user_message,
            exception=error,
            context=f"API Operation: {operation}",
            parent=parent,
        )

    @staticmethod
    def handle_validation_error(
        field_name: str, message: str, parent: Optional[QWidget] = None
    ) -> None:
        """مدیریت خطاهای اعتبارسنجی"""
        ErrorHandler.show_error(
            title="خطای اعتبارسنجی",
            message=f"فیلد '{field_name}': {message}",
            context="Validation Error",
            parent=parent,
        )

    @staticmethod
    def handle_file_error(
        file_path: str, error: Exception, parent: Optional[QWidget] = None
    ) -> None:
        """مدیریت خطاهای فایل"""
        ErrorHandler.show_error(
            title="خطا در عملیات فایل",
            message=f"خطا در کار با فایل: {file_path}\n{str(error)}",
            exception=error,
            context=f"File Operation: {file_path}",
            parent=parent,
        )

    @staticmethod
    def log_info(message: str) -> None:
        """لاگ اطلاعات عمومی"""
        logger.info(message)

    @staticmethod
    def log_warning(message: str) -> None:
        """لاگ هشدار"""
        logger.warning(message)

    @staticmethod
    def log_debug(message: str) -> None:
        """لاگ دیباگ"""
        logger.debug(message)
