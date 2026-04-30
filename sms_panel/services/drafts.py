from __future__ import annotations

from datetime import datetime
from typing import Any


def normalize_drafts(raw_drafts: Any) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    if not isinstance(raw_drafts, list):
        return normalized

    for index, item in enumerate(raw_drafts):
        if not isinstance(item, dict):
            continue
        message = str(item.get("message", "")).strip()
        if not message:
            continue

        saved_at = str(item.get("saved_at", "")).strip() or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        title = str(item.get("title", "")).strip() or f"پیش نویس {index + 1}"
        normalized.append(
            {
                "title": title,
                "message": message,
                "saved_at": saved_at,
                "type": str(item.get("type", "generic")),
                "line": str(item.get("line", "")).strip(),
                "mobiles": item.get("mobiles", []),
            }
        )
    return normalized
