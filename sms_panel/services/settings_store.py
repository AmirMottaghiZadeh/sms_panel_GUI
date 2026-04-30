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
            "theme": "light",
            "color_scheme": "peach_eggplant",
            "line_number": "",
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
        return data

    def save(self, settings: dict[str, Any]) -> None:
        payload = json.dumps(settings, ensure_ascii=False, indent=2)
        self.path.write_text(payload, encoding="utf-8")
