from __future__ import annotations

from typing import Any


def extract_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("items", "data", "messages", "result", "list"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return [payload]
    return []


def _find_key_value_for_keys(payload: Any, keys: tuple[str, ...]) -> tuple[str, Any] | tuple[None, None]:
    if isinstance(payload, dict):
        lower_map = {str(key).lower(): (str(key), value) for key, value in payload.items()}
        for key in keys:
            found = lower_map.get(key.lower())
            if found is not None and found[1] not in (None, ""):
                return found
        for value in payload.values():
            found_key, found_value = _find_key_value_for_keys(value, keys)
            if found_value not in (None, ""):
                return found_key, found_value
    elif isinstance(payload, list):
        for value in payload:
            found_key, found_value = _find_key_value_for_keys(value, keys)
            if found_value not in (None, ""):
                return found_key, found_value
    return None, None


def extract_credit_details(data_payload: Any, raw_payload: Any) -> tuple[Any, Any]:
    money_keys = (
        "returnedCreditCount",
        "creditAmount",
        "cashCredit",
        "rialBalance",
        "balance",
        "amount",
        "money",
        "credit",
        "currentCredit",
    )
    sms_keys = (
        "smsCount",
        "remainSmsCount",
        "remainingSmsCount",
        "remainingSms",
        "smsQuota",
        "messageCount",
        "availableSms",
        "remainCount",
    )

    # REST endpoint /v1/credit currently returns a scalar decimal in `data`.
    if isinstance(data_payload, (int, float, str)):
        return data_payload, "-"

    _, rial_value = _find_key_value_for_keys(data_payload, money_keys)
    sms_key, sms_value = _find_key_value_for_keys(data_payload, sms_keys)

    if rial_value is None:
        _, rial_value = _find_key_value_for_keys(raw_payload, money_keys)
    if sms_value is None:
        sms_key, sms_value = _find_key_value_for_keys(raw_payload, sms_keys)

    # When only SMS-related keys are present, do not map them into financial credit.
    if rial_value is None and sms_value is not None and sms_key is not None:
        return "-", sms_value

    if rial_value is None and isinstance(data_payload, (int, float, str)):
        rial_value = data_payload
    if rial_value is None and isinstance(raw_payload, (int, float, str)):
        rial_value = raw_payload

    return rial_value if rial_value is not None else "-", sms_value if sms_value is not None else "-"


def extract_line_numbers(payload: Any) -> list[str]:
    lines: list[str] = []
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                lines.append(str(item.get("lineNumber", item.get("number", ""))))
            else:
                lines.append(str(item))
    elif isinstance(payload, dict):
        candidates = payload.get("items") if isinstance(payload.get("items"), list) else [payload]
        for item in candidates:
            if isinstance(item, dict):
                line = item.get("lineNumber") or item.get("number") or item.get("line")
                if line:
                    lines.append(str(line))

    return [line for line in lines if line]
