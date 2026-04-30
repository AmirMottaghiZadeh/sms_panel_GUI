from __future__ import annotations

import csv
import io
import json
import math
from pathlib import Path
from typing import Any

from sms_panel.config import CONTACTS_CACHE_FILE

REQUIRED_EXCEL_COLUMNS = ("name", "phone", "category")
PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
ENGLISH_DIGITS = "0123456789"
DIGIT_TRANSLATION = str.maketrans(PERSIAN_DIGITS + ARABIC_DIGITS, ENGLISH_DIGITS + ENGLISH_DIGITS)


def _repair_mojibake(text: str) -> str:
    # Fixes common UTF-8-as-Latin1 artifacts such as "Ø§Ø±...".
    if any(marker in text for marker in ("Ø", "Ù", "Ã", "Â")):
        try:
            repaired = text.encode("latin-1").decode("utf-8")
            if repaired:
                return repaired
        except Exception:
            pass
    return text


def _normalize_persian_text(text: str) -> str:
    normalized = _repair_mojibake(text)
    normalized = normalized.replace("ي", "ی").replace("ك", "ک")
    return normalized.strip()


def _clean_text(value: Any, *, repair_persian: bool = False) -> str:
    if value is None:
        return ""

    if isinstance(value, float):
        if math.isnan(value):
            return ""
        if value.is_integer():
            value = int(value)

    text = str(value).strip()
    if text.lower() in {"nan", "none", "null"}:
        return ""

    if repair_persian:
        text = _normalize_persian_text(text)

    return text


def _normalize_mobile(value: Any) -> str:
    text = _clean_text(value)
    if not text:
        return ""

    text = text.translate(DIGIT_TRANSLATION)
    digits = "".join(ch for ch in text if ch.isdigit())
    if not digits:
        return ""

    if digits.startswith("0098"):
        digits = digits[4:]
    elif digits.startswith("98"):
        digits = digits[2:]

    if not digits.startswith("0"):
        digits = "0" + digits

    return digits


def _normalize_row(row: dict[str, Any]) -> dict[str, str] | None:
    mobile = _normalize_mobile(row.get("mobile") or row.get("phone") or "")
    if not mobile:
        return None

    name = _clean_text(row.get("name") or "بدون نام", repair_persian=True) or "بدون نام"
    category = _clean_text(row.get("category") or row.get("group") or row.get("tag") or "عمومی", repair_persian=True) or "عمومی"

    return {"name": name, "mobile": mobile, "category": category}


def normalize_contacts(raw_contacts: Any) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    if not isinstance(raw_contacts, list):
        return normalized

    for item in raw_contacts:
        if not isinstance(item, dict):
            continue
        row = _normalize_row(item)
        if row is not None:
            normalized.append(row)

    return normalized


def _read_csv_content(path: Path) -> tuple[list[str], list[dict[str, Any]]]:
    raw = path.read_bytes()
    tried: list[str] = []

    for encoding in ("utf-8-sig", "utf-16", "cp1256", "windows-1256", "utf-8", "latin-1"):
        tried.append(encoding)
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError:
            continue

        reader = csv.DictReader(io.StringIO(text))
        if reader.fieldnames is None:
            continue

        rows = list(reader)
        field_names = [str(name).strip() for name in reader.fieldnames if name is not None]
        return field_names, rows

    raise RuntimeError(f"کدگذاری فایل CSV قابل تشخیص نبود. کدگذاری های بررسی شده: {', '.join(tried)}")


def _normalize_header(name: str) -> str:
    return _clean_text(name, repair_persian=True).lstrip("\ufeff").strip().lower()


def _normalize_row_keys(row: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in row.items():
        normalized[_normalize_header(str(key))] = value
    return normalized


def read_contacts_from_csv(file_path: str | Path) -> list[dict[str, str]]:
    path = Path(file_path)
    field_names, rows = _read_csv_content(path)

    normalized_headers = tuple(_normalize_header(name) for name in field_names)
    should_cache = normalized_headers == REQUIRED_EXCEL_COLUMNS

    imported: list[dict[str, str]] = []
    for row in rows:
        normalized_row = _normalize_row_keys(row)
        parsed = _normalize_row(normalized_row)
        if parsed is not None:
            imported.append(parsed)

    if should_cache and imported:
        save_contacts_cache(imported)

    return imported


def _records_from_excel(path: Path) -> list[dict[str, Any]]:
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError("برای ورود فایل اکسل باید بسته های pandas و openpyxl نصب باشند.") from exc

    try:
        frame = pd.read_excel(path, dtype=str, keep_default_na=False)
    except Exception as exc:
        raise RuntimeError(f"خواندن فایل اکسل ممکن نشد: {exc}") from exc

    normalized_columns = tuple(_normalize_header(str(column)) for column in frame.columns)
    if normalized_columns != REQUIRED_EXCEL_COLUMNS:
        expected = ", ".join(REQUIRED_EXCEL_COLUMNS)
        received = ", ".join(normalized_columns)
        raise RuntimeError(f"ساختار فایل اکسل نامعتبر است. ترتیب ستون ها باید دقیقا {expected} باشد. ستون های فعلی: {received}")

    records: list[dict[str, Any]] = []
    for row in frame.to_dict(orient="records"):
        records.append(_normalize_row_keys(row))
    return records


def save_contacts_cache(contacts: list[dict[str, str]]) -> None:
    payload = {
        "schema": list(REQUIRED_EXCEL_COLUMNS),
        "count": len(contacts),
        "contacts": contacts,
    }
    CONTACTS_CACHE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_contacts_cache() -> list[dict[str, str]]:
    if not CONTACTS_CACHE_FILE.exists():
        return []
    try:
        payload = json.loads(CONTACTS_CACHE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, dict):
        return []
    return normalize_contacts(payload.get("contacts", []))


def read_contacts_from_file(file_path: str | Path) -> list[dict[str, str]]:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        return read_contacts_from_csv(path)

    if suffix not in {".xlsx", ".xls"}:
        raise RuntimeError("فرمت فایل پشتیبانی نمی شود. فقط csv/xlsx/xls مجاز است.")

    records = _records_from_excel(path)
    imported: list[dict[str, str]] = []

    for row in records:
        parsed = _normalize_row(row)
        if parsed is not None:
            imported.append(parsed)

    if imported:
        save_contacts_cache(imported)

    return imported
