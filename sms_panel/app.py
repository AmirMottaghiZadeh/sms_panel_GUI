from __future__ import annotations

import sys
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QDialog, QInputDialog, QLineEdit

from sms_panel.config import API_KEY_FILE, APP_ICON_FILE, SETTINGS_FILE
from sms_panel.services.settings_store import SettingsStore
from sms_panel.ui.dialogs.api_key_dialog import ApiKeyDialog
from sms_panel.ui.main_window import MainWindow


def detect_default_api_key(settings: dict[str, Any]) -> str:
    if settings.get("api_key"):
        return str(settings["api_key"]).strip()

    if API_KEY_FILE.exists():
        return API_KEY_FILE.read_text(encoding="utf-8").strip()

    return ""


def ensure_api_key(store: SettingsStore, settings: dict[str, Any]) -> str:
    api_key = detect_default_api_key(settings)

    if api_key:
        settings["api_key"] = api_key
        store.save(settings)
        return api_key

    dialog = ApiKeyDialog()
    if dialog.exec() != QDialog.DialogCode.Accepted:
        raise SystemExit(0)

    api_key = dialog.api_key()
    settings["api_key"] = api_key
    store.save(settings)
    API_KEY_FILE.write_text(api_key, encoding="utf-8")
    return api_key


def ensure_panel_title(store: SettingsStore, settings: dict[str, Any]) -> str:
    panel_title = str(settings.get("panel_title", "")).strip()
    if panel_title:
        return panel_title

    title, ok = QInputDialog.getText(
        None,
        "تنظیم نام پنل",
        "نام پنل پیامکی را وارد کنید:",
        QLineEdit.EchoMode.Normal,
        "پنل پیامکی دسکتاپ",
    )
    panel_title = title.strip() if ok and title.strip() else "پنل پیامکی دسکتاپ"
    settings["panel_title"] = panel_title
    store.save(settings)
    return panel_title


def apply_fusion_style(app: QApplication) -> None:
    app.setStyle("Fusion")


def main() -> int:
    app = QApplication(sys.argv)
    if APP_ICON_FILE.exists():
        app.setWindowIcon(QIcon(str(APP_ICON_FILE)))

    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    apply_fusion_style(app)

    store = SettingsStore(SETTINGS_FILE)
    settings = store.load()
    api_key = ensure_api_key(store, settings)
    settings["panel_title"] = ensure_panel_title(store, settings)

    window = MainWindow(store=store, settings=settings, api_key=api_key)
    window.show()

    return app.exec()
