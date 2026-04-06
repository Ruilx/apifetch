# -*- coding: utf-8 -*-

"""Tiny runnable demo for HttpApi without external network dependency."""

from pathlib import Path
import sys
from typing import Any

from requests.exceptions import HTTPError

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from data.apis.http_api import HttpApi
else:
    from .http_api import HttpApi
from src.base.api_base import RetryPolicy


class FakeResponse:
    def __init__(self, status_code: int, payload: dict[str, Any]):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict[str, Any]:
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise HTTPError(f"status={self.status_code}", response=self)


class FakeSession:
    total_calls = 0

    def __init__(self):
        self.headers: dict[str, str] = {}

    def request(self, **kwargs):
        FakeSession.total_calls += 1
        if FakeSession.total_calls == 1:
            return FakeResponse(503, {"ok": False, "attempt": FakeSession.total_calls})
        return FakeResponse(200, {"ok": True, "attempt": FakeSession.total_calls, "url": kwargs.get("url")})

    def close(self):
        return None


class DemoHttpApi(HttpApi):
    def build_request(self) -> dict[str, Any]:
        return {"method": "GET", "url": "/status"}

    def _parse_response(self, raw_response):
        return raw_response.json()


def main():
    api = DemoHttpApi(
        arguments=[],
        base_url="https://example.local",
        default_headers={"X-Token": "demo-token"},
        retry_policy=RetryPolicy(max_attempts=3, initial_delay_seconds=0.0, max_delay_seconds=0.0),
        session_factory=FakeSession,
    )
    result = api.exec()
    print(result)


if __name__ == "__main__":
    main()
