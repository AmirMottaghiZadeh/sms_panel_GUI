from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SETTINGS_FILE = PROJECT_ROOT / "sms_panel_settings.json"
API_KEY_FILE = PROJECT_ROOT / "sms_api.txt"
APP_ICON_FILE = PROJECT_ROOT / "sms_panel" / "ui" / "logo.png"
CONTACTS_CACHE_FILE = PROJECT_ROOT / "contacts_import_cache.json"
DEFAULT_LOG_FILE = PROJECT_ROOT / "sms_panel.log"
APP_VERSION = "1.2.0"
