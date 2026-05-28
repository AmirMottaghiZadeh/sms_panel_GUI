from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SettingsStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def defaults(self) -> dict[str, Any]:
        return {
            "api_key": "",
            "panel_title": "",
            "organization_name": "",
            "brand_logo_path": "",
            "theme": "light",
            "color_scheme": "peach_eggplant",
            "font_scale": "normal",
            "ui_density": "comfortable",
            "line_number": "",
            "message_signature": "",
            "bulk_confirm_enabled": True,
            "bulk_confirm_threshold": 50,
            "contacts_default_category": "عمومی",
            "dedupe_contacts_on_save": True,
            "max_drafts": 100,
            "notify_on_success": True,
            "notify_on_error": True,
            "show_popup_notifications": True,
            "beep_on_error": False,
            "mask_mobile_numbers": False,
            "app_lock_enabled": False,
            "app_pin_hash": "",
            "require_sensitive_action_confirmation": True,
            "api_timeout_sec": 25,
            "api_retry_count": 1,
            "last_api_success_at": "",
            "log_level": "INFO",
            "log_file_path": "",
            "auto_refresh_interval_sec": 0,
            "window_geometry": "",
            "contacts": [],
            "drafts": [],
        }

    def load(self) -> dict[str, Any]:
        data = self.defaults()
        if self.path.exists():
            try:
                loaded = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    data.update(loaded)
            except json.JSONDecodeError:
                pass
        return self._sanitize(data)

    def save(self, settings: dict[str, Any]) -> None:
        payload = json.dumps(self._sanitize(settings), ensure_ascii=False, indent=2)
        self.path.write_text(payload, encoding="utf-8")

    def _sanitize(self, data: dict[str, Any]) -> dict[str, Any]:
        defaults = self.defaults()
        sanitized: dict[str, Any] = dict(defaults)

        for key, value in data.items():
            if key not in defaults:
                sanitized[key] = value

        allowed_theme = {"light", "dark"}
        allowed_scheme = {
            "peach_eggplant",
            "brown_mustard",
            "orange_black",
            "beige_red_gradient",
            "school_navy_gold",
        }
        allowed_font_scale = {"small", "normal", "large"}
        allowed_density = {"compact", "comfortable"}
        allowed_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR"}

        sanitized["api_key"] = self._as_text(data.get("api_key"), "")
        sanitized["panel_title"] = self._as_text(data.get("panel_title"), "")
        sanitized["organization_name"] = self._as_text(data.get("organization_name"), "")
        sanitized["brand_logo_path"] = self._as_text(data.get("brand_logo_path"), "")

        theme = self._as_text(data.get("theme"), defaults["theme"]).lower()
        sanitized["theme"] = theme if theme in allowed_theme else defaults["theme"]

        scheme = self._as_text(data.get("color_scheme"), defaults["color_scheme"])
        sanitized["color_scheme"] = scheme if scheme in allowed_scheme else defaults["color_scheme"]

        font_scale = self._as_text(data.get("font_scale"), defaults["font_scale"]).lower()
        sanitized["font_scale"] = font_scale if font_scale in allowed_font_scale else defaults["font_scale"]

        density = self._as_text(data.get("ui_density"), defaults["ui_density"]).lower()
        sanitized["ui_density"] = density if density in allowed_density else defaults["ui_density"]

        sanitized["line_number"] = self._as_text(data.get("line_number"), "")
        sanitized["message_signature"] = self._as_text(data.get("message_signature"), "")

        sanitized["bulk_confirm_enabled"] = self._as_bool(data.get("bulk_confirm_enabled"), True)
        sanitized["bulk_confirm_threshold"] = self._as_int(
            data.get("bulk_confirm_threshold"),
            default=50,
            minimum=1,
            maximum=100000,
        )
        sanitized["contacts_default_category"] = self._as_text(data.get("contacts_default_category"), "عمومی") or "عمومی"
        sanitized["dedupe_contacts_on_save"] = self._as_bool(data.get("dedupe_contacts_on_save"), True)
        sanitized["max_drafts"] = self._as_int(data.get("max_drafts"), default=100, minimum=10, maximum=1000)

        sanitized["notify_on_success"] = self._as_bool(data.get("notify_on_success"), True)
        sanitized["notify_on_error"] = self._as_bool(data.get("notify_on_error"), True)
        sanitized["show_popup_notifications"] = self._as_bool(data.get("show_popup_notifications"), True)
        sanitized["beep_on_error"] = self._as_bool(data.get("beep_on_error"), False)

        sanitized["mask_mobile_numbers"] = self._as_bool(data.get("mask_mobile_numbers"), False)
        sanitized["app_lock_enabled"] = self._as_bool(data.get("app_lock_enabled"), False)
        sanitized["app_pin_hash"] = self._as_text(data.get("app_pin_hash"), "")
        sanitized["require_sensitive_action_confirmation"] = self._as_bool(
            data.get("require_sensitive_action_confirmation"),
            True,
        )

        sanitized["api_timeout_sec"] = self._as_int(data.get("api_timeout_sec"), default=25, minimum=5, maximum=120)
        sanitized["api_retry_count"] = self._as_int(data.get("api_retry_count"), default=1, minimum=0, maximum=5)
        sanitized["last_api_success_at"] = self._as_text(data.get("last_api_success_at"), "")

        log_level = self._as_text(data.get("log_level"), "INFO").upper()
        sanitized["log_level"] = log_level if log_level in allowed_log_levels else "INFO"
        sanitized["log_file_path"] = self._as_text(data.get("log_file_path"), "")
        sanitized["auto_refresh_interval_sec"] = self._as_int(
            data.get("auto_refresh_interval_sec"), default=0, minimum=0, maximum=3600
        )
        sanitized["window_geometry"] = self._as_text(data.get("window_geometry"), "")

        contacts = data.get("contacts")
        drafts = data.get("drafts")
        sanitized["contacts"] = contacts if isinstance(contacts, list) else []
        sanitized["drafts"] = drafts if isinstance(drafts, list) else []
        return sanitized

    @staticmethod
    def _as_text(value: Any, default: str) -> str:
        if value is None:
            return default
        return str(value).strip()

    @staticmethod
    def _as_int(value: Any, *, default: int, minimum: int, maximum: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = default
        return max(minimum, min(maximum, parsed))

    @staticmethod
    def _as_bool(value: Any, default: bool) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"1", "true", "yes", "on", "y"}:
                return True
            if lowered in {"0", "false", "no", "off", "n"}:
                return False
        if isinstance(value, (int, float)):
            return bool(value)
        return default
