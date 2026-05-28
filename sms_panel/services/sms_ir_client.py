from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

import requests

from sms_panel.core.models import ApiResult

_TEHRAN_TZ = timezone(timedelta(hours=3, minutes=30))

try:
    from sms_ir import SmsIr as SmsIrSdk
except Exception:
    SmsIrSdk = None


class SmsIrClient:
    BASE_URL = "https://api.sms.ir"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key.strip()
        self.timeout = 25
        self.retries = 1
        self.sdk = None
        if SmsIrSdk is not None and self.api_key:
            try:
                self.sdk = SmsIrSdk(self.api_key)
            except Exception:
                self.sdk = None

    def update_api_key(self, api_key: str) -> None:
        self.api_key = api_key.strip()
        if SmsIrSdk is not None and self.api_key:
            try:
                self.sdk = SmsIrSdk(self.api_key)
            except Exception:
                self.sdk = None
        else:
            self.sdk = None

    def _headers(self) -> dict[str, str]:
        return {
            "X-API-KEY": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> ApiResult:
        url = f"{self.BASE_URL}{path}"
        last_error: requests.RequestException | None = None
        for _attempt in range(self.retries + 1):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=self._headers(),
                    params=params,
                    json=body,
                    timeout=self.timeout,
                )
                return self._parse_response(response)
            except requests.RequestException as exc:
                last_error = exc

        message = str(last_error) if last_error is not None else "خطای اتصال نامشخص"
        return ApiResult(
            ok=False,
            status_code=0,
            message=message,
            data=None,
            raw={"error": message},
        )

    @staticmethod
    def _iso_to_unix(date_str: str, end_of_day: bool = False) -> int | None:
        """Convert YYYY-MM-DD to Unix timestamp in Iran Standard Time (UTC+3:30)."""
        if not date_str:
            return None
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            if end_of_day:
                dt = dt.replace(hour=23, minute=59, second=59)
            return int(dt.replace(tzinfo=_TEHRAN_TZ).timestamp())
        except ValueError:
            return None

    def update_network_options(self, timeout_sec: int, retry_count: int) -> None:
        self.timeout = max(5, min(120, int(timeout_sec)))
        self.retries = max(0, min(5, int(retry_count)))

    @staticmethod
    def _parse_response(response: requests.Response) -> ApiResult:
        raw_data: Any
        try:
            raw_data = response.json()
        except ValueError:
            raw_data = {"text": response.text}

        message = ""
        data: Any = raw_data
        ok = response.status_code < 400

        if isinstance(raw_data, dict):
            message = str(raw_data.get("message", "")).strip()
            if "data" in raw_data:
                data = raw_data.get("data")
            status_flag = raw_data.get("status")
            if status_flag in (False, 0):
                ok = False
            if status_flag in (True, 1) and response.status_code < 500:
                ok = True

        if not message:
            message = f"HTTP {response.status_code}"

        return ApiResult(ok=ok, status_code=response.status_code, message=message, data=data, raw=raw_data)

    def health_check(self) -> ApiResult:
        return self.get_credit()

    def get_credit(self) -> ApiResult:
        if self.sdk is not None:
            return self._parse_response(self.sdk.get_credit())
        return self._request("GET", "/v1/credit/")

    def get_financial_credit(self) -> ApiResult:
        # Based on official SMS.ir docs, current financial credit is returned by GET /v1/credit.
        return self.get_credit()

    def get_line_numbers(self) -> ApiResult:
        if self.sdk is not None:
            return self._parse_response(self.sdk.get_line_numbers())
        return self._request("GET", "/v1/line/")

    def report_today(self, page_size: int = 20, page_number: int = 1) -> ApiResult:
        if self.sdk is not None:
            return self._parse_response(self.sdk.report_today(page_size=page_size, page_number=page_number))
        return self._request("GET", "/v1/send/live/", params={"pageSize": page_size, "pageNumber": page_number})

    def report_archived(self, from_date: str, to_date: str, page_size: int = 20, page_number: int = 1) -> ApiResult:
        from_unix = self._iso_to_unix(from_date)
        to_unix = self._iso_to_unix(to_date, end_of_day=True)
        if self.sdk is not None:
            return self._parse_response(
                self.sdk.report_archived(
                    from_date=from_unix,
                    to_date=to_unix,
                    page_size=page_size,
                    page_number=page_number,
                )
            )
        params = {
            "fromDate": from_unix,
            "toDate": to_unix,
            "pageSize": page_size,
            "pageNumber": page_number,
        }
        return self._request("GET", "/v1/send/archive/", params=params)

    def report_latest_received(self, count: int = 20) -> ApiResult:
        if self.sdk is not None:
            return self._parse_response(self.sdk.report_latest_received(count=count))
        return self._request("GET", "/v1/receive/latest/", params={"count": count})

    def report_today_received(self, page_size: int = 20, page_number: int = 1) -> ApiResult:
        if self.sdk is not None:
            return self._parse_response(self.sdk.report_today_received(page_size=page_size, page_number=page_number))
        return self._request("GET", "/v1/receive/live/", params={"pageSize": page_size, "pageNumber": page_number})

    def report_archived_received(self, from_date: str, to_date: str, page_size: int = 20, page_number: int = 1) -> ApiResult:
        from_unix = self._iso_to_unix(from_date)
        to_unix = self._iso_to_unix(to_date, end_of_day=True)
        if self.sdk is not None:
            return self._parse_response(
                self.sdk.report_archived_received(
                    from_date=from_unix,
                    to_date=to_unix,
                    page_size=page_size,
                    page_number=page_number,
                )
            )
        params = {
            "fromDate": from_unix,
            "toDate": to_unix,
            "pageSize": page_size,
            "pageNumber": page_number,
        }
        return self._request("GET", "/v1/receive/archive/", params=params)

    def report_message(self, message_id: int) -> ApiResult:
        if self.sdk is not None:
            return self._parse_response(self.sdk.report_message(message_id=message_id))
        return self._request("GET", f"/v1/send/{message_id}/")

    def report_pack(self, pack_id: int) -> ApiResult:
        if self.sdk is not None:
            return self._parse_response(self.sdk.report_pack(pack_id=pack_id))
        return self._request("GET", f"/v1/send/pack/{pack_id}/")

    def send_bulk(self, line_number: str, mobiles: list[str], message: str) -> ApiResult:
        cleaned = [item.strip() for item in mobiles if item.strip()]
        if not cleaned:
            raise ValueError("شماره موبایل معتبر وارد نشده است.")

        if self.sdk is not None:
            return self._parse_response(self.sdk.send_bulk_sms(numbers=cleaned, message=message, linenumber=line_number or None))

        body = {
            "lineNumber": line_number,
            "messageText": message,
            "mobiles": cleaned,
        }
        return self._request("POST", "/v1/send/bulk/", body=body)
