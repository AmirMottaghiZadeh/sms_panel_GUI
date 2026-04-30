from __future__ import annotations

from typing import Any

import requests

from sms_panel.core.models import ApiResult

try:
    from sms_ir import SmsIr as SmsIrSdk
except Exception:
    SmsIrSdk = None


class SmsIrClient:
    BASE_URL = "https://api.sms.ir"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key.strip()
        self.timeout = 25
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
            return ApiResult(
                ok=False,
                status_code=0,
                message=str(exc),
                data=None,
                raw={"error": str(exc)},
            )

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
        if self.sdk is not None:
            return self._parse_response(
                self.sdk.report_archived(
                    from_date=from_date or None,
                    to_date=to_date or None,
                    page_size=page_size,
                    page_number=page_number,
                )
            )
        params = {
            "fromDate": from_date or None,
            "toDate": to_date or None,
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
        if self.sdk is not None:
            return self._parse_response(
                self.sdk.report_archived_received(
                    from_date=from_date or None,
                    to_date=to_date or None,
                    page_size=page_size,
                    page_number=page_number,
                )
            )
        params = {
            "fromDate": from_date or None,
            "toDate": to_date or None,
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
