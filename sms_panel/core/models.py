from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ApiResult:
    ok: bool
    status_code: int
    message: str
    data: Any
    raw: Any
